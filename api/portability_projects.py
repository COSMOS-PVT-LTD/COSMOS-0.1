"""Explicit authenticated package preview/mapping; no posted filesystem paths."""
from __future__ import annotations

import base64
from typing import Any

from systems.projects.authority import AccessDenied, InvalidRecord, SchemaMismatch


def handle_import(api: Any, user: Any, action: str, body: dict[str, Any]) -> dict[str, Any]:
    from api.project_authority import _allowed, principal
    if api.portability is None:
        raise SchemaMismatch("Project portability requires explicit schema6 composition.")
    _allowed(body, {"package_base64"} if action == "import-preview" else {"package_base64", "confirmed_manifest_sha256", "user_mapping", "confirmed_memberships"})
    raw = base64.b64decode(body["package_base64"], validate=True)
    if action == "import-preview":
        return {"ok": True, "preview": api.portability.preview(raw)}
    if type(body["user_mapping"]) is not dict or len(body["user_mapping"]) > 1000 or any(type(k) is not str or type(v) is not str for k,v in body["user_mapping"].items()):
        raise InvalidRecord("Provide a bounded explicit source-to-active-user-ID mapping.")
    users = {}
    for old_id, new_id in body["user_mapping"].items():
        account = api.auth.get_user_by_id(new_id)
        if account is None or not account.active:
            raise AccessDenied("Every destination owner/member must be an exact active local account; credentials are never imported.")
        users[old_id] = principal(account)
    return {"ok": True, "import": api.portability.import_project(principal(user), raw, confirmed_manifest=body["confirmed_manifest_sha256"],
        users=users, confirmed_memberships=body["confirmed_memberships"])}
