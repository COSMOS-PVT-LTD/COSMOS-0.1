"""Explicit local operator command: retain old sources, select a CAD development default.

No store discovery, owner guessing, migrations, native builds, account bootstrap,
historical receipt rewriting or deletion. Preview first, then apply the exact
preview SHA256 using the same explicit project/source/user/operation arguments.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid5

from core.serialization import canonical_json_dumps
from infrastructure.persistence.files import CoordinatorLease
from infrastructure.persistence.portability import require_completed_restore
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from scripts.project_storage import active_user
from systems.geometry.component_authority import ComponentModels, from_source
from systems.geometry.development_baseline import DevelopmentBaselines
from systems.geometry.engine_redesign import compile_candidate
from systems.geometry.engine_redesign_authority import Redesigns
from systems.projects.authority import Head, InvalidRecord, identity


def command(args):
    identity(args.operation_id, "operator operation ID")
    if (
        len(args.operation_id) > 110
        or not 0 < len(args.title.strip()) <= 240
        or not 0 < len(args.reason.strip()) <= 1000
    ):
        raise InvalidRecord(
            "Bounded operation, title and explicit development-only selection reason required"
        )
    root = args.app_root
    store = root / "engineering_state/v1"
    auth = root / "auth/users.sqlite"
    if (
        not root.is_absolute()
        or root != root.resolve()
        or not (store / "metadata.sqlite3").is_file()
        or not auth.is_file()
    ):
        raise InvalidRecord(
            "Explicit existing real application root with authority/auth databases required; no initialization"
        )
    actor = active_user(auth, args.user)
    actor.require(write=True)
    with CoordinatorLease(store):
        require_completed_restore(store)
        repo = SQLiteProjectRepository(store)
        project = repo.get_project(actor, args.project)
        components = SimpleNamespace(repository=repo, models=ComponentModels(repo))
        redesigns = Redesigns(components)
        baselines = DevelopmentBaselines(redesigns)
        source = redesigns.source(actor, args.project, args.source_commit)
        seed = redesigns.seed(actor, args.project, source.commit_id)
        active = baselines.current(actor, args.project)
        object_id = str(
            uuid5(
                UUID(args.project),
                actor.user_id + ":engine-redesign:" + args.operation_id,
            )
        )
        preview = {
            "schema": "cosmos.development-baseline-install-preview.v1",
            "app_root": str(root),
            "project_id": project.project_id,
            "project_title": project.title,
            "actor_user_id": actor.user_id,
            "source_commit_id": source.commit_id,
            "source_head": asdict(source.head),
            "candidate_object_id": object_id,
            "recipe_sha256": seed["inspection"]["recipe_sha256"],
            "method_sources": baselines.loaded_methods,
            "operator_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "expected_baseline": active["expected"],
            "operation_id": args.operation_id,
            "title": args.title,
            "reason": args.reason,
            "source_metal_parts": seed["inspection"]["source_metal_parts"],
            "candidate_metal_groups": seed["inspection"]["candidate_metal_groups"],
            "source_retention": "RETAIN_IMMUTABLE_HISTORY_NO_DELETION",
            "selection_scope": "PRELIMINARY_GEOMETRY_DEVELOPMENT_ONLY",
            "native_build": "NOT_REQUESTED",
            "physical_validation": "NOT_PERFORMED",
            "r08": "ON_HOLD",
        }
        preview_hash = sha256(canonical_json_dumps(preview).encode()).hexdigest()
        if args.apply_preview_sha256 is None:
            return {
                "ok": True,
                "applied": False,
                "preview_sha256": preview_hash,
                "preview": preview,
            }
        if args.apply_preview_sha256 != preview_hash:
            raise InvalidRecord(
                "Installation preview changed. Re-preview and review; no baseline was switched"
            )
        body = {
            "title": args.title,
            "source_commit_id": source.commit_id,
            "expected_source": asdict(source.head),
            "specification": seed["specification"],
            "expected": asdict(Head.absent()),
            "operation_id": args.operation_id,
        }
        request_hash = sha256(
            canonical_json_dumps(
                {"action": "operator.compact-candidate", "preview": preview}
            ).encode()
        ).hexdigest()
        saved = redesigns.save(
            actor,
            args.project,
            object_id,
            body,
            Head.absent(),
            source.head,
            request_hash,
        )
        selected = baselines.activate(
            actor,
            args.project,
            candidate_commit_id=saved.commit_id,
            expected_candidate=saved.head,
            expected=Head(**active["expected"]),
            operation_id=args.operation_id + ":activate",
            command_hash=sha256((preview_hash + ":activate").encode()).hexdigest(),
            reason=args.reason,
        )
        after = repo.get_snapshot(
            actor, args.project, domain=source.domain, object_id=source.object_id
        )
        if after.head != source.head:
            raise InvalidRecord(
                "Source changed during installation; selected baseline requires reconciliation"
            )
        candidate = compile_candidate(from_source(source), seed["specification"])
        return {
            "ok": True,
            "applied": True,
            "preview_sha256": preview_hash,
            "baseline": selected["baseline"],
            "candidate": redesigns.envelope(actor, saved)["authority"],
            "research_input": {
                "schema": "cosmos.compact-engine-input.v1",
                "source_commit_id": source.commit_id,
                "source_model": {
                    "snapshot_json": candidate.plan.snapshot.to_json(),
                    "graph_json": candidate.plan.graph.to_json(),
                },
                "specification": candidate.specification,
                "recipe_sha256": candidate.wire()["recipe_sha256"],
            },
            "source_head_unchanged": True,
            "qualification": "NOT_PERFORMED",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--apply-preview-sha256")
    parser.add_argument("--output", type=Path, help="NEW receipt path; never overwrite")
    args = parser.parse_args()
    if args.output is not None and (
        not args.output.is_absolute()
        or args.output.exists()
        or not args.output.parent.is_dir()
    ):
        raise InvalidRecord("Existing parent and a new absolute receipt path required")
    value = command(args)
    if args.output is not None:
        with args.output.open("x") as stream:
            json.dump(value, stream, allow_nan=False, indent=2)
        print(
            json.dumps(
                {
                    "ok": True,
                    "applied": value["applied"],
                    "preview_sha256": value["preview_sha256"],
                    "receipt": str(args.output),
                }
            )
        )
    else:
        print(json.dumps(value, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
