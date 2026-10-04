"""COSMOS desktop application lifecycle."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from gui.native_window import (
    NativeWindowError,
    launch_native_window,
    start_server_thread,
)

__all__ = ("launch_desktop_application",)


def launch_desktop_application(
    *,
    root: Path | str = "cosmos_app_data",
    host: str = "127.0.0.1",
    port: int = 8780,
    browser_mode: bool = False,
    headless: bool = False,
) -> None:
    """Start COSMOS as a local installed application."""

    from gui.server import serve_application

    url = f"http://{host}:{port}/"

    if headless:
        serve_application(root, host=host, port=port)
        return

    if browser_mode:
        from gui.native_window import _wait_for_server

        thread = start_server_thread(serve_application, root=root, host=host, port=port)
        _wait_for_server(url)
        webbrowser.open(url)
        print(f"COSMOS 0.1 running in browser mode at {url}", flush=True)
        thread.join()
        return

    thread = None
    try:
        from gui.native_window import _wait_for_server

        thread = start_server_thread(serve_application, root=root, host=host, port=port)
        _wait_for_server(url)
        if not thread.is_alive():
            raise NativeWindowError("COSMOS background server exited before the window opened.")
        print("COSMOS 0.1 — native desktop application", flush=True)
        print(f"Local server: {url}", flush=True)
        print("Close the COSMOS window to exit.", flush=True)
        launch_native_window(url=url, title="COSMOS 0.1")
    except NativeWindowError as exc:
        print(str(exc), file=sys.stderr)
        print(
            "\nNative desktop window unavailable — temporary browser fallback only.\n"
            "COSMOS is designed as an installed desktop app (like SolidWorks / ANSYS Workbench),\n"
            "not a browser product. Install pywebview and relaunch:\n"
            "  pip install -r requirements-desktop.txt\n"
            "  python main.py\n"
            f"\nFallback URL (developer use): {url}",
            flush=True,
        )
        webbrowser.open(url)
        if thread is not None and thread.is_alive():
            thread.join()
            return
        launch_desktop_application(
            root=root, host=host, port=port, browser_mode=True, headless=False
        )
