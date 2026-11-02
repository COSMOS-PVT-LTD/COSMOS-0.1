"""Real authenticated HTTP and export checks; scientific services stubbed explicitly."""
import hashlib
import json
import threading
import urllib.error
import urllib.request
from http import cookiejar

import pytest

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler, ThreadingHTTPServer
from tests.fixtures.knowledge_reports import CLAIM_ID, add_knowledge, report_services


@pytest.fixture
def server(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, knowledge_reports_enabled=True)
    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args): pass
    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    base = f"http://127.0.0.1:{http.server_port}"
    def login(login_id="cosmos-admin", profile="ADMIN", password="COSMOS-Dev-2026!"):
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
        client.open(urllib.request.Request(base+"/api/auth/login", json.dumps({"login_id": login_id, "login_profile": profile, "password": password}).encode(), {"Content-Type": "application/json"})).close()
        return client
    yield app, base, login()
    http.shutdown(); http.server_close(); thread.join()
    if app._knowledge_workspace is not None:
        app._knowledge_workspace.persistence.close()


def post(client, base, action, value, headers=None):
    req = urllib.request.Request(base+"/api/knowledge-reports/"+action, json.dumps(value).encode(), {"Content-Type": "application/json", "Origin": base, **(headers or {})})
    try:
        with client.open(req) as response: return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


def test_empty_context_legacy_access_and_no_science_activation(server):
    app, base, client = server
    value = json.load(client.open(base+"/api/knowledge-reports/context"))
    assert not value["knowledge"]["sources"] and not value["reports"]["report_ids"]
    assert app._ngg_workspace is app._simulation_workspace is app._comparison_workspace is None
    assert b"kr-workbench" in client.open(base+"/app/workbench/knowledge").read()
    assert b"mh-workspace-head" in client.open(base+"/app/workbench/knowledge?knowledge=legacy").read()
    assert b"kr-workbench" in client.open(base+"/app/workbench/reports").read()
    assert post(client, base, "production-handoff", {})[0] == 403


def test_default_off_and_invalid_flag_preserve_original_page(tmp_path, server):
    app, base, client = server; app.knowledge_reports_enabled = False
    assert b"mh-workspace-head" in client.open(base+"/app/workbench/knowledge").read()
    with pytest.raises(urllib.error.HTTPError) as caught: client.open(base+"/api/knowledge-reports/context")
    assert caught.value.code == 404 and app._reports_workspace is None
    assert not CosmosApplication(tmp_path/"default").knowledge_reports_enabled
    assert not CosmosApplication(tmp_path/"no-shell", new_shell=False, knowledge_reports_enabled=True).knowledge_reports_enabled


def test_source_to_claim_and_report_exports_with_exact_byte_headers(server):
    app, base, client = server; add_knowledge(app.knowledge_workspace())
    c, s, g, key = report_services(); app._comparison_workspace=c; app._simulation_workspace=s; app._ngg_workspace=g
    evidence = json.load(client.open(base+"/api/knowledge-reports/claims/"+CLAIM_ID))
    assert evidence["claim"]["source_navigation_status"] == "recorded-approved-source-and-review"
    status, value = post(client, base, "generate", {"title": "Synthetic HTTP report", "receipt_id": key, "claim_ids": [CLAIM_ID]})
    assert status == 200; report_id = value["report_id"]
    assert hashlib.sha256(value["canonical_json"].encode()).hexdigest() == report_id
    for kind in ("json", "md", "html", "package"):
        with client.open(base+"/api/knowledge-reports/reports/"+report_id+"/"+kind) as response:
            raw = response.read()
            assert response.headers["X-COSMOS-SHA256"] == hashlib.sha256(raw).hexdigest()
            assert "attachment" in response.headers["Content-Disposition"] and response.headers["X-Content-Type-Options"] == "nosniff"
    assert post(client, base, "review-intent", {"report_id": report_id, "note": "Synthetic test only"})[1]["independent_acceptance"] is False


@pytest.mark.parametrize("headers", [{"Origin": "https://evil.example"}, {"Host": "evil.example"}, {"Content-Type": "text/plain"}])
def test_transport_refused_before_service(server, headers):
    app, base, client = server
    assert post(client, base, "search", {"query": "", "offset": 0}, headers)[0] == 400
    assert app._reports_workspace is app._knowledge_workspace is None


@pytest.mark.parametrize("value", [{"query": "a", "offset": False}, {"query": "a", "offset": 0, "approved": True}, {"query": "a"}, {"query": "a"*257, "offset": 0}])
def test_strict_search_contract(server, value):
    _, base, client = server
    assert post(client, base, "search", value)[0] == 400


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER])
def test_read_only_roles_cannot_generate_or_publish(server, role):
    app, base, _ = server
    app.auth.register_user(login_id="p11-role", password="Synthetic-P11-password", display_name="Synthetic", designation="Test", employee_id="TEST", team="Test", role=role)
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    client.open(urllib.request.Request(base+"/api/auth/login", json.dumps({"login_id": "p11-role", "login_profile": "USER", "password": "Synthetic-P11-password"}).encode(), {"Content-Type": "application/json"})).close()
    assert post(client, base, "generate", {"title": "test", "receipt_id": "a"*64, "claim_ids": []})[0] == 403
    assert post(client, base, "production-handoff", {})[0] == 403
    assert app._reports_workspace is None


def test_unauthenticated_duplicate_oversized_and_path_requests(server):
    app, base, client = server
    with pytest.raises(urllib.error.HTTPError) as caught: urllib.request.urlopen(base+"/api/knowledge-reports/context")
    assert caught.value.code == 401
    for raw in (b'{"query":"a","query":"b","offset":0}', b'{"query":NaN,"offset":0}', b'[]'):
        with pytest.raises(urllib.error.HTTPError) as caught:
            client.open(urllib.request.Request(base+"/api/knowledge-reports/search", raw, {"Content-Type": "application/json", "Origin": base}))
        assert caught.value.code == 400
    assert post(client, base, "search", {"query": "x"*17000, "offset": 0})[0] == 400
    with pytest.raises(urllib.error.HTTPError): client.open(base+"/api/knowledge-reports/claims/..%2foutside")
    assert app._ngg_workspace is None
