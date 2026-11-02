"""Actual packaged Cocoa/WebKit → login → current workspace routes, isolated data."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("NEW native smoke output required")
    import webview

    from api.authentication import AuthService
    from gui import desktop_app
    from gui.desktop_config import Workspace

    isolated = Path(tempfile.mkdtemp(prefix="cosmos-desktop-native-"))
    AuthService(isolated / "auth")
    profile_reader = desktop_app.read_profile

    def read_profile(path):
        _, runtimes = profile_reader(path)
        return [
            Workspace(
                "native-test",
                "Isolated native verification · NOT hardware data",
                isolated,
            )
        ], runtimes

    desktop_app.read_profile = read_profile
    original = webview.start
    evidence = {
        "schema": "cosmos.desktop-native-smoke.v1",
        "isolated_root": str(isolated),
        "browser_fallback": False,
        "routes": [],
    }
    failures = []

    def start(*_args, **kwargs):
        startup = kwargs.get("func")
        window = webview.windows[0]
        # Driver intentionally destroys its own isolated test window without a
        # human confirmation dialog; the installed entrypoint keeps it enabled.
        window.confirm_close = False

        def evaluate(code):
            return window.evaluate_js(code)

        def wait_for(expression):
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if evaluate(expression):
                    return
                time.sleep(0.1)
            raise AssertionError("Native renderer timeout: " + expression)

        def driver():
            try:
                if startup:
                    startup()
                wait_for("!!window.pywebview?.api?.open_workspace")
                evaluate("openWorkspace('native-test')")
                wait_for("!!document.querySelector('#login-id')")
                evaluate(
                    "window.__login=null;fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({login_id:'cosmos-admin',password:'COSMOS-Dev-2026!',login_profile:'ADMIN'})}).then(async r=>window.__login={status:r.status,body:await r.json()})"
                )
                wait_for("!!window.__login")
                login = evaluate("window.__login")
                assert login["status"] == 200, login
                evidence["native_backend"] = window.gui.__name__
                evidence["login_status"] = login["status"]
                evaluate(
                    "window.__catalog=null;fetch('/api/workbenches').then(r=>r.json()).then(r=>window.__catalog=r)"
                )
                wait_for("!!window.__catalog")
                evidence["catalog"] = evaluate("window.__catalog")
                for label, route in desktop_app.ROUTES.items():
                    window.load_url(desktop_app_session_url(window) + route)
                    wait_for(
                        "document.readyState==='complete' && location.pathname==="
                        + json.dumps(route)
                    )
                    wait_for(
                        "!!document.querySelector('main') || !!document.querySelector('#app-shell') || !!document.querySelector('form')"
                    )
                    page = evaluate(
                        "({path:location.pathname,title:document.title,bytes:document.documentElement.outerHTML.length,unauthenticated:!!document.querySelector('#login-id'),error:document.body.innerText.includes('404 Not Found')})"
                    )
                    assert (
                        not page["unauthenticated"]
                        and not page["error"]
                        and page["bytes"] > 1000
                    ), page
                    evidence["routes"].append({"label": label, **page})
                    remote = evaluate(
                        "performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n)&&new URL(n).hostname!=='127.0.0.1')"
                    )
                    assert not remote, remote
                evidence["webgl2"] = evaluate(
                    "!!document.createElement('canvas').getContext('webgl2')"
                )
                evidence["pass"] = True
            except Exception as error:  # noqa: BLE001 - persist native boundary failures before closing the test window
                failures.append(str(error))
                evidence.update({"pass": False, "error": str(error)})
            finally:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x") as stream:
                    json.dump(evidence, stream, indent=2)
                window.destroy()

        kwargs["func"] = driver
        return original(**kwargs)

    webview.start = start
    desktop_app.main(
        ["--profile", str(ROOT / "desktop-profile.json")],
        confirm_quit=False,
        terminate_on_close=False,
    )
    assert not failures, failures
    print("Actual packaged Cocoa/WebKit route verification PASS; no browser opened")


def desktop_app_session_url(window):
    from urllib.parse import urlsplit

    parsed = urlsplit(window.get_current_url())
    assert parsed.hostname == "127.0.0.1"
    return f"http://127.0.0.1:{parsed.port}"


if __name__ == "__main__":
    main()
