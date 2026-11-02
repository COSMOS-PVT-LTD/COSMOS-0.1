#!/usr/bin/env python3
"""Capture the user's current case read-only; test a separate managed copy."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from hashlib import sha256
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.project_authority import principal
from api.propulsion_workflow import run_design_workflow
from gui.server import CosmosApplication
from systems.projects.models import PropulsionDesign


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-api", default="http://127.0.0.1:8878")
    args = parser.parse_args()
    if urlparse(args.source_api).hostname != "127.0.0.1" or urlparse(args.source_api).scheme != "http":
        raise ValueError("This tool only authenticates to the explicit local development source")
    root = args.output.absolute()
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    client = build_opener(HTTPCookieProcessor(CookieJar()))
    client.open(Request(args.source_api+"/api/auth/login", data=json.dumps({
        "login_id":"cosmos-admin", "password":"COSMOS-Dev-2026!", "login_profile":"ADMIN"}).encode(),
        headers={"Content-Type":"application/json"}), timeout=15).close()
    source_path = "/api/projects/01cd79e6-3923-4eca-ae1f-544cc30d8901/designs/6524df5d-46f9-5b74-b214-8f5ada56acf6"
    original = json.load(client.open(args.source_api+source_path, timeout=15))
    save(root/"original-envelope.json", original)
    source_hash = sha256(original["source_canonical_json"].encode()).hexdigest()
    app = CosmosApplication(root/"app-data", new_shell=True, durable_projects=True,
        ngg_enabled=True, ngg_runtime=ROOT/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-v3.json")
    try:
        api = app.project_api
        actor = principal(next(user for user in app.auth.list_users() if user.login_id == "cosmos-admin"))
        project = api.repository.create_project(actor, title="Engine goal repair · preserved methalox copy",
            mission="Normal recalculation qualification, not user approval or hardware evidence", operation_id="goal-project")
        source = api.service.create(actor, project.project_id,
            design=PropulsionDesign.from_canonical_dict(original["design"]), operation_id="preserved-source", command_hash=source_hash)
        calculated = api.service.calculate(actor, project.project_id, source.object_id, expected=source.head,
            operation_id="one-captured-analysis", command_hash=sha256(b"engine-goal-configured-analysis-v1").hexdigest(),
            parameters={"action":"run/analysis", "phase3_inputs":{}, "phase4_inputs":{}}, evaluate=run_design_workflow)
        saved = api.envelope(actor, calculated)
        save(root/"analysis-envelope.json", saved)
        save(root/"identities.json", {"project_id":project.project_id, "design_id":source.object_id,
            "source_commit_id":source.commit_id, "result_commit_id":calculated.commit_id,
            "result_head":asdict(calculated.head), "original_commit_id":original["authority"]["commit_id"]})
        design = saved["design"]
        assert design["workflow"]["results"]["performance"]["status"] == "CURRENT"
        assert design["workflow"]["results"]["design_review"]["outputs"]["review_verdict"] == "INCOMPLETE"
        assert not any(value["status"] == "FAILED" for value in design["workflow"]["results"].values())
        latest = json.load(client.open(args.source_api+source_path, timeout=15))
        save(root/"qualification.json", {"normal_analysis_ready_stages_pass":True, "original_case_unchanged_at_check":latest["source_canonical_json"]==original["source_canonical_json"],
            "physical_validation":"NOT_PERFORMED", "goal_complete":False, "R08":"HOLD_UNTIL_USER_ACCEPTANCE"})
        print(json.dumps({"isolated_project":project.project_id, "isolated_design":source.object_id,
            "original_unchanged":latest["source_canonical_json"]==original["source_canonical_json"],
            "stages":{key:value["status"] for key,value in design["workflow"]["results"].items()}}))
    finally:
        app.close()


if __name__ == "__main__":
    main()
