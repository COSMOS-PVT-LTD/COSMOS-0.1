"""Governance payload remains solo-safe and templates cover scientific review."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_protection_is_blocking_without_impossible_review() -> None:
    policy = json.loads((ROOT / ".github/governance/main-protection.json").read_text())
    assert policy["enforce_admins"] is True
    assert policy["required_status_checks"]["strict"] is True
    assert "contexts" not in policy["required_status_checks"]
    assert {c["context"] for c in policy["required_status_checks"]["checks"]} == {
        "Test (Python 3.11)", "Test (Python 3.12)", "Lint and type check",
    }
    assert all(c["app_id"] == 15368 for c in policy["required_status_checks"]["checks"])
    assert policy["required_pull_request_reviews"]["required_approving_review_count"] == 0
    assert policy["required_pull_request_reviews"]["require_last_push_approval"] is False
    assert policy["required_pull_request_reviews"]["require_code_owner_reviews"] is False
    assert policy["allow_force_pushes"] is False
    assert policy["allow_deletions"] is False
    assert policy["lock_branch"] is False
    assert policy["required_conversation_resolution"] is True


def test_templates_and_real_owner_exist() -> None:
    owners = (ROOT / ".github/CODEOWNERS").read_text()
    assert "* @trishul4kumar-ui" in owners
    assert "[COSMOS-GITHUB-TEAM]" not in owners
    template = (ROOT / ".github/PULL_REQUEST_TEMPLATE.md").read_text()
    for term in ("numerical algorithm", "physical model", "validity range", "Negative/failure",
                 "pytest", "Ruff", "Mypy", "certification", "approval"):
        assert term in template
    assert (ROOT / ".github/ISSUE_TEMPLATE/scientific_defect.md").is_file()
    release = (ROOT / ".github/workflows/release.yml").read_text()
    assert "workflow_dispatch" in release
    assert "gh release create" not in release
    assert "git merge-base --is-ancestor" in release
