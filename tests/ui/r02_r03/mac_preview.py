"""Isolated R02/R03 Mac usability fixture; never opens existing COSMOS storage."""
from __future__ import annotations

import argparse
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from api.authentication import UserRole
from api.propulsion_workflow import run_subsystems
from gui.native_window import launch_native_window
from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer
from tests.fixtures.knowledge_reports import add_knowledge
from tests.fixtures.propulsion_subsystems import (
    cooling_inputs,
    nozzle_inputs,
    seeded_design,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="Use the actual installed pywebview/Cocoa window")
    parser.add_argument("--port", type=int, default=8850)
    parser.add_argument("--connect", help="Open an already running task-owned loopback preview (native only)")
    args = parser.parse_args()
    if args.connect:
        url = urlsplit(args.connect)
        if not args.native or url.scheme != "http" or url.hostname != "127.0.0.1" or url.port not in (8845, 8850) or url.path not in ("", "/") or url.query or url.fragment:
            parser.error("Connect is restricted to the task-owned loopback preview on 8845/8850")
        launch_native_window(url=args.connect, title="COSMOS R02/R03 synthetic usability preview")
        return
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged loopback port")
    root = Path(tempfile.mkdtemp(prefix="cosmos-r02-r03-usability."))
    app = CosmosApplication(root, new_shell=True, simulation_enabled=True,
        comparison_enabled=True, knowledge_reports_enabled=True, ngg_enabled=False)
    app.auth.register_user(login_id="presentation-qa", password="isolated-presentation-qa",
        display_name="Synthetic Presentation QA", designation="Synthetic fixture",
        employee_id="QA", team="Local UI QA", role=UserRole.ENGINEER)
    for label in ("A", "B"):
        design = seeded_design()
        design.name = f"Synthetic presentation fixture {label} — not hardware evidence"
        result = run_subsystems(design, inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()},
            stages=("nozzle", "cooling"), store=app.design_store)
        if not result["execution_ok"]:
            raise RuntimeError("Synthetic visualization fixture could not be prepared")
    add_knowledge(app.knowledge_workspace(), approved=False)

    class Handler(CosmosApplicationHandler):
        application = app

        def log_message(self, *_args: object) -> None:
            pass

    server = PreviewHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Synthetic UI preview: http://127.0.0.1:{args.port}/\nStorage: {root}\n"
          "Choose ENGINEER; login presentation-qa / isolated-presentation-qa.\n"
          "Test fixture only: no hardware evidence, no native geometry acceptance, no production credentials.", flush=True)
    try:
        if args.native:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            launch_native_window(url=f"http://127.0.0.1:{args.port}/", title="COSMOS R02/R03 synthetic usability preview")
            server.shutdown()
            thread.join(timeout=5)
        else:
            server.serve_forever()
    finally:
        server.server_close()
        for name in ("_comparison_workspace", "_simulation_workspace", "_ngg_workspace"):
            workspace = getattr(app, name, None)
            if workspace is not None:
                workspace.close()
        print(f"Preview stopped. Recoverable synthetic fixture retained at {root}; existing application data was not used.")


if __name__ == "__main__":
    main()
