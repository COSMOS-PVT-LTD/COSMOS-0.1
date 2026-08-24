"""COSMOS desktop application lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path
import webbrowser

from gui.native_window import NativeWindowError, launch_native_window, start_server_thread

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

    try:
        from gui.native_window import _wait_for_server

        thread = start_server_thread(serve_application, root=root, host=host, port=port)
        _wait_for_server(url)
        if not thread.is_alive():
            raise NativeWindowError("COSMOS background server exited before the window opened.")
        launch_native_window(url=url, title="COSMOS 0.1")
    except NativeWindowError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
