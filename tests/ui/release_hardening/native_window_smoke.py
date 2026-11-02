"""Instrument the actual existing pywebview/Cocoa renderer; never browser fallback."""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import webview

from gui.native_window import launch_native_window

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
assert args.url.startswith("http://127.0.0.1:"), "Only the isolated local P12 preview is in scope"
original = webview.start
failure = []
logger = logging.getLogger(__name__)


def instrumented_start(*positional, **kwargs):
    window = webview.windows[0]
    def loaded():
        try:
            data = json.loads(window.evaluate_js("JSON.stringify({title:document.title,url:location.href,usernameInput:!!document.querySelector('#login-id'),privateHint:document.body.innerText.includes('first-login.json'),oldSharedPasswordVisible:document.body.innerText.includes('COSMOS-Dev-2026!')})"))
            assert data["url"].startswith(args.url) and data["usernameInput"] and data["privateHint"]
            assert not data["oldSharedPasswordVisible"]
            with args.output.open("x") as handle:
                json.dump({"pass": True, "actual_native_renderer": True, "browser_fallback": False,
                           "backend": window.gui.__name__, "document": data,
                           "scope": "Existing desktop native adapter and real Cocoa/WebKit login DOM, not all scientific flows inside the native window"}, handle, indent=2)
        except Exception as error:
            logger.exception("Native renderer evidence capture failed")
            failure.append(str(error))
        finally:
            window.destroy()
    window.events.loaded += loaded
    return original(*positional, **kwargs)


webview.start = instrumented_start
launch_native_window(url=args.url, title="COSMOS P12 isolated native renderer check")
if failure or not args.output.is_file():
    raise SystemExit("Native renderer smoke failed: " + "; ".join(failure))
print("Actual native Cocoa renderer PASS; no browser fallback")
