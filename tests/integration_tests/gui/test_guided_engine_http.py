"""Same-origin authenticated HTTP, new guided assets and persisted exact sources."""

import json
import threading
import time
import urllib.error
import urllib.request
from http import cookiejar
from http.server import ThreadingHTTPServer

import pytest

from gui.server import CosmosApplication, CosmosApplicationHandler


@pytest.fixture
def server(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, durable_projects=True)
    handler = type(
        "GuidedTestHandler", (CosmosApplicationHandler,), {"application": app}
    )
    http = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    http.daemon_threads = True
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:" + str(http.server_port)
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
    )

    def request(path, body=None):
        r = urllib.request.Request(
            base + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        with opener.open(r, timeout=10) as response:
            return json.loads(response.read())

    request(
        "/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!"}
    )
    yield base, opener, request
    http.shutdown()
    http.server_close()
    app.close()


def test_actual_http_assets_auth_and_guided_workflow(server):
    base, opener, request = server
    from tests.unit_tests.systems_layer.test_guided_engine import engine_brief

    html = opener.open(base + "/app/workbench/rocket-engine").read().decode()
    assert 'src="/assets/guided-engine.js"' in html
    assert (
        "Expert Mode" in opener.open(base + "/assets/guided-engine.js").read().decode()
    )
    assert (
        "guided-grid" in opener.open(base + "/assets/guided-engine.css").read().decode()
    )
    project = request(
        "/api/projects",
        {
            "title": "HTTP guided software fixture",
            "mission": "not physical evidence",
            "operation_id": "project",
        },
    )["project"]["project_id"]
    path = "/api/projects/" + project + "/guided-engine"
    with pytest.raises(urllib.error.HTTPError) as denied:
        urllib.request.urlopen(base + path + "/capabilities")
    assert denied.value.code == 401
    spec = {
        "brief": engine_brief(),
        "overrides": {"mixture_ratio": {"value": 2.63, "unit": "1"}},
        "profile_id": "methalox-pf-preliminary-v1",
    }
    r = request(path + "/preview", spec)
    source = request(
        path,
        {
            **spec,
            "review_hash": r["resolution"]["review_hash"],
            "operation_id": "accept",
        },
    )
    source_path = path + "/" + source["authority"]["object_id"]
    job = request(
        source_path + "/jobs",
        {"expected": source["authority"]["head"], "operation_id": "calculate"},
    )
    deadline = time.monotonic() + 15
    while (
        job["state"] not in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}
        and time.monotonic() < deadline
    ):
        time.sleep(0.05)
        job = request(source_path + "/jobs/" + job["job_id"])
    assert job["state"] == "COMPLETED", job
    assert job["result_current"] and not job["result"]["report"]["engine_complete"]
    assert len(request(path)["inputs"]) == 1
