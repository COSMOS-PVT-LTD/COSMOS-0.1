"""Native file-dialog access to the existing unqualified compact CAD CLI.

No formulas, hidden assumptions, managed-data writes or R08 acceptance. Full
generation is never started automatically and retains its 10GiB storage guard.
"""

from __future__ import annotations

import math
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from infrastructure.geometry import WorkerCommand, WorkerSupervisor


class ResearchTools:
    def __init__(self, root):
        self._root = root
        self._window = None
        self._input = None
        self._parent = None
        self._future = None
        self._supervisor = None
        self._output = None
        self._lock = threading.Lock()

    def pick_input(self):
        import webview

        selected = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Compact research input (*.json)",),
        )
        if selected:
            self._input = Path(selected[0]).resolve()
        return str(self._input) if self._input else "No input selected"

    def pick_output(self):
        import webview

        selected = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if selected:
            self._parent = Path(selected[0]).resolve()
        return str(self._parent) if self._parent else "No output folder selected"

    def start(self, backend, voxel_m):
        if not self._lock.acquire(blocking=False):
            return {"error": "A research command is already being prepared"}
        try:
            return self._start(backend, voxel_m)
        except (ValueError, OSError) as error:
            return {"error": str(error)}
        finally:
            self._lock.release()

    def _start(self, backend, voxel_m):
        if self._window.get_current_url() not in (None, "about:blank"):
            return {"error": "Research tools must remain on their local native form"}
        if self._future is not None:
            return {
                "error": "One research build per tool window; open a new tool for another run"
            }
        if (
            backend not in ("occt", "picogk")
            or self._input is None
            or self._parent is None
        ):
            return {
                "error": "Select a research JSON and an existing output volume first"
            }
        if (
            not self._input.is_file()
            or self._input.stat().st_size > 2097152
            or not self._parent.is_dir()
        ):
            return {
                "error": "Bounded existing research input and output folder required"
            }
        if shutil.disk_usage(self._parent).free < 10 * 1024**3:
            return {
                "error": "Generation remains paused: this output volume needs at least 10GiB free. No files created or removed."
            }
        voxel = None
        if backend == "picogk":
            try:
                voxel = float(voxel_m)
            except (TypeError, ValueError):
                return {
                    "error": "Enter an explicit voxel size in metres; no assumed resolution"
                }
            if not math.isfinite(voxel) or not 2.5e-5 <= voxel <= 0.002:
                return {"error": "Voxel size must be between 0.000025 and 0.002 metres"}
        if not self._window.create_confirmation_dialog(
            "Unqualified research CAD",
            "Generate only a preliminary research artifact from the selected exact input? This does not establish engine efficiency, engineering acceptance, manufacturability or hot-fire readiness. R08 remains on hold.",
        ):
            return {"error": "No build started"}
        name = (
            "compact-research-"
            + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-")
            + uuid4().hex[:8]
        )
        self._output = self._parent / name
        command = [
            str(self._root / ".venv-cad-inspection/bin/python"),
            "-m",
            "scripts.generate_engine_redesign",
            str(self._input),
            "--output",
            str(self._output),
            "--backend",
            backend,
            "--research-only",
        ]
        if voxel is not None:
            command.extend(
                [
                    "--voxel-m",
                    str(voxel),
                    "--dotnet",
                    str(self._root / ".runtime-picogk/2026-10-24-v1/dotnet9/dotnet"),
                    "--picogk-worker",
                    str(self._root / ".runtime-compact/worker/PicoCompact.dll"),
                ]
            )
        self._supervisor = WorkerSupervisor(timeout_s=660)
        self._future = self._supervisor.submit(
            "desktop-" + uuid4().hex,
            WorkerCommand(tuple(command), (("PYTHONPATH", str(self._root)),)),
            b"",
            self._parent,
        )
        return {"status": "RUNNING", "output": str(self._output)}

    def status(self):
        if self._future is None:
            return {"status": "NOT_STARTED"}
        if not self._future.done():
            return {"status": "RUNNING", "output": str(self._output)}
        result = self._future.result()
        return {
            "status": "RESEARCH_ARTIFACT_CREATED"
            if result.code == "OK" and result.exit_code == 0
            else "FAILED_UNQUALIFIED",
            "output": str(self._output),
            "details": result.stderr.decode(errors="replace")[-2000:],
            "qualification": "NOT_PERFORMED",
            "r08": "ON_HOLD",
        }

    def _close(self):
        if self._supervisor:
            self._supervisor.close()
            self._supervisor = None


def open_tools(root):
    import webview

    tools = ResearchTools(root)
    page = """<!doctype html><html><head><meta charset="utf-8"><title>Compact research CAD</title><style>body{background:#101923;color:#e3edf6;font:16px -apple-system,sans-serif;padding:28px}p{line-height:1.5}button,input,select{padding:10px;background:#192b3b;color:#e3edf6;border:1px solid #7890a6;margin:6px 0}button{cursor:pointer}label{display:block;margin:15px 0}output,pre{display:block;white-space:pre-wrap;overflow-wrap:anywhere}small{color:#ffcc85}</style></head><body><h1>Compact research CAD</h1><p>In Native Geometry, save the exact candidate and download its research input first. Select that JSON here. A new output subfolder will be created; existing files are never overwritten.</p><small>UNQUALIFIED research artifacts only · R08 ON HOLD · no manufacturing or physical acceptance.</small><p><button onclick="pick('pick_input','inputPath')">Select research input JSON…</button><output id="inputPath">No input selected</output></p><p><button onclick="pick('pick_output','outputPath')">Select output volume/folder…</button><output id="outputPath">No output folder selected</output></p><label>Backend <select id="backend"><option value="picogk">PicoGK · implicit/VDB/STL</option><option value="occt">OCCT · exact solid/STEP</option></select></label><label>PicoGK voxel size [m], explicitly chosen <input id="voxel" type="number" step="any" placeholder="No default resolution"></label><p>At least 10GiB free on the selected output volume is required. Nothing runs until you explicitly start.</p><button id="run" onclick="run()">Generate preliminary research CAD</button><pre id="status" role="status"></pre><script>
    async function pick(method,id){document.getElementById(id).textContent=await window.pywebview.api[method]();}
    async function run(){const r=await window.pywebview.api.start(document.getElementById('backend').value,document.getElementById('voxel').value);document.getElementById('status').textContent=JSON.stringify(r,null,2);if(!r.error){document.getElementById('run').disabled=true;const timer=setInterval(async()=>{const s=await window.pywebview.api.status();document.getElementById('status').textContent=JSON.stringify(s,null,2);if(s.status!=='RUNNING')clearInterval(timer)},1000)}}
    </script></body></html>"""
    tools._window = webview.create_window(
        "COSMOS · Compact research CAD",
        html=page,
        js_api=tools,
        width=850,
        height=850,
        min_size=(700, 650),
        confirm_close=True,
    )
    tools._window.events.closed += tools._close
    return tools
