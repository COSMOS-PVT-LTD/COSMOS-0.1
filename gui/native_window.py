"""Native desktop window for COSMOS (pywebview — macOS WebKit / Windows Edge)."""

from __future__ import annotations

from pathlib import Path
import sys
import threading
import time

__all__ = ("NativeWindowError", "launch_native_window", "require_native_runtime")


class NativeWindowError(RuntimeError):
    """Native desktop runtime is unavailable."""


def require_native_runtime() -> None:
    try:
        import webview  # noqa: F401
    except ImportError as exc:
        raise NativeWindowError(
            "COSMOS desktop requires pywebview for a native application window.\n"
            "Install desktop dependencies:\n"
            "  pip install -r requirements-desktop.txt\n"
            "Then launch again:\n"
            "  python main.py\n"
            "Developer browser mode (not for end users):\n"
            "  python main.py --browser",
        ) from exc


def _wait_for_server(url: str, *, timeout: float = 15.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.15)
    raise NativeWindowError(f"COSMOS server did not become ready at {url}")


def launch_native_window(
    *,
    url: str,
    title: str = "COSMOS 0.1",
    width: int = 1440,
    height: int = 900,
    min_size: tuple[int, int] = (1100, 700),
    icon_path: Path | None = None,
) -> None:
    """Open a standalone native window (RPL / SolidWorks style — not a browser tab)."""

    require_native_runtime()
    import webview

    resolved_icon = icon_path
    if resolved_icon is None:
        candidate = Path(__file__).resolve().parent / "assets" / "cosmos_logo.png"
        if candidate.is_file():
            resolved_icon = candidate

    window = webview.create_window(
        title,
        url,
        width=width,
        height=height,
        min_size=min_size,
        resizable=True,
        fullscreen=False,
        frameless=False,
        easy_drag=False,
        background_color="#04060d",
        text_select=True,
    )

    def on_loaded() -> None:
        # macOS: ensure the app presents as a foreground application.
        if sys.platform == "darwin":
            try:
                from AppKit import NSApp  # type: ignore[import-untyped]

                NSApp.activateIgnoringOtherApps_(True)
            except Exception:
                pass

    if hasattr(window, "events") and hasattr(window.events, "loaded"):
        window.events.loaded += on_loaded

    webview.start(debug=False, icon=str(resolved_icon) if resolved_icon else None)


def start_server_thread(target, *, root, host: str, port: int) -> threading.Thread:
    thread = threading.Thread(
        target=target,
        kwargs={"root": root, "host": host, "port": port},
        daemon=True,
        name="cosmos-http-server",
    )
    thread.start()
    return thread
