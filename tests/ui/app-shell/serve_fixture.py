"""P04 browser fixture; temporary designs, never the user's workspace storage."""

import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from api.propulsion_workflow import create_design, update_requirements
from gui.server import CosmosApplication, CosmosApplicationHandler

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    parser.add_argument("--port", type=int, default=8795)
    parser.add_argument("--legacy", action="store_true")
    args = parser.parse_args()
    app = CosmosApplication(args.state, new_shell=not args.legacy)
    if not app.design_store.list_design_ids():
        for name in ["P04 Fixture A", "P04 Fixture B"]:
            design = create_design(
                name=name,
                engineer="P04 isolated browser fixture",
                store=app.design_store,
            )
            update_requirements(
                design,
                updates={
                    "target_chamber_pressure": {"magnitude": 5, "unit_symbol": "bar"},
                    "target_thrust": {"magnitude": 10000, "unit_symbol": "N"},
                    "mixture_ratio": 3.2,
                },
                store=app.design_store,
            )

    class Handler(CosmosApplicationHandler):
        application = app

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(
        f"P04 isolated fixture on localhost:{args.port}; shell={not args.legacy}",
        flush=True,
    )
    server.serve_forever()
