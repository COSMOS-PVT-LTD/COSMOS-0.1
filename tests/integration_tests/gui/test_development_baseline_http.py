"""Actual HTTP selection/CAS/rollback and source preservation; no native release."""

from dataclasses import asdict, replace
from uuid import uuid4

import pytest

from systems.geometry.development_baseline import DevelopmentBaselines
from systems.geometry.engine_redesign_authority import Redesigns
from systems.projects.authority import AccessDenied, Head
from tests.integration_tests.gui.test_engine_redesign_http import (
    compact_source,
    seed_and_command,
)
from tests.integration_tests.gui.test_project_authority_http import request, running


def setup(app, base, client):
    root, source, physics, actor = compact_source(app, base, client)
    _, command = seed_and_command(client, base, root, source)
    candidate = request(client, base, root + "/engine-redesign", command)
    path = root + "/engine-redesign/active-baseline"
    select = {
        "candidate_commit_id": candidate["authority"]["commit_id"],
        "expected_candidate": candidate["authority"]["head"],
        "expected": asdict(Head.absent()),
        "operation_id": str(uuid4()),
        "reason": "Preliminary CAD selection, not engineering approval",
    }
    return root, path, source, physics, actor, candidate, command, select


def test_exact_selection_replay_history_rollback_and_restart(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        _root, path, source, physics, actor, candidate, _, select = setup(
            app, base, client
        )
        assert request(client, base, path)["baseline"] is None
        assert request(client, base, path + "/history")["baselines"] == []
        installed = request(client, base, path, select)
        chosen = installed["baseline"]
        assert chosen["upstream_current"] is True
        assert (
            chosen["record"]["selection"]["commit_id"]
            == candidate["authority"]["commit_id"]
        )
        assert chosen["record"]["previous_selection"]["commit_id"] == source.commit_id
        assert chosen["record"]["engineering_acceptance"] == "NOT_PERFORMED"
        assert chosen["record"]["r08"] == "ON_HOLD"
        assert (
            request(client, base, path, select)["baseline"]["authority"]
            == chosen["authority"]
        )
        request(
            client, base, path, {**select, "operation_id": str(uuid4())}, expected=409
        )
        undo = {
            "expected": installed["expected"],
            "operation_id": str(uuid4()),
            "reason": "Restore preceding retained development source",
        }
        restored = request(client, base, path + "/rollback", undo)
        assert (
            restored["baseline"]["record"]["selection"]["kind"] == "RETAINED_COMPONENT"
        )
        assert (
            restored["baseline"]["record"]["selection"]["commit_id"] == source.commit_id
        )
        assert (
            request(client, base, path + "/rollback", undo)["baseline"]["authority"]
            == restored["baseline"]["authority"]
        )
        installed = request(
            client,
            base,
            path,
            {**select, "expected": restored["expected"], "operation_id": str(uuid4())},
        )
        assert len(request(client, base, path + "/history")["baselines"]) == 3
        repo = app.project_api.repository
        assert (
            repo.get_snapshot(
                actor,
                source.project_id,
                domain=source.domain,
                object_id=source.object_id,
            ).head
            == source.head
        )
        assert (
            repo.get_snapshot(
                actor,
                physics.project_id,
                domain=physics.domain,
                object_id=physics.object_id,
            ).head
            == physics.head
        )
    with running(tmp_path / "state") as (_, base, client):
        assert (
            request(client, base, path)["baseline"]["authority"]
            == installed["baseline"]["authority"]
        )
        assert request(client, base, path)["baseline"]["upstream_current"] is True


def test_newer_candidate_invalidates_selection_without_following_it(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        root, path, _, _, _, candidate, command, select = setup(app, base, client)
        installed = request(client, base, path, select)
        command.update(
            expected=candidate["authority"]["head"], operation_id=str(uuid4())
        )
        command["specification"]["stations"][12]["depth"]["value"] *= 0.8
        updated = request(
            client,
            base,
            root + "/engine-redesign/" + candidate["authority"]["object_id"],
            command,
        )
        stale = request(client, base, path)["baseline"]
        assert stale["upstream_current"] is False
        assert (
            stale["record"]["selection"]["commit_id"]
            == candidate["authority"]["commit_id"]
        )
        request(
            client,
            base,
            path,
            {**select, "expected": installed["expected"], "operation_id": str(uuid4())},
            expected=400,
        )
        reconciled = request(
            client,
            base,
            path,
            {
                **select,
                "expected": installed["expected"],
                "operation_id": str(uuid4()),
                "candidate_commit_id": updated["authority"]["commit_id"],
                "expected_candidate": updated["authority"]["head"],
            },
        )
        assert reconciled["baseline"]["upstream_current"] is True


def test_denies_qualification_overrides_foreign_sources_and_readonly_writes(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        _root, path, _, _, actor, _, _, select = setup(app, base, client)
        request(
            client,
            base,
            path,
            {**select, "engineering_acceptance": "ACCEPTED"},
            expected=400,
        )
        request(client, base, path + "?commit=override", select, expected=400)
        request(client, base, path + "/purge", select, expected=404)
        other = request(
            client,
            base,
            "/api/projects",
            {"title": "Foreign test project", "operation_id": str(uuid4())},
        )["project"]
        request(
            client,
            base,
            "/api/projects/" + other["project_id"] + "/engine-redesign/active-baseline",
            select,
            expected=404,
        )
        service = DevelopmentBaselines(Redesigns(app.project_api.components))
        readonly = replace(actor, global_role="VIEWER")
        with pytest.raises(AccessDenied):
            service.activate(
                readonly,
                actor.user_id,
                candidate_commit_id=select["candidate_commit_id"],
                expected_candidate=Head(**select["expected_candidate"]),
                expected=Head.absent(),
                operation_id="denied",
                command_hash="d" * 64,
                reason="Forbidden",
            )
        assert request(client, base, path)["baseline"] is None
