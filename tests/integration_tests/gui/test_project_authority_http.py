"""R05.2 real authenticated HTTP, restart and stale-completion evidence."""

from __future__ import annotations

import json
import sqlite3
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http import cookiejar
from http.server import ThreadingHTTPServer
from uuid import uuid4

import pytest

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler
from systems.persistence.design_store import DesignStore
from systems.projects.authority import AccessDenied, SchemaMismatch, StoreUnavailable
from systems.projects.models import PropulsionDesign
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def request(client, base, path, data=None, expected=200):
    payload = json.dumps(data).encode() if data is not None else None
    try:
        with client.open(
            urllib.request.Request(
                base + path, data=payload, headers={"Content-Type": "application/json"}
            ),
            timeout=15,
        ) as response:
            code, body = response.status, json.load(response)
    except urllib.error.HTTPError as error:
        code, body = error.code, json.load(error)
    assert code == expected, body
    return body


def client_for(
    base, login="cosmos-admin", password="COSMOS-Dev-2026!", profile="ADMIN"
):
    client = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
    )
    request(
        client,
        base,
        "/api/auth/login",
        {"login_id": login, "password": password, "login_profile": profile},
    )
    return client


@contextmanager
def running(root, *, enabled=True):
    app = CosmosApplication(root, new_shell=True, durable_projects=enabled)

    class Handler(CosmosApplicationHandler):
        application = app

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        yield app, base, client_for(base)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        app.close()


@pytest.fixture
def server(tmp_path):
    with running(tmp_path / "state") as value:
        yield value


def new_project(base, client, title="Synthetic R05.2 project — not hardware evidence"):
    return request(
        client,
        base,
        "/api/projects",
        {
            "title": title,
            "mission": "Software verification",
            "operation_id": str(uuid4()),
        },
    )["project"]


def new_design(base, client, project):
    return request(
        client,
        base,
        f"/api/projects/{project['project_id']}/designs",
        {"name": "Synthetic propulsion", "operation_id": str(uuid4())},
    )


def command(saved, **kwargs):
    return {
        "expected": saved["authority"]["head"],
        "operation_id": str(uuid4()),
        **kwargs,
    }


def route(project, saved):
    return (
        f"/api/projects/{project['project_id']}/designs/{saved['design']['design_id']}"
    )


def configured(base, client, project, design):
    return request(
        client,
        base,
        route(project, design) + "/save",
        command(
            design,
            requirements={
                "target_chamber_pressure": {"magnitude": 50, "unit_symbol": "bar"},
                "target_thrust": {"magnitude": 1.5, "unit_symbol": "kN"},
                "mixture_ratio": 2.6,
                "expansion_ratio": 12,
                "ambient_pressure": {"magnitude": 101325, "unit_symbol": "Pa"},
            },
            propellants={"oxidizer_id": "LOX", "fuel_id": "RP-1", "mixture_ratio": 2.6},
        ),
    )


ASSUMED = {
    "chamber_temperature_k": 3500,
    "gamma": 1.22,
    "molecular_weight_kg_per_mol": 0.022,
    "throat_area_m2": 0.0001,
    "expansion_ratio": 12,
    "thermochemistry_configuration": {"mode": "assumed"},
}


def test_default_off_does_not_initialize_authority_or_change_legacy(tmp_path):
    with running(tmp_path / "default", enabled=False) as (app, base, client):
        assert not (app.root / "engineering_state").exists()
        request(client, base, "/api/projects", expected=404)
        legacy = request(
            client, base, "/api/propulsion/designs", {"name": "Unmigrated legacy"}
        )
        assert (
            app.design_store.root / (legacy["design"]["design_id"] + ".json")
        ).is_file()


def test_managed_create_edit_snapshot_history_and_conflict(server):
    app, base, client = server
    project = new_project(base, client)
    first = new_design(base, client, project)
    url = route(project, first)
    assert (
        project["owner_user_id"]
        == app.auth.get_user_by_id(project["owner_user_id"]).user_id
    )
    assert first["authority"]["input_revision"] == 0
    assert not list(app.design_store.root.glob("*.json"))
    body = command(first, name="Changed")
    saved = request(client, base, url + "/save", body)
    assert saved["design"]["revision"] == 1
    assert saved["authority"]["head"]["version"] == 2
    assert request(client, base, url + "/save", body) == saved
    stale = request(
        client, base, url + "/save", command(first, name="Lost overwrite"), expected=409
    )
    assert stale["error"]["current_head"] == saved["authority"]["head"]
    historical = request(
        client, base, url + "?commit=" + first["authority"]["commit_id"]
    )
    assert historical["design"]["name"] == "Synthetic propulsion"
    assert historical["authority"]["is_current"] is False
    assert historical["source_canonical_json"] == first["source_canonical_json"]
    assert len(request(client, base, url + "/history")["commits"]) == 2


def test_actual_phase3_same_input_distinct_results_and_durable_runtime_inputs(server):
    app, base, client = server
    project = new_project(base, client)
    design = configured(base, client, project, new_design(base, client, project))
    url = route(project, design)
    body = command(design, **ASSUMED)
    first = request(client, base, url + "/run/phase3", body)
    assert first["execution_ok"] is True
    assert first["stages"]["performance"]["status"] == "CURRENT"
    assert first["authority"]["input_commit_id"]
    assert (
        request(client, base, url + "/run/phase3", body)["authority"]["commit_id"]
        == first["authority"]["commit_id"]
    )
    second = request(client, base, url + "/run/phase3", command(first, **ASSUMED))
    assert second["design"]["revision"] == first["design"]["revision"]
    assert (
        second["stages"]["performance"]["result_id"]
        != first["stages"]["performance"]["result_id"]
    )
    assert second["authority"]["commit_id"] != first["authority"]["commit_id"]
    old = request(
        client,
        base,
        url + "/stages/performance?commit=" + first["authority"]["commit_id"],
    )
    assert old["displayable_as_current"] is False
    assert old["result"]["status"] == "CURRENT"  # Original receipt is not mutated.
    with sqlite3.connect(app._project_authority.repository.path) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM objects WHERE domain='propulsion-inputs'"
            ).fetchone()[0]
            == 2
        )


def test_managed_phase4_and_phase6_keep_existing_preliminary_science_contract(server):
    _app, base, client = server
    project = new_project(base, client)
    saved = configured(base, client, project, new_design(base, client, project))
    url = route(project, saved)
    phase3 = request(client, base, url + "/run/phase3", command(saved, **ASSUMED))
    phase4 = request(
        client,
        base,
        url + "/run/phase4",
        command(
            phase3,
            characteristic_length_m=1.0,
            contraction_ratio=2.5,
            wall_thickness_m=0.0006,
            material_id="stainless_304",
            external_pressure_pa=101325,
            material_temperature_k=300,
            viscosity_pa_s=8e-5,
            conductivity_w_m_k=0.3,
            cp_j_kg_k=2500,
            wall_temperature_k=800,
        ),
    )
    assert phase4["execution_ok"] is True
    assert phase4["stages"]["nozzle"]["status"] == "CURRENT"
    phase6 = request(client, base, url + "/run/phase6", command(phase4))
    assert phase6["execution_ok"] is True
    assert phase6["workflow_complete"] is False
    assert phase6["validation_level"] == "NOT_CLAIMED"
    assert phase6["stages"]["design_review"]["outputs"]["review_verdict"] == "INCOMPLETE"
    assert phase6["authority"]["source_commit_id"] == phase4["authority"]["commit_id"]
    reopened = request(client, base, url)
    assert reopened["authority"]["commit_id"] == phase6["authority"]["commit_id"]
    assert reopened["design"] == phase6["design"]


def test_restart_and_flag_off_keep_scoped_reads_and_legacy_guard(tmp_path):
    root = tmp_path / "restart"
    with running(root) as (_, base, client):
        project = new_project(base, client)
        first = new_design(base, client, project)
        url = route(project, first)
        saved = request(
            client, base, url + "/save", command(first, name="Retained after restart")
        )
    with running(root, enabled=False) as (app, base, client):
        loaded = request(client, base, url)
        assert loaded["source_canonical_json"] == saved["source_canonical_json"]
        request(
            client,
            base,
            url + "/save",
            command(saved, name="Flag-off write"),
            expected=403,
        )
        legacy = "/api/propulsion/designs/" + first["design"]["design_id"]
        request(client, base, legacy, expected=409)
        request(client, base, legacy + "/save", {"name": "Bypass"}, expected=409)
        with pytest.raises(AccessDenied):
            DesignStore(app.design_store.root).save(
                PropulsionDesign(
                    name="Denied bypass", design_id=first["design"]["design_id"]
                )
            )
        assert request(client, base, "/api/propulsion/designs")["designs"] == []


def test_cross_user_denies_owner_membership_and_read_only_roles(server):
    app, base, owner = server
    project = new_project(base, owner)
    design = new_design(base, owner, project)
    for name, role in (("other", UserRole.ENGINEER), ("viewer", UserRole.VIEWER)):
        user = app.auth.register_user(
            login_id=name,
            display_name=name,
            password="Synthetic-Test-Password!",
            designation="Test",
            employee_id="TEST-" + name,
            team="QA",
            role=role,
        )
        member = client_for(base, name, "Synthetic-Test-Password!", "USER")
        request(member, base, route(project, design), expected=403)
        assert request(member, base, "/api/projects")["projects"] == []
        project = request(
            owner,
            base,
            f"/api/projects/{project['project_id']}/members",
            {
                "user_id": user.user_id,
                "capability": "VIEWER",
                "expected": project["head"],
                "operation_id": str(uuid4()),
            },
        )["project"]
        request(member, base, route(project, design))
        request(
            member,
            base,
            route(project, design) + "/save",
            command(design, name="Denied"),
            expected=403,
        )
        request(
            member,
            base,
            f"/api/projects/{project['project_id']}/members",
            {
                "user_id": user.user_id,
                "capability": "EDITOR",
                "expected": project["head"],
                "operation_id": str(uuid4()),
            },
            expected=403,
        )


def test_historical_activation_and_branch_never_promote_old_current_results(server):
    _, base, client = server
    project = new_project(base, client)
    design = configured(base, client, project, new_design(base, client, project))
    url = route(project, design)
    calculated = request(client, base, url + "/run/phase3", command(design, **ASSUMED))
    edited = request(
        client, base, url + "/save", command(calculated, name="Newer inputs")
    )
    activated = request(
        client,
        base,
        url + "/activate",
        command(edited, source_commit_id=calculated["authority"]["commit_id"]),
    )
    assert activated["design"]["revision"] > edited["design"]["revision"]
    assert (
        activated["design"]["workflow"]["results"]["performance"]["status"] == "STALE"
    )
    branched = request(
        client,
        base,
        url + "/branch",
        command(
            activated,
            source_commit_id=calculated["authority"]["commit_id"],
            name="New identity",
        ),
    )
    assert branched["design"]["design_id"] != design["design"]["design_id"]
    assert branched["design"]["workflow"]["results"]["performance"]["status"] == "STALE"
    original = request(
        client, base, url + "?commit=" + calculated["authority"]["commit_id"]
    )
    assert (
        original["design"]["workflow"]["results"]["performance"]["status"] == "CURRENT"
    )


def test_late_actual_calculation_is_retained_without_overwriting_newer_save(
    server, monkeypatch
):
    import api.project_authority as boundary

    _app, base, client = server
    project = new_project(base, client)
    design = configured(base, client, project, new_design(base, client, project))
    url = route(project, design)
    entered, release = threading.Event(), threading.Event()
    original = boundary.run_phase3

    def slow(candidate, **kwargs):
        entered.set()
        assert release.wait(8)
        return original(candidate, **kwargs)

    # Preserve the actual supported parameter signature used by the API whitelist.
    import functools

    functools.update_wrapper(slow, original)
    monkeypatch.setattr(boundary, "run_phase3", slow)
    separate = client_for(base)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            request, separate, base, url + "/run/phase3", command(design, **ASSUMED)
        )
        assert entered.wait(5)
        try:
            newer = request(
                client,
                base,
                url + "/save",
                command(design, name="Edit while solver running"),
            )
        finally:
            release.set()
        late = future.result(timeout=10)
    assert late["authority"]["selected_at_commit"] is False
    assert late["authority"]["is_current"] is False
    current = request(client, base, url)
    assert current["authority"]["commit_id"] == newer["authority"]["commit_id"]
    assert current["design"]["name"] == "Edit while solver running"
    assert (
        request(client, base, url + "?commit=" + late["authority"]["commit_id"])[
            "design"
        ]["workflow"]["results"]["performance"]["status"]
        == "CURRENT"
    )


def test_missing_database_cannot_reset_or_fall_back(tmp_path):
    root = tmp_path / "missing"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        new_design(base, client, project)
        path = app._project_authority.repository.path
    moved = path.with_suffix(".preserved")
    path.rename(moved)
    with pytest.raises(StoreUnavailable):
        CosmosApplication(root, durable_projects=False)
    assert not path.exists()
    assert moved.exists()


@pytest.mark.parametrize(
    "extra",
    [
        {"owner_user_id": "USR-forged"},
        {"role": "ADMIN"},
        {"design": {"status": "CURRENT"}},
    ],
)
def test_posted_authority_fields_are_refused(server, extra):
    _, base, client = server
    project = new_project(base, client)
    request(
        client,
        base,
        f"/api/projects/{project['project_id']}/designs",
        {"name": "Do not trust client identity", "operation_id": str(uuid4()), **extra},
        expected=400,
    )


def test_authentication_and_coordinator_exclusion(server):
    app, base, _client = server
    anonymous = urllib.request.build_opener()
    request(anonymous, base, "/api/projects", expected=401)
    with pytest.raises(StoreUnavailable, match="coordinator"):
        CosmosApplication(app.root, durable_projects=True)


def test_foundation_v1_is_readable_but_not_implicitly_upgraded(tmp_path):
    from infrastructure.persistence.schema import APPLICATION_ID, SCHEMA_V1
    from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository

    root = tmp_path / "v1"
    root.mkdir(mode=0o700)
    path = root / "metadata.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            SCHEMA_V1
            + f"PRAGMA user_version=1; PRAGMA application_id={APPLICATION_ID};"
        )
    path.chmod(0o600)
    original = path.read_bytes()
    repository = SQLiteProjectRepository(root)
    assert repository.schema_version == 1
    assert path.read_bytes() == original
    from systems.persistence.project_repository import RecordPayload
    from systems.projects.authority import Head, Principal

    actor = Principal("USR-owner", "ENGINEER")
    project = repository.create_project(
        actor, title="Old foundation", operation_id="create"
    )
    with pytest.raises(SchemaMismatch):
        repository.save_snapshot(
            actor,
            project.project_id,
            domain="propulsion",
            object_id="design-1",
            input_revision=0,
            payload=RecordPayload(b"{}", "test.v1"),
            expected=Head.absent(),
            operation_id="new-command",
            purpose="create",
        )


def test_project_api_rejects_cross_origin_and_non_json_writes(server):
    _, base, client = server
    for headers in (
        {"Content-Type": "text/plain"},
        {"Content-Type": "application/json", "Origin": "https://not-cosmos.invalid"},
    ):
        raw = urllib.request.Request(
            base + "/api/projects",
            data=b'{"title":"forged","operation_id":"unsafe"}',
            headers=headers,
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            client.open(raw)
        assert error.value.code == 403
    assert request(client, base, "/api/projects")["projects"] == []


def test_scoped_reads_are_not_cacheable_between_sessions(server):
    _, base, client = server
    with client.open(base + "/api/projects") as response:
        assert response.headers["Cache-Control"] == "no-store"
        assert "Cookie" in response.headers["Vary"]


def test_wrong_hash_and_reused_command_id_never_overwrite(server):
    _, base, client = server
    project = new_project(base, client)
    first = new_design(base, client, project)
    url = route(project, first)
    stale = command(first, name="Wrong hash")
    stale["expected"] = {**stale["expected"], "content_hash": "0" * 64}
    request(client, base, url + "/save", stale, expected=409)
    body = command(first, name="Once")
    saved = request(client, base, url + "/save", body)
    request(
        client, base, url + "/save", {**body, "name": "Changed command"}, expected=409
    )
    assert (
        request(client, base, url)["authority"]["commit_id"]
        == saved["authority"]["commit_id"]
    )


def test_every_legacy_managed_subroute_is_guarded_even_with_a_json_copy(server):
    app, base, client = server
    project = new_project(base, client)
    design = new_design(base, client, project)
    design_id = design["design"]["design_id"]
    # Fault fixture: an old/global JSON duplicate must never bypass membership/CAS.
    (app.design_store.root / (design_id + ".json")).write_text(
        design["source_canonical_json"]
    )
    legacy = "/api/propulsion/designs/" + design_id
    for suffix in ("", "/workflow", "/export", "/stages/performance"):
        request(client, base, legacy + suffix, expected=409)
    for suffix in (
        "/clone",
        "/save",
        "/requirements",
        "/cycle",
        "/propellants",
        "/run/phase3",
        "/run/phase4",
        "/run/phase6",
        "/run/subsystems",
    ):
        request(client, base, legacy + suffix, {}, expected=409)
    assert request(client, base, "/api/propulsion/designs")["designs"] == []


def test_archive_and_tombstone_are_recoverable_and_block_new_calculations(server):
    _, base, client = server
    project = new_project(base, client)
    design = new_design(base, client, project)
    path = "/api/projects/" + project["project_id"]
    archived = request(
        client,
        base,
        path,
        {
            "lifecycle": "ARCHIVED",
            "expected": project["head"],
            "operation_id": str(uuid4()),
        },
    )["project"]
    request(
        client,
        base,
        route(project, design) + "/run/phase3",
        command(design, **ASSUMED),
        expected=403,
    )
    request(
        client,
        base,
        path,
        {
            "lifecycle": "DELETED",
            "expected": archived["head"],
            "operation_id": str(uuid4()),
        },
        expected=400,
    )
    deleted = request(
        client,
        base,
        path,
        {
            "lifecycle": "DELETED",
            "confirmation_project_id": project["project_id"],
            "expected": archived["head"],
            "operation_id": str(uuid4()),
        },
    )["project"]
    restored = request(
        client,
        base,
        path,
        {
            "lifecycle": "ACTIVE",
            "expected": deleted["head"],
            "operation_id": str(uuid4()),
        },
    )["project"]
    assert restored["lifecycle"] == "ACTIVE"
    assert (
        request(client, base, route(project, design))["source_canonical_json"]
        == design["source_canonical_json"]
    )


def test_cross_project_commit_cannot_be_activated_or_read_by_hash_substitution(server):
    _, base, client = server
    a, b = new_project(base, client), new_project(base, client)
    first, other = new_design(base, client, a), new_design(base, client, b)
    request(
        client,
        base,
        route(b, other) + "?commit=" + first["authority"]["commit_id"],
        expected=404,
    )
    request(
        client,
        base,
        route(b, other) + "/activate",
        command(other, source_commit_id=first["authority"]["commit_id"]),
        expected=404,
    )


def test_response_checksum_failure_is_unavailable_not_a_substituted_latest_result(
    server,
):
    from systems.projects.authority import IntegrityFailure

    app, base, client = server
    project = new_project(base, client)
    design = configured(base, client, project, new_design(base, client, project))
    computed = request(
        client, base, route(project, design) + "/run/phase3", command(design, **ASSUMED)
    )
    repository = app._project_authority.repository
    with sqlite3.connect(repository.path) as connection:
        trigger = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name='immutable_commit_contexts_update'"
        ).fetchone()[0]
        connection.execute("DROP TRIGGER immutable_commit_contexts_update")
        raw = connection.execute(
            "SELECT response_json FROM commit_contexts WHERE commit_id=?",
            (computed["authority"]["commit_id"],),
        ).fetchone()[0]
        changed = json.loads(raw)
        changed["utf8"] = '{"ok":true,"forged":123}'
        connection.execute(
            "UPDATE commit_contexts SET response_json=? WHERE commit_id=?",
            (json.dumps(changed), computed["authority"]["commit_id"]),
        )
        connection.execute(trigger)
    request(client, base, route(project, design), expected=503)
    from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository

    with pytest.raises(IntegrityFailure, match="checksum"):
        SQLiteProjectRepository(repository.files.root)
