"""Accepted guided inputs -> durable bounded attempt -> ordinary propulsion design."""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from uuid import UUID, uuid5

from systems.guided_engine.resolution import digest
from systems.persistence.job_repository import TERMINAL, JobState
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import Head, InvalidRecord, StoreUnavailable
from systems.projects.models import PropulsionDesign

DOMAIN = "guided-engine-input"
SCHEMA = "cosmos.accepted-guided-input.v1"


def payload(value, schema="cosmos.guided-attempt.v1"):
    return RecordPayload(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode(),
        schema,
    )


class GuidedEngines:
    def __init__(self, repository, jobs, runner, methods, resolve_actor):
        self.repository, self.jobs, self.runner = repository, jobs, runner
        self.methods, self.resolve_actor = methods, resolve_actor
        self.loaded_methods = methods()
        self.lock = threading.RLock()
        self.closed = False
        self.active = set()
        self.pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="guided-design"
        )

    def stable(self):
        if self.closed or self.methods() != self.loaded_methods:
            raise StoreUnavailable(
                "Guided runtime/source changed or closed. Reopen and review the new exact basis; originals are retained."
            )

    def accept(self, actor, project, plan, operation, command_hash):
        actor.require(write=True)
        self.stable()
        replay = self.repository.resolve_command(
            actor, project, operation_id=operation, command_hash=command_hash
        )
        if replay is not None:
            if replay.domain != DOMAIN:
                raise InvalidRecord("Operation belongs to another command.")
            return replay
        object_id = str(uuid5(UUID(project), actor.user_id + ":guided:" + operation))
        return self.repository.save_snapshot(
            actor,
            project,
            domain=DOMAIN,
            object_id=object_id,
            input_revision=0,
            payload=payload(
                {
                    "resolution": plan,
                    "review_hash": plan["review_hash"],
                    "accepted_by": actor.user_id,
                    "scope": "Accepted preliminary assumptions, not engineering or hardware acceptance",
                },
                SCHEMA,
            ),
            expected=Head.absent(),
            operation_id=operation,
            command_hash=command_hash,
            purpose="create",
        )

    def start(self, actor, source, operation, request_hash):
        self.stable()
        replay = self.jobs.resolve_command(
            actor, source.project_id, operation_id=operation, request_hash=request_hash
        )
        if replay is not None:
            return replay
        if source.domain != DOMAIN:
            raise InvalidRecord("Exact accepted guided input source required.")
        plan = json.loads(source.payload)["resolution"]
        if plan["method_sources"] != self.loaded_methods:
            raise InvalidRecord(
                "Accepted plan uses different methods. Make a new review; it cannot silently select updated sources."
            )
        with self.lock:
            if self.closed or len(self.active) >= 3:
                raise StoreUnavailable(
                    "Guided worker queue is closed/full. Existing work was not replaced; retry when idle."
                )
            job = self.jobs.admit(
                actor, source, operation_id=operation, request_hash=request_hash
            )
            if job.state not in TERMINAL and job.job_id not in self.active:
                self.active.add(job.job_id)
                self.pool.submit(self._run, job, plan)
            return job

    def _run(self, job, plan):
        try:
            with self.lock:
                if self.closed:
                    self.jobs.advance(
                        job.job_id,
                        JobState.INTERRUPTED,
                        payload({"code": "APP_CLOSED"}),
                    )
                    return
                started = self.jobs.advance(
                    job.job_id,
                    JobState.RUNNING,
                    payload(
                        {
                            "code": "GUIDED_CEA_SIZING",
                            "review_hash": plan["review_hash"],
                        }
                    ),
                )
                if started.state in TERMINAL:
                    return
            process = self.runner.submit(
                job.job_id,
                json.dumps(
                    plan, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode(),
            ).result()
            with self.lock:
                actor = self.resolve_actor(job.creator_user_id)
                observed = self.jobs.get(actor, job.project_id, job.job_id)
                if self.closed:
                    self.jobs.advance(
                        job.job_id,
                        JobState.INTERRUPTED,
                        payload({"code": "APP_CLOSED"}),
                    )
                    return
                if (
                    observed.state in {JobState.CANCEL_REQUESTED, JobState.CANCELLED}
                    or process.code == "CANCELLED"
                ):
                    self.jobs.advance(
                        job.job_id,
                        JobState.CANCELLED,
                        payload(
                            {"code": "CANCELLED", "review_hash": plan["review_hash"]}
                        ),
                    )
                    return
                if process.code != "OK" or process.exit_code != 0:
                    raise InvalidRecord(
                        "Guided worker "
                        + process.code
                        + ": "
                        + process.stderr.decode(errors="replace")[-1800:]
                    )
                self.stable()
                result = json.loads(process.stdout)
                if (
                    set(result) != {"review_hash", "design", "report"}
                    or result["review_hash"] != plan["review_hash"]
                    or result["report"]["review_hash"] != plan["review_hash"]
                ):
                    raise InvalidRecord(
                        "Worker result differs from the accepted exact plan."
                    )
                design = PropulsionDesign.from_canonical_dict(result["design"])
                design.design_id = str(
                    uuid5(UUID(job.project_id), "guided-design:" + job.job_id)
                )
                design.engineer = actor.user_id
                saved = self.repository.save_snapshot(
                    actor,
                    job.project_id,
                    domain="propulsion",
                    object_id=design.design_id,
                    input_revision=design.revision,
                    payload=RecordPayload.from_design(design),
                    expected=Head.absent(),
                    operation_id="guided-result." + job.job_id,
                    command_hash=digest(
                        {"job": job.job_id, "source": job.source_commit_id}
                    ),
                    input_commit_id=job.source_commit_id,
                    dependencies=(Dependency("guided-input", job.source_commit_id),),
                    purpose="calculation",
                )
                self.jobs.advance(
                    job.job_id,
                    JobState.COMPLETED,
                    payload(
                        {
                            "code": "PRELIMINARY_RESULTS_WITH_LIMITATIONS",
                            "report": result["report"],
                            "design_object_id": design.design_id,
                            "design_commit_id": saved.commit_id,
                            "review_hash": plan["review_hash"],
                            "physical_validation": "NOT_PERFORMED",
                        }
                    ),
                    actor=actor,
                )
        except Exception as error:
            logging.getLogger(__name__).exception("Guided design attempt failed")
            try:
                self.jobs.advance(
                    job.job_id,
                    JobState.FAILED,
                    payload(
                        {
                            "code": type(error).__name__,
                            "message": str(error)[:2400],
                            "review_hash": plan["review_hash"],
                            "action": "Inspect the saved basis; correct it and explicitly start a new reviewed attempt.",
                        }
                    ),
                )
            except Exception:
                logging.getLogger(__name__).exception(
                    "Guided terminal retention failed; lease recovery required"
                )
        finally:
            with self.lock:
                self.active.discard(job.job_id)

    def cancel(self, actor, project, job_id, expected, operation, request_hash):
        with self.lock:
            receipt = self.jobs.cancel(
                actor,
                project,
                job_id,
                expected=expected,
                operation_id=operation,
                request_hash=request_hash,
            )
            self.runner.cancel(job_id)
            return receipt

    def envelope(self, actor, source):
        if source.domain != DOMAIN or source.schema_id != SCHEMA:
            raise InvalidRecord("Not an accepted guided input source.")
        return {
            "ok": True,
            "authority": {
                "object_id": source.object_id,
                "commit_id": source.commit_id,
                "project_id": source.project_id,
                "head": asdict(source.head),
            },
            "record": json.loads(source.payload),
            "methods_current": json.loads(source.payload)["resolution"][
                "method_sources"
            ]
            == self.loaded_methods
            == self.methods(),
        }

    def close(self):
        with self.lock:
            self.closed = True
            for job_id in self.active:
                self.runner.cancel(job_id)
        self.pool.shutdown(wait=True)
        self.runner.close()
