"""COSMOS desktop GUI launcher."""

from __future__ import annotations

from gui.application import launch_desktop_application

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="COSMOS 0.1 desktop shell")
    parser.add_argument("--root", default="cosmos_app_data")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    launch_desktop_application(
        root=args.root,
        host=args.host,
        port=args.port,
        browser_mode=args.browser,
        headless=args.headless,
    )
