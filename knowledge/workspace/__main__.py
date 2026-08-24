"""python -m knowledge.workspace → local workspace HTTP UI."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_repo_path() -> None:
    """Ensure the COSMOS repo root wins over any third-party `knowledge` package."""

    repo_root = Path(__file__).resolve().parents[2]
    candidate = str(repo_root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def main() -> None:
    _bootstrap_repo_path()

    import argparse
    import json

    from knowledge.workspace.server import diagnose_startup, serve_workspace

    parser = argparse.ArgumentParser(description="COSMOS Knowledge Workspace (local)")
    parser.add_argument("--root", default="workspace_data")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--threaded",
        action="store_true",
        help="Use ThreadingHTTPServer (default is single-threaded HTTPServer for stability).",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Load the seed engineering corpus at startup (default: lazy on first search/chat).",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run startup probes and exit (useful if the server segfaults).",
    )
    args = parser.parse_args()

    if args.diagnose:
        print(json.dumps(diagnose_startup(args.root), indent=2, sort_keys=True))
        return

    serve_workspace(
        args.root,
        host=args.host,
        port=args.port,
        threaded=args.threaded,
        seed_corpus=args.seed,
    )


if __name__ == "__main__":
    main()
