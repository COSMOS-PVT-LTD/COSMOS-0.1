"""Launch the existing compact-development CAD project, never switch the default data root.

Starts no native build or R08 campaign. Refuses an occupied port rather than
terminating another viewer. Qualified legacy generators keep their own receipts;
the compact generator remains a separate unqualified research path.
"""

from __future__ import annotations

import argparse
import os
import socket
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8898)
    parser.add_argument(
        "--headless", action="store_true", help="Explicit developer HTTP-only viewer"
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a local unprivileged TCP port")
    repo = Path(__file__).resolve().parents[1]
    app = repo / "output/picogk-components-2026-10-24/app-data"
    database = app / "engineering_state/v1/metadata.sqlite3"
    project = "bb7ebea6-15f9-43b8-b6c0-fd2a2d358155"
    if not database.is_file() or not (app / "auth/users.sqlite").is_file():
        raise SystemExit(
            "Existing approved CAD project/auth root is unavailable; nothing was initialized"
        )
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        found = connection.execute(
            "SELECT 1 FROM objects WHERE project_id=? AND domain=?",
            (project, "engine-development-baseline"),
        ).fetchone()
    if found is None:
        raise SystemExit(
            "No approved development baseline installed in this root; select it explicitly first"
        )
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError as error:
            raise SystemExit(
                f"Port {args.port} unavailable. No process was stopped. Save edits and inspect the existing viewer, or choose --port with a free port."
            ) from error
    flags = {
        "COSMOS_NEW_SHELL": "1",
        "COSMOS_DURABLE_PROJECTS": "1",
        "COSMOS_NGG": "1",
        "COSMOS_NEW_SIM_UI": "1",
        "COSMOS_NEW_VV_UI": "1",
        "COSMOS_NEW_KNOWLEDGE_REPORTS_UI": "1",
        "COSMOS_NGG_RUNTIME_CONFIG": str(
            repo
            / "docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/occt-runtime/runtime.json"
        ),
        "COSMOS_PICOGK_COMPONENT_CONFIG": str(
            repo
            / "docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/pico-runtime-v4/runtime.json"
        ),
    }
    for name in ("COSMOS_NGG_RUNTIME_CONFIG", "COSMOS_PICOGK_COMPONENT_CONFIG"):
        if not Path(flags[name]).is_file():
            raise SystemExit(
                "Existing legacy runtime profile missing; no replacement profile was synthesized"
            )
    os.environ.update(flags)
    from gui.application import launch_desktop_application

    print(
        f"Open http://127.0.0.1:{args.port}/app/workbench/native-geometry?project={project}",
        flush=True,
    )
    print(
        "Preliminary CAD development baseline. Regenerated research files are loaded separately; matched thermal/feed physics and R08 acceptance remain pending.",
        flush=True,
    )
    from systems.projects.authority import IntegrityFailure

    try:
        launch_desktop_application(
            root=str(app), host="127.0.0.1", port=args.port, headless=args.headless
        )
    except IntegrityFailure as error:
        raise SystemExit(
            "Saved workspace integrity check failed: "
            + str(error)
            + " No project history was reset. Recover the exact missing/corrupt retained bytes from a verified copy; do not delete engineering_state or disable integrity checks."
        ) from None


if __name__ == "__main__":
    main()
