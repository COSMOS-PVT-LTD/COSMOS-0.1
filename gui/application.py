"""COSMOS desktop application lifecycle."""

from __future__ import annotations

import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

from gui.native_window import (
    launch_native_window,
    require_native_runtime,
)

__all__ = ("launch_desktop_application",)


def launch_desktop_application(
    *,
    root: Path | str = "cosmos_app_data",
    host: str = "127.0.0.1",
    port: int = 8780,
    browser_mode: bool = False,
    headless: bool = False,
    start_path: str = "/",
) -> None:
    """Start COSMOS as a local installed application."""

    from gui.desktop_runtime import DesktopServer
    from gui.server import serve_application

    parsed = urlsplit(start_path)
    if (
        not start_path.startswith("/")
        or start_path.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or "\\" in start_path
    ):
        raise ValueError("Desktop start path must be a same-origin application route")

    if headless:
        serve_application(root, host=host, port=port)
        return

    if not browser_mode:
        require_native_runtime()
    with DesktopServer(root, host=host, port=port) as server:
        url = server.url + start_path
        if browser_mode:
            webbrowser.open(url)
            try:
                server.thread.join()
            except KeyboardInterrupt:
                pass
        else:
            launch_native_window(url=url, title="COSMOS 0.1")
