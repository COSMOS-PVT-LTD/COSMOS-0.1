#!/usr/bin/env bash
# COSMOS PVT LTD. All Rights Reserved.
# Read-only by default. An existing protection is never overwritten implicitly.
set -euo pipefail
task_repo="COSMOS-PVT-LTD/COSMOS-0.1"
task_root="$(git rev-parse --show-toplevel)"
task_mode="${1:---inspect}"
task_sha="$(gh api "repos/$task_repo/branches/main" --jq '.commit.sha')"
gh api "repos/$task_repo/branches/main" --jq '{name,sha:.commit.sha,protected}'
gh api "repos/$task_repo/rulesets"
if [[ "$task_mode" == "--apply" ]]; then
    [[ "${2:-}" == "$task_sha" ]] || { echo 'Expected main SHA does not match; inspect/reconcile first.' >&2; exit 1; }
    task_protected="$(gh api "repos/$task_repo/branches/main" --jq '.protected')"
    [[ "$task_protected" == "false" ]] || { echo 'Protection already exists; review its diff manually.' >&2; exit 1; }
    [[ "$(gh repo view "$task_repo" --json viewerPermission --jq '.viewerPermission')" == "ADMIN" ]] || { echo 'Repository admin permission required.' >&2; exit 1; }
    gh api --method PUT "repos/$task_repo/branches/main/protection" --input "$task_root/.github/governance/main-protection.json"
elif [[ "$task_mode" != "--inspect" ]]; then
    echo 'Usage: apply_repository_governance.sh [--inspect | --apply EXPECTED_MAIN_SHA]' >&2
    exit 2
fi
gh api "repos/$task_repo/branches/main/protection"
