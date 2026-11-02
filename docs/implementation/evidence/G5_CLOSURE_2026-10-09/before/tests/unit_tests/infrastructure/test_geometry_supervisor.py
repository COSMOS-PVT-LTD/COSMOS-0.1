import os
import sys
import threading
import time

import pytest

from infrastructure.geometry import WorkerCommand, WorkerError, WorkerSupervisor


def command(source):
    return WorkerCommand((sys.executable, "-c", source))


@pytest.mark.parametrize("settings", [{"max_workers": 0}, {"max_workers": True}, {"max_queued": -1}, {"timeout_s": float("nan")},
                                      {"timeout_s": 0}, {"stdout_limit": True}, {"stderr_limit": 0}, {"rss_limit_bytes": 0}])
def test_invalid_supervisor_configuration_is_typed(settings):
    with pytest.raises(WorkerError):
        WorkerSupervisor(**settings)


@pytest.mark.parametrize("argv,env", [((), ()), (("python",), ()), (("/does/not/exist",), ()),
                                   ((sys.executable,), (("AWS_SECRET_ACCESS_KEY", "x"),)),
                                   ((sys.executable,), (("PYTHONPATH", "x"), ("PYTHONPATH", "y")))])
def test_trusted_configuration_refuses_shell_search_and_secret_env(argv, env):
    with pytest.raises(WorkerError):
        WorkerCommand(argv, env)


def test_actual_bounded_echo_and_clean_close(tmp_path):
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("echo", command("import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())"), b'{"ok":true}', tmp_path).result()
        assert result.code == "OK" and result.stdout == b'{"ok":true}' and result.exit_code == 0
    with pytest.raises(WorkerError):
        supervisor.submit("closed", command("pass"), b"", tmp_path)


def test_actual_timeout_and_retry(tmp_path):
    with WorkerSupervisor(timeout_s=.1) as supervisor:
        result = supervisor.submit("timeout", command("import time;time.sleep(10)"), b"", tmp_path).result()
        assert result.code == "TIMEOUT" and result.elapsed_s < 2
        assert supervisor.submit("retry", command("print('retry')"), b"", tmp_path).result().code == "OK"


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_actual_output_overflow_not_unbounded_memory(stream, tmp_path):
    with WorkerSupervisor(stdout_limit=128, stderr_limit=128) as supervisor:
        result = supervisor.submit("overflow", command(f"import sys;sys.{stream}.write('x'*20000);sys.{stream}.flush()"), b"", tmp_path).result()
        assert result.code == "OUTPUT_LIMIT"
        assert len(result.stdout) <= 128 and len(result.stderr) <= 128


def test_actual_memory_guard(tmp_path):
    with WorkerSupervisor(rss_limit_bytes=1024*1024) as supervisor:
        result = supervisor.submit("memory", command("import time;data=bytearray(32*1024*1024);time.sleep(10)"), b"", tmp_path).result()
        assert result.code == "MEMORY_LIMIT" and result.maximum_rss_bytes > 1024*1024


def test_actual_crash_is_not_success(tmp_path):
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("crash", command("import os;os._exit(7)"), b"", tmp_path).result()
        assert result.code == "WORKER_CRASH" and result.exit_code == 7


def test_bounded_queue_duplicate_jobs_queued_and_running_cancel(tmp_path):
    with WorkerSupervisor(max_workers=1, max_queued=1) as supervisor:
        first = supervisor.submit("first", command("import time;time.sleep(10)"), b"", tmp_path)
        second = supervisor.submit("second", command("print('must not run')"), b"", tmp_path)
        for name in ("first", "third"):
            with pytest.raises(WorkerError):
                supervisor.submit(name, command("pass"), b"", tmp_path)
        assert supervisor.cancel("second") and supervisor.cancel("first")
        assert first.result().code == second.result().code == "CANCELLED"
        assert second.result().pid is None
        assert not supervisor.cancel("not-active")


def test_process_group_cancellation_removes_spawned_child(tmp_path):
    source = "import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)']);Path('child.pid').write_text(str(p.pid));time.sleep(20)"
    with WorkerSupervisor() as supervisor:
        future = supervisor.submit("tree", command(source), b"", tmp_path)
        until = time.monotonic() + 2
        marker = tmp_path / "child.pid"
        while not marker.exists() and time.monotonic() < until:
            time.sleep(.01)
        assert marker.exists()
        child = int(marker.read_text())
        supervisor.cancel("tree")
        assert future.result().code == "CANCELLED"
        until = time.monotonic() + 2
        alive = True
        while alive and time.monotonic() < until:
            try:
                os.kill(child, 0)
                time.sleep(.01)
            except ProcessLookupError:
                alive = False
        assert not alive


def test_input_size_identifier_and_directory_guards(tmp_path):
    with WorkerSupervisor() as supervisor:
        for name, data, path in [("../bad", b"", tmp_path), ("large", b"x"*(2*1024**2+1), tmp_path), ("missing", b"", tmp_path/"missing")]:
            with pytest.raises(WorkerError):
                supervisor.submit(name, command("pass"), data, path)


def test_pre_cancelled_shared_token_cannot_miss_worker_registration(tmp_path):
    token = threading.Event(); token.set()
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("pre-cancel", command("raise RuntimeError('must not execute')"), b"", tmp_path, cancellation=token).result()
        assert result.code == "CANCELLED" and result.pid is None


def test_shared_token_cancels_already_running_child_without_registration_race(tmp_path):
    token = threading.Event()
    with WorkerSupervisor() as supervisor:
        future = supervisor.submit("shared", command("from pathlib import Path;import time;Path('started').touch();time.sleep(10)"), b"", tmp_path, cancellation=token)
        until = time.monotonic() + 2
        while not (tmp_path / "started").exists() and time.monotonic() < until:
            time.sleep(.01)
        assert (tmp_path / "started").exists()
        token.set()
        assert future.result(timeout=2).code == "CANCELLED"


def test_normal_leader_exit_also_terminates_live_descendant(tmp_path):
    source = "import subprocess,sys;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)']);Path('child.pid').write_text(str(p.pid))"
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("exit-tree", command(source), b"", tmp_path).result(timeout=3)
        assert result.code == "OK"
        child = int((tmp_path / "child.pid").read_text())
        until = time.monotonic() + 2
        while time.monotonic() < until:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                return
            time.sleep(.01)
        pytest.fail("Live descendant remains after leader exit")
