"""Explicit R05 operator tools. Never auto-migrate, overwrite or switch roots."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infrastructure.persistence.files import CoordinatorLease
from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.legacy_import import (
    import_legacy,
    original_file,
    preview_legacy,
)
from infrastructure.persistence.portability import (
    ProjectPortability,
    _write,
    backup_store,
    canonical,
    require_completed_restore,
    restore_store,
)
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import InvalidRecord, Principal


def active_user(database: Path, user_id: str) -> Principal:
    if not database.is_absolute() or not database.is_file() or database.is_symlink():
        raise InvalidRecord("Use an explicit existing local users.sqlite; no account initialization/import.")
    connection = sqlite3.connect("file:" + quote(str(database), safe="/") + "?mode=ro", uri=True)
    try:
        row = connection.execute("SELECT user_id,role,active FROM users WHERE user_id=?", (user_id,)).fetchone()
    finally:
        connection.close()
    if row is None:
        raise InvalidRecord("Unknown stable user; no owner guessing.")
    result = Principal(row[0], row[1], bool(row[2]))
    result.require()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("legacy-preview", "legacy-import", "package-preview", "package-export", "package-import", "backup", "restore", "upgrade-copy", "inventory"))
    parser.add_argument("--store", type=Path, help="Existing engineering_state/v1, not an application/workspace root")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, help="Explicit absent output; existing files/roots are never overwritten")
    parser.add_argument("--confirm", help="Exact preview/backup manifest SHA256, not an automatic yes flag")
    parser.add_argument("--auth-db", type=Path)
    parser.add_argument("--user", help="Active stable local user ID")
    parser.add_argument("--project")
    parser.add_argument("--mapping", type=Path, help="Explicit source identity to active local user ID JSON mapping")
    parser.add_argument("--confirm-memberships", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional absent JSON receipt file")
    args = parser.parse_args()
    required = {
        "legacy-preview": ("source",), "legacy-import": ("source", "confirm", "mapping", "auth_db", "user", "project"),
        "package-preview": ("source",), "package-export": ("destination", "auth_db", "user", "project"),
        "package-import": ("source", "confirm", "mapping", "auth_db", "user"), "backup": ("destination",),
        "restore": ("source", "destination", "confirm"), "upgrade-copy": ("source", "destination", "confirm"), "inventory": (),
    }
    missing = ["--" + name.replace("_", "-") for name in required[args.action] if getattr(args, name) is None]
    if missing:
        parser.error(args.action + " requires " + ", ".join(missing))
    result = None
    if args.action == "legacy-preview":
        result = preview_legacy(args.source)
    elif args.action in {"restore", "upgrade-copy"}:
        result = restore_store(args.source, args.destination, confirmed_manifest=args.confirm, upgrade=args.action == "upgrade-copy")
    else:
        if args.store is None or not args.store.is_absolute() or not (args.store / "metadata.sqlite3").is_file():
            raise InvalidRecord("Choose an explicit existing engineering store; a missing store is never initialized here.")
        with CoordinatorLease(args.store):
            require_completed_restore(args.store)
            repo = SQLiteProjectRepository(args.store)
            service = ProjectPortability(repo)
            if args.action == "backup":
                result = backup_store(repo, args.destination)
            elif args.action == "inventory":
                from dataclasses import asdict
                result = asdict(inventory(repo))
            elif args.action == "package-preview":
                result = service.preview(original_file(args.source, service.limits.max_bytes))
            else:
                actor = active_user(args.auth_db, args.user)
                actor.require(write=True)
                if args.action == "package-export":
                    project = repo.get_project(actor, args.project)
                    raw = service.export(actor, args.project, project.head)
                    _write(args.destination, raw)
                    result = service.preview(raw)
                else:
                    mapping = json.loads(original_file(args.mapping))
                    users = {key: active_user(args.auth_db, value) for key, value in mapping.items()}
                    if args.action == "legacy-import":
                        result = import_legacy(repo, actor, args.project, args.source, confirmed_preview=args.confirm, selected_owners=users)
                    else:
                        result = service.import_project(actor, original_file(args.source, service.limits.max_bytes),
                            confirmed_manifest=args.confirm, users=users, confirmed_memberships=args.confirm_memberships)
    if args.output:
        _write(args.output, canonical(result))
        print("Receipt saved:", args.output)
    else:
        print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
