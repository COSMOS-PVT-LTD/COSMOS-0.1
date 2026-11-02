"""Installed desktop entrypoint. Existing roots stay separate and in place."""

from __future__ import annotations

import argparse
import html
import json
import logging
import threading
from pathlib import Path

from gui.desktop_config import enable_workspaces, existing_root, read_profile
from gui.desktop_runtime import DesktopServer
from gui.native_window import require_native_runtime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ROUTES = {
    "Projects": "/app/projects",
    "Rocket Engine": "/app/workbench/rocket-engine",
    "Native Geometry / CAD": "/app/workbench/native-geometry",
    "Simulation": "/app/workbench/simulation",
    "Verification and Comparison": "/app/workbench/comparison",
    "Visualization and Graphs": "/app/workbench/visualization",
    "Knowledge": "/app/workbench/knowledge",
    "Reports, History and Governance": "/app/workbench/reports",
}


class WorkspaceBridge:
    def __init__(self, session):
        self._session = session

    def open_workspace(self, key):
        # Only the local chooser has the bridge action; never accept paths or
        # commands from engineering content or an externally navigated page.
        if self._session.window.get_current_url() not in (None, "about:blank"):
            return {"error": "Choose a workspace from the Desktop home screen"}
        # Resolve the bridge promise before replacing its HTML document. The
        # chooser performs same-window navigation after receiving the local URL.
        return self._session.open_workspace(key, navigate=False)


class DesktopSession:
    def __init__(self, workspaces):
        self.workspaces = {w.key: w for w in workspaces}
        self.server = None
        self.window = None
        self.active = None
        self._lock = threading.Lock()
        self._research_tools = []

    def home(self):
        rows = "".join(
            f'<button onclick="openWorkspace({html.escape(json.dumps(w.key), quote=True)})"><strong>{html.escape(w.label)}</strong><small>{html.escape(str(w.root))}</small></button>'
            for w in self.workspaces.values()
        )
        return (
            """<!doctype html><html><head><meta charset="utf-8"><title>COSMOS Desktop</title><style>
        body{background:#101923;color:#e3edf6;font:16px -apple-system,sans-serif;margin:0;padding:6vh 7vw}h1{font-size:34px}p{color:#b6c6d6;line-height:1.6;max-width:900px}button{display:block;text-align:left;width:100%;max-width:950px;padding:22px;margin:16px 0;background:#192b3b;color:#e3edf6;border:1px solid #58738b;border-radius:6px;cursor:pointer}button:focus{outline:3px solid #72cdff}strong{display:block;font-size:19px}small{display:block;margin-top:10px;overflow-wrap:anywhere;color:#b8cadd}#message{color:#ffcc85}footer{margin-top:35px;color:#a7bacb}
        </style></head><body><h1>COSMOS 0.1 · Desktop</h1><p>Open an existing workspace. Project history and accounts remain in their original folders. Switching workspaces does not copy, merge, delete or migrate data.</p>"""
            + rows
            + """<p id="message" role="status"></p><footer>Local engineering software · preliminary research models. Software availability is not hardware validation.<br>Engine regeneration and R08 remain on hold. Use the Workspaces menu to return here.</footer><script>
        let opening=false;
        async function openWorkspace(key){if(opening)return;opening=true;const m=document.getElementById('message');m.textContent='Opening workspace…';document.querySelectorAll('button').forEach(b=>b.disabled=true);let timer;try{const r=await Promise.race([window.pywebview.api.open_workspace(key),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Workspace startup not confirmed within 30 seconds. Use Workspaces to return here before retrying; details are in Library/Logs/COSMOS/desktop.log.')),30000)})]);if(r.error)m.textContent=r.error;else location.assign(r.url);}catch(e){m.textContent=String(e)}finally{clearTimeout(timer);opening=false;document.querySelectorAll('button').forEach(b=>b.disabled=false)}}
        </script></body></html>"""
        )

    def _confirm_leave(self):
        return self.server is None or self.window.create_confirmation_dialog(
            "Change workspace",
            "Save your edits and wait for running jobs to finish first. Changing workspace closes this backend and cancels unfinished jobs. Continue?",
        )

    def open_workspace(self, key, *, navigate=True):
        with self._lock:
            if type(key) is not str or key not in self.workspaces:
                return {"error": "Unknown registered workspace"}
            if not self._confirm_leave():
                return {"error": "Workspace unchanged"}
            try:
                root = existing_root(self.workspaces[key].root)
                if self.server:
                    self.server.close()
                    self.server = None
                self.server = DesktopServer(root).start()
                self.active = key
                self.window.set_title("COSMOS 0.1 · " + self.workspaces[key].label)
                url = self.server.url + "/"
                if navigate:
                    self.window.load_url(url)
                return {"ok": True, "url": url}
            except Exception as error:
                logger.exception("Desktop workspace could not open")
                if self.server:
                    self.server.close()
                self.server = None
                self.active = None
                return {"error": str(error)}

    def choose(self):
        with self._lock:
            if not self._confirm_leave():
                return
            if self.server:
                self.server.close()
                self.server = None
            self.active = None
            self.window.set_title("COSMOS 0.1 · Desktop")
            self.window.load_html(self.home())

    def navigate(self, route):
        if self.server and route in ROUTES.values():
            # Existing frontend link guards retain unsaved-form protection.
            self.window.evaluate_js(
                "(()=>{const a=document.createElement('a');a.href="
                + json.dumps(route)
                + ";document.body.append(a);a.click();a.remove()})()"
            )

    def open_existing_folder(self):
        import webview

        selected = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if not selected:
            return
        try:
            root = existing_root(Path(selected[0]))
        except ValueError as error:
            self.window.create_confirmation_dialog("Workspace not opened", str(error))
            return
        from hashlib import sha256

        from gui.desktop_config import Workspace

        key = "folder-" + sha256(str(root).encode()).hexdigest()[:12]
        self.workspaces[key] = Workspace(key, "Existing workspace · " + root.name, root)
        self.choose()

    def close(self):
        with self._lock:
            for tool in self._research_tools:
                tool._close()
                if tool._window is not None:
                    tool._window.confirm_close = False
                    tool._window.destroy()
            self._research_tools.clear()
            if self.server:
                self.server.close()
                self.server = None

    def research_tools(self):
        from gui.desktop_research import open_tools

        self._research_tools.append(open_tools(Path(__file__).resolve().parents[1]))


def main(argv=None, *, confirm_quit=True, terminate_on_close=True):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--workspace")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate packaged imports and profiles without opening user data",
    )
    args = parser.parse_args(argv)
    workspaces, runtimes = read_profile(args.profile)
    enable_workspaces(runtimes)
    if args.check:
        import importlib

        for name in ("webview", "cea", "numpy", "pypdf"):
            importlib.import_module(name)
        import os
        import ssl

        certificates = Path(os.environ.get("SSL_CERT_FILE", ""))
        if (
            not certificates.is_file()
            or not certificates.resolve().is_relative_to(args.profile.parent.resolve())
            or ssl.create_default_context().cert_store_stats()["x509_ca"] == 0
        ):
            raise ValueError(
                "Bundled TLS trust roots required; certificate verification is never bypassed"
            )
        import subprocess

        subprocess.run(
            [
                str(args.profile.parent / ".venv-cad-inspection/bin/python"),
                "-c",
                "import OCP, vtkmodules.vtkFiltersCore",
            ],
            check=True,
            timeout=30,
        )
        from api.occt_component_runtime import configuration as occt
        from api.pico_component_runtime import configuration as pico

        occt(Path(runtimes["COSMOS_NGG_RUNTIME_CONFIG"]))
        pico(Path(runtimes["COSMOS_PICOGK_COMPONENT_CONFIG"]))
        print(
            json.dumps(
                {
                    "desktop_imports": "PASS",
                    "occt_profile": "PASS",
                    "picogk_profile": "PASS",
                    "user_data_opened": False,
                }
            )
        )
        return
    require_native_runtime()
    import webview
    from webview.menu import Menu, MenuAction

    session = DesktopSession(workspaces)
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["ALLOW_FILE_URLS"] = False
    session.window = webview.create_window(
        "COSMOS 0.1 · Desktop",
        html=session.home(),
        js_api=WorkspaceBridge(session),
        width=1500,
        height=960,
        min_size=(1100, 700),
        confirm_close=False,
        text_select=True,
        background_color="#101923",
    )

    def closing():
        # pywebview's locking closing event is invoked on Cocoa's main thread.
        # Confirm before cleanup, including App-menu Quit (which need not emit
        # a per-window closed event before the OS terminates the application).
        if confirm_quit:
            from AppKit import NSAlert, NSAlertFirstButtonReturn

            alert = NSAlert.alloc().init()
            alert.setMessageText_("Close COSMOS Desktop?")
            alert.setInformativeText_(
                "Save your edits first. Unfinished calculations and research jobs will be cancelled; saved projects will not be deleted."
            )
            alert.addButtonWithTitle_("Close COSMOS")
            alert.addButtonWithTitle_("Cancel")
            if alert.runModal() != NSAlertFirstButtonReturn:
                return False
        session.close()
        return True

    def closed():
        session.close()
        if terminate_on_close:
            from AppKit import NSApp
            from PyObjCTools import AppHelper

            # Last-window closure can leave NSApplication.run waiting without
            # another event. Terminate only after owned workers/leases close.
            AppHelper.callAfter(NSApp.terminate_, None)

    session.window.events.closing += closing
    session.window.events.closed += closed

    def present():
        from AppKit import NSApp, NSImage
        from Foundation import NSProcessInfo
        from PyObjCTools import AppHelper

        # loaded handlers run on a Python event thread. All AppKit window and
        # activation calls must be scheduled on Cocoa's main run loop.
        def activate():
            NSProcessInfo.processInfo().setProcessName_("COSMOS Desktop")
            NSApp.setActivationPolicy_(0)
            icon = args.profile.parent.parent / "cosmos_logo.icns"
            if icon.is_file():
                NSApp.setApplicationIconImage_(
                    NSImage.alloc().initWithContentsOfFile_(str(icon))
                )
            NSApp.activateIgnoringOtherApps_(True)
            session.window.show()
            logger.info("COSMOS primary native window loaded and presented")

        AppHelper.callAfter(activate)

    session.window.events.loaded += present
    menus = [
        Menu(
            "Workspaces",
            [
                MenuAction("Choose saved data folder…", session.choose),
                MenuAction(
                    "Open another existing data folder…", session.open_existing_folder
                ),
            ],
        ),
        Menu(
            "Engineering",
            [
                MenuAction(label, lambda route=route: session.navigate(route))
                for label, route in ROUTES.items()
            ],
        ),
        Menu(
            "Research Tools",
            [MenuAction("Compact CAD generation…", session.research_tools)],
        ),
    ]
    try:

        def startup():
            session.window.show()
            logger.info("COSMOS native window startup requested")
            if args.workspace:
                session.open_workspace(args.workspace)

        webview.start(
            func=startup,
            debug=False,
            private_mode=True,
            menu=menus,
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
