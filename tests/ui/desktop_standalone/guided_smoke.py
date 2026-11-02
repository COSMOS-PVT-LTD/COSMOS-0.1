"""Actual Cocoa/WebKit guided flow, isolated roots, no production data/builds."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inspect-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("New evidence file required")
    if not 0 <= args.inspect_seconds <= 45:
        raise ValueError("Inspection interval must be0..45 seconds")
    import webview

    from gui.desktop_runtime import DesktopServer

    os.environ.update(COSMOS_NEW_SHELL="1", COSMOS_DURABLE_PROJECTS="1")
    isolated = Path(tempfile.mkdtemp(prefix="cosmos-guided-native-")).resolve()
    proof = {
        "schema": "cosmos.guided-native-smoke.v1",
        "isolated_root": str(isolated),
        "hardware_evidence": False,
    }
    failures = []
    with DesktopServer(isolated) as server:
        window = webview.create_window(
            "COSMOS Guided Design — isolated verification",
            server.url,
            width=1280,
            height=900,
        )

        def check(expression, seconds=25):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if window.evaluate_js(expression):
                    return
                time.sleep(0.1)
            raise AssertionError("Native condition timeout: " + expression)

        def driver():
            try:
                check("!!document.querySelector('#login-id')")
                window.evaluate_js(
                    "window.__login=null;fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({login_id:'cosmos-admin',password:'COSMOS-Dev-2026!'})}).then(async r=>window.__login={status:r.status,data:await r.json()})"
                )
                check("!!window.__login")
                assert window.evaluate_js("window.__login.status") == 200
                window.load_url(server.url + "/app/workbench/rocket-engine")
                check(
                    "!!document.querySelector('#guided-preview') && !!window.CosmosGuidedEngine"
                )
                check("!document.querySelector('#guided-brief fieldset').disabled")
                assert (
                    window.evaluate_js("document.body.dataset.engineMode") == "guided"
                )
                # Exercise real UI buttons/fields, not a direct calculation API.
                window.evaluate_js(
                    "document.querySelector('.guided-project button').click()"
                )
                check(
                    "!!window.CosmosGuidedEngine.readState().project && !!document.querySelector('#guided-brief details input') && !document.querySelector('#guided-brief fieldset').disabled"
                )
                window.evaluate_js(
                    "for(const [id,value] of Object.entries({'guided-thrust':'1.5','guided-pressure':'5','guided-duration':'5'})){let e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}));}document.querySelector('#guided-brief').requestSubmit()"
                )
                check(
                    "!!document.querySelector('#guided-calculate') && !document.querySelector('#guided-brief fieldset').disabled"
                )
                proof["review_hash"] = window.evaluate_js(
                    "window.CosmosGuidedEngine.readState().reviewHash"
                )
                assert len(proof["review_hash"]) == 64
                window.evaluate_js(
                    "document.querySelector('#guided-calculate').click()"
                )
                check("window.CosmosGuidedEngine.readState().state==='COMPLETED'", 40)
                check("!!document.querySelector('#guided-results .guided-metrics')")
                text = window.evaluate_js(
                    "document.querySelector('#guided-results').innerText"
                )
                assert "1,500" in text or "1500" in text, text
                assert "BLOCKED" in text and "Physical validation" in text
                if args.inspect_seconds:
                    window.evaluate_js(
                        "document.querySelector('#guided-brief').scrollIntoView({block:'start'})"
                    )
                    time.sleep(args.inspect_seconds)
                proof["completed_state"] = window.evaluate_js(
                    "window.CosmosGuidedEngine.readState()"
                )
                proof["results_text"] = text[:4000]
                expert = window.evaluate_js(
                    "document.querySelector('#guided-results a').href"
                )
                assert "engine_mode=expert" in expert
                window.load_url(expert)
                check("!!window.COSMOS?.rocketPresentation?.readContext().designId")
                assert (
                    window.evaluate_js("document.body.dataset.engineMode") == "expert"
                )
                proof["expert_design_id"] = window.evaluate_js(
                    "window.COSMOS.rocketPresentation.readContext().designId"
                )
                assert proof["expert_design_id"]
                check("document.getElementById('guided-thrust').value==='1.5'")
                window.evaluate_js(
                    "document.querySelector('#guided-mode-toggle').click()"
                )
                assert (
                    window.evaluate_js("document.body.dataset.engineMode") == "guided"
                )
                assert (
                    window.evaluate_js("document.getElementById('guided-thrust').value")
                    == "1.5"
                )
                # Return to saved guided history, without running a new job.
                project = proof["completed_state"]["project"]
                window.load_url(
                    server.url + "/app/workbench/rocket-engine?project=" + project
                )
                check("!!document.querySelector('#guided-history details')")
                proof["history_reopened"] = True
                proof["native_backend"] = window.gui.__name__
                proof["pass"] = True
                window.load_url(
                    server.url + "/app/workbench/rocket-engine?project=" + project
                )
            except Exception as error:  # noqa: BLE001 - preserve native boundary failures
                failures.append(str(error))
                proof.update({"pass": False, "error": str(error)})
                proof["visible_status"] = window.evaluate_js(
                    "document.querySelector('#guided-status')?.innerText"
                )
            finally:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x") as stream:
                    json.dump(proof, stream, indent=2)
                window.destroy()

        webview.start(driver, private_mode=True)
    assert not failures, failures
    print(
        "Native guided brief -> review -> supervised CEA -> saved design -> Expert Mode -> history PASS"
    )


if __name__ == "__main__":
    main()
