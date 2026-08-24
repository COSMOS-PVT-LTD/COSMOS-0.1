"""COSMOS 0.1 desktop application entry point."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_repo_path() -> None:
    repo_root = Path(__file__).resolve().parent
    candidate = str(repo_root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def main() -> None:
    _bootstrap_repo_path()
    import argparse

    from gui.application import launch_desktop_application

    parser = argparse.ArgumentParser(
        description="COSMOS 0.1 — local engineering desktop application (native window)",
    )
    parser.add_argument("--root", default="cosmos_app_data", help="Local application data directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Developer mode: open in the default browser instead of the native window",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run HTTP server only (no window)",
    )
    args = parser.parse_args()
    launch_desktop_application(
        root=args.root,
        host=args.host,
        port=args.port,
        browser_mode=args.browser,
        headless=args.headless,
    )


if __name__ == "__main__":
    main()
