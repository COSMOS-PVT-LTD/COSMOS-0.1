"""Bounded, cancellable, one-request-per-process execution on POSIX hosts.

Trusted host code supplies executable/argv/env. Never construct commands from UI input.
Process isolation is not a malicious-code filesystem/network sandbox.
"""
from __future__ import annotations

import math
import os
import re
import signal
import subprocess
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Self

MAX_WIRE_BYTES = 2 * 1024 * 1024


class WorkerError(ValueError):
    """Infrastructure error; this layer never imports scientific Systems contracts."""
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise WorkerError(code, message)


def identifier(value: str, field: str) -> None:
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is not None,
            "INVALID_IDENTIFIER", f"Invalid {field}")


@dataclass(frozen=True, slots=True)
class WorkerCommand:
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", tuple(self.argv))
        object.__setattr__(self, "environment", tuple(tuple(v) for v in self.environment))
        require(bool(self.argv) and all(type(a) is str and a and "\0" not in a for a in self.argv), "WORKER_CONFIG", "Invalid trusted argv")
        executable = Path(self.argv[0])
        require(executable.is_absolute() and executable.is_file() and os.access(executable, os.X_OK), "WORKER_CONFIG", "Worker executable must be an existing absolute executable")
        require(len(dict(self.environment)) == len(self.environment), "WORKER_CONFIG", "Duplicate environment keys")
        require(all(k in {"PYTHONPATH", "DOTNET_ROOT", "DOTNET_CLI_TELEMETRY_OPTOUT", "DOTNET_CLI_HOME", "NUGET_PACKAGES", "DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"}
                    and type(v) is str and "\0" not in v for k, v in self.environment), "WORKER_CONFIG", "Unsupported trusted environment key")


@dataclass(frozen=True, slots=True)
class ProcessResult:
    job_id: str
    code: str
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    elapsed_s: float
    maximum_rss_bytes: int
    pid: int | None


def _rss(pid: int) -> int:
    if Path(f"/proc/{pid}/statm").is_file():
        try:
            return int(Path(f"/proc/{pid}/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            return 0
    try:
        output = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(pid)], capture_output=True, timeout=.5, check=False).stdout
        return int(output.strip() or b"0") * 1024
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 0


def _kill_group(process: subprocess.Popen[bytes]) -> bool:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except PermissionError:
        # macOS can retain an orphan zombie group after its leader is reaped.
        # Never treat denial against a live member as successful cleanup.
        try:
            observed = subprocess.run(["/bin/ps", "-axo", "pgid=,stat="], capture_output=True, timeout=.5, check=True).stdout.decode()
            return not any(fields[0] == str(process.pid) and not fields[1].startswith("Z")
                           for line in observed.splitlines() if len(fields := line.split()) == 2)
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
    return True


class WorkerSupervisor:
    """Nonblocking bounded admission; explicit limits, shutdown and cancellation."""

    def __init__(self, *, max_workers: int = 1, max_queued: int = 2, timeout_s: float = 45,
                 stdout_limit: int = MAX_WIRE_BYTES, stderr_limit: int = 65536,
                 rss_limit_bytes: int = 1024 * 1024 * 1024) -> None:
        require(os.name == "posix", "UNSUPPORTED_PLATFORM", "Geometry process supervision is qualified only on POSIX")
        require(type(max_workers) is int and 1 <= max_workers <= 4 and type(max_queued) is int and 0 <= max_queued <= 32, "WORKER_CONFIG", "Invalid queue limits")
        require(type(timeout_s) in (int, float) and math.isfinite(timeout_s) and .05 <= timeout_s <= 300, "WORKER_CONFIG", "Invalid explicit timeout")
        require(all(type(v) is int and 1 <= v <= 1024**3 for v in (stdout_limit, stderr_limit, rss_limit_bytes)), "WORKER_CONFIG", "Invalid byte/memory limits")
        self.timeout_s, self.stdout_limit, self.stderr_limit = timeout_s, stdout_limit, stderr_limit
        self.rss_limit_bytes = rss_limit_bytes
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="cosmos-geometry")
        self._admission = threading.BoundedSemaphore(max_workers + max_queued)
        self._lock = threading.Lock()
        self._tokens: dict[str, threading.Event] = {}
        self._closed = False

    def submit(self, job_id: str, command: WorkerCommand, payload: bytes, working_directory: Path,
               *, cancellation: threading.Event | None = None) -> Future[ProcessResult]:
        identifier(job_id, "job_id")
        require(type(payload) is bytes and len(payload) <= MAX_WIRE_BYTES, "CONTRACT_LIMIT", "Worker input exceeds bounded protocol size")
        require(working_directory.is_absolute() and working_directory.is_dir(), "WORKER_CONFIG", "Trusted working directory must exist")
        require(cancellation is None or isinstance(cancellation, threading.Event), "WORKER_CONFIG", "Cancellation must be a trusted job token")
        with self._lock:
            require(not self._closed, "SUPERVISOR_CLOSED", "Supervisor is closed")
            require(job_id not in self._tokens, "DUPLICATE_JOB", "Job identity is already active")
            require(self._admission.acquire(blocking=False), "QUEUE_FULL", "Geometry queue is full; retry later")
            token = cancellation if cancellation is not None else threading.Event()
            self._tokens[job_id] = token
            future = self._pool.submit(self._run, job_id, command, payload, working_directory, token)
        def completed(_: Future[ProcessResult]) -> None:
            with self._lock:
                self._tokens.pop(job_id, None)
            self._admission.release()
        future.add_done_callback(completed)
        return future

    def cancel(self, job_id: str) -> bool:
        identifier(job_id, "job_id")
        with self._lock:
            token = self._tokens.get(job_id)
            if token is not None:
                token.set()
            return token is not None

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for token in self._tokens.values():
                token.set()
        self._pool.shutdown(wait=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _run(self, job: str, command: WorkerCommand, payload: bytes, directory: Path, token: threading.Event) -> ProcessResult:
        start = time.monotonic()
        if token.is_set():
            return ProcessResult(job, "CANCELLED", None, b"", b"", 0, 0, None)
        environment = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL", "TMPDIR") if k in os.environ}
        environment.update(command.environment)
        try:
            process = subprocess.Popen(command.argv, cwd=directory, env=environment, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        except OSError as error:
            return ProcessResult(job, "WORKER_START", None, b"", str(error).encode()[:self.stderr_limit], time.monotonic() - start, 0, None)
        buffers = [bytearray(), bytearray()]
        overflow = threading.Event()
        def drain(stream, buffer, limit):
            try:
                while chunk := stream.read(8192):
                    room = limit - len(buffer)
                    buffer.extend(chunk[:max(room, 0)])
                    if len(chunk) > room:
                        overflow.set()
            finally:
                stream.close()
        def feed():
            assert process.stdin is not None
            try:
                process.stdin.write(payload)
                process.stdin.close()
            except (OSError, ValueError):
                pass
        assert process.stdout is not None and process.stderr is not None
        threads = [threading.Thread(target=drain, args=(process.stdout, buffers[0], self.stdout_limit), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, buffers[1], self.stderr_limit), daemon=True),
                   threading.Thread(target=feed, daemon=True)]
        for thread in threads:
            thread.start()
        code, peak, next_sample, group_killed = "OK", 0, start, False
        while process.poll() is None:
            now = time.monotonic()
            if token.is_set():
                code = "CANCELLED"
            elif overflow.is_set():
                code = "OUTPUT_LIMIT"
            elif now - start >= self.timeout_s:
                code = "TIMEOUT"
            if now >= next_sample:
                peak = max(peak, _rss(process.pid))
                next_sample = now + .2
                if peak > self.rss_limit_bytes:
                    code = "MEMORY_LIMIT"
            if code != "OK":
                group_killed = _kill_group(process)
                if not group_killed:
                    code = "CLEANUP_FAILED"
                    process.kill()  # Only our exact launched leader; no permission escalation.
                break
            token.wait(.02)
        process.wait(timeout=2)
        # Descendants cannot keep pipes or work alive after the leader exits.
        if not group_killed and not _kill_group(process):
            code = "CLEANUP_FAILED"
        for thread in threads:
            thread.join(timeout=1)
        if code == "OK" and overflow.is_set():
            code = "OUTPUT_LIMIT"
        if code == "OK" and process.returncode != 0:
            code = "WORKER_CRASH"
        return ProcessResult(job, code, process.returncode, bytes(buffers[0]), bytes(buffers[1]), time.monotonic() - start, peak, process.pid)
