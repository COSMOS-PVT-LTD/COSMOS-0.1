"""Terminal-launched, read-only native view of one exact generated candidate.

Uses COSMOS's existing offline Three.js/CAD controls. No installation, accounts,
owner-store writes, generation, geometry acceptance or external hosting.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import threading
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>COSMOS regenerated engine · research inspection</title>
<link rel="stylesheet" href="/assets/ngg/styles.css">
<style>body{margin:0;padding:16px;background:#0b1420;color:#e4edf4;font:15px system-ui}
h1{font-size:23px;margin:0 0 8px}p{margin:8px 0}#cad{position:relative}
canvas{width:100%;height:68vh;display:block;border:1px solid #57718a}
#basis{overflow-wrap:anywhere;font-size:12px;color:#afc2d5}button,select,input{font:inherit}
</style><h1>1.5 kN methalox · regenerated compact engine</h1>
<p>Read-only research inspection · approximate reduced display, not manufacturing CAD.
Original STEP / native VDB / native STL are retained separately. Matched thermal/feed closure is not established.</p>
<p id="basis"></p><p id="status" role="status">Checking exact source and mesh bytes…</p>
<div id="cad"><canvas aria-label="Regenerated engine 3D inspection" tabindex="0"></canvas></div>
<script src="/assets/ngg/model.js"></script><script src="/assets/ngg/viewport.js"></script>
<script>var module={exports:{}};</script><script src="/assets/engine-redesign.js"></script>
<script>var compactResearchDecoder=module.exports.decodeResearchMesh;module=undefined;</script><script>
(async()=>{try{
const manifest=await(await fetch('/manifest.json')).json(),bytes=await(await fetch('/mesh.stl')).arrayBuffer();
const checksum=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
if(checksum!==manifest.artifacts['DISPLAY-ONLY-export.stl'])throw Error('Display SHA256 mismatch');
const decoded=compactResearchDecoder(bytes,manifest,manifest.recipe_sha256,manifest.source_commit_id);
if(!decoded.displayOnly)throw Error('Explicit display derivative required');
const canvas=document.querySelector('canvas'),viewer=new CosmosNGGViewport(canvas,()=>{},e=>{document.getElementById('status').textContent=e.message;});
CosmosNGGViewTools.mountTools(viewer,document.getElementById('cad'),{title:'Regenerated research model · display only'});
if(!await viewer.load(decoded.values,decoded.parts))throw Error('Native WebGL viewport failed');
viewer.setProjection('orthographic');viewer.orient('isometric');viewer.fit();window.compactViewer=viewer;
document.getElementById('basis').textContent='Component source '+manifest.source_commit_id+' · recipe '+manifest.recipe_sha256;
document.getElementById('status').textContent=decoded.parts.length+' metal groups · '+manifest.result.triangle_count.toLocaleString()+' display triangles · NOT QUALIFIED';
await fetch('/rendered',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pass:true,parts:decoded.parts.length,display_triangles:manifest.result.triangle_count,projection:'orthographic',orientation:'isometric'})});
}catch(e){document.getElementById('status').textContent=e.message;
await fetch('/rendered',{method:'POST',body:JSON.stringify({pass:false,error:String(e.message).slice(0,500)})});}})();
</script></html>"""


def launch(campaign, *, output=None, inspect_seconds=0, display_dir=None):
    import webview

    if type(inspect_seconds) is not int or not 0 <= inspect_seconds <= 45:
        raise ValueError("Bounded inspection interval 0..45 seconds required")
    if output is not None and (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
    ):
        raise ValueError("New absolute verification output required")
    directory = display_dir if display_dir is not None else campaign / "display"
    manifest_path = directory / "manifest.json"
    mesh = directory / "DISPLAY-ONLY-export.stl"
    if (
        manifest_path.stat().st_size > 262144
        or (campaign / "preflight.json").stat().st_size > 262144
    ):
        raise ValueError("Bounded source manifests required")
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    preflight = json.loads((campaign / "preflight.json").read_bytes())
    if mesh.stat().st_size > 10_000_084:
        raise ValueError("Bounded display mesh required")
    mesh_bytes = mesh.read_bytes()
    if (
        manifest["schema"] != "cosmos.compact-engine-display.v1"
        or manifest["recipe_sha256"] != preflight["recipe_sha256"]
        or manifest["source_commit_id"] != preflight["component_source_commit_id"]
        or sha256(mesh_bytes).hexdigest() != manifest["artifacts"][mesh.name]
    ):
        raise ValueError(
            "Display must match this campaign's exact source/recipe and bytes"
        )
    assets = Path(__file__).resolve().parents[1] / "gui/static"
    event, observed = threading.Event(), {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = unquote(urlsplit(self.path).path)
            if path == "/":
                data, content_type = PAGE.encode(), "text/html; charset=utf-8"
            elif path == "/manifest.json":
                data, content_type = manifest_raw, "application/json"
            elif path == "/mesh.stl":
                data, content_type = mesh_bytes, "application/octet-stream"
            elif path.startswith("/assets/"):
                asset_root = (
                    assets.parent / "assets"
                    if path.startswith("/assets/cad-icons/")
                    else assets
                )
                file = (asset_root / path[len("/assets/") :]).resolve()
                if (
                    not file.is_relative_to(asset_root)
                    or not file.is_file()
                    or file.stat().st_size > 32 * 1024**2
                ):
                    self.send_error(404)
                    return
                data, content_type = (
                    file.read_bytes(),
                    mimetypes.guess_type(file.name)[0] or "application/octet-stream",
                )
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/rendered" or not 0 < length <= 4096:
                self.send_error(400)
                return
            try:
                value = json.loads(self.rfile.read(length))
                if type(value) is not dict or type(value.get("pass")) is not bool:
                    raise ValueError("Render status required")
            except (ValueError, TypeError):
                self.send_error(400)
                return
            observed.update(value)
            event.set()
            self.send_response(204)
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    print("Read-only terminal-launched native viewer: " + url, flush=True)
    window = None

    def verified():
        if not event.wait(45):
            observed.update({"pass": False, "error": "Native render timed out"})
        if inspect_seconds:
            threading.Event().wait(inspect_seconds)
        observed.update(
            {
                "schema": "cosmos.compact-native-display-check.v1",
                "manifest_sha256": sha256(manifest_raw).hexdigest(),
                "app_installed": False,
                "owner_data_opened": False,
                "engineering_acceptance": "NOT_PERFORMED",
            }
        )
        with output.open("x") as stream:
            json.dump(observed, stream, indent=2, allow_nan=False)
        window.destroy()

    try:
        window = webview.create_window(
            "COSMOS · regenerated engine · research inspection",
            url,
            width=1440,
            height=1000,
        )
        webview.start(
            verified if output is not None else None, gui="cocoa", debug=False
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    if output is not None and not observed.get("pass"):
        raise ValueError("Native display verification failed; inspect its report")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--verification-output", type=Path)
    parser.add_argument("--inspect-seconds", type=int, default=0)
    parser.add_argument("--display-dir", type=Path)
    args = parser.parse_args()
    launch(
        args.campaign,
        output=args.verification_output,
        inspect_seconds=args.inspect_seconds,
        display_dir=args.display_dir,
    )


if __name__ == "__main__":
    main()
