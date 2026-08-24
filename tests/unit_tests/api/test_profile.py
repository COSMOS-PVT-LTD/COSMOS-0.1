"""Profile service tests."""

from __future__ import annotations

from pathlib import Path

from api.authentication import AuthService, UserRole
from api.profile import ProfileService


def test_update_profile_and_photo(tmp_path: Path) -> None:
    auth = AuthService(tmp_path)
    auth.register_user(
        login_id="engineer-1",
        password="Secret-123!",
        display_name="Engineer One",
        designation="Propulsion Engineer",
        employee_id="EMP-100",
        team="Rocket Engine",
        role=UserRole.ENGINEER,
    )
    user = auth.get_user_by_id(auth.list_users()[1].user_id if len(auth.list_users()) > 1 else auth.list_users()[0].user_id)
    # find engineer-1
    for account in auth.list_users():
        if account.login_id == "engineer-1":
            user = account
            break
    profiles = ProfileService(auth)
    updated = profiles.update_profile(user.user_id, display_name="Engineer Updated", bio="FFSC specialist")
    assert updated.display_name == "Engineer Updated"
    assert updated.bio == "FFSC specialist"
    mapping = profiles.profile_mapping(updated)
    assert mapping["bio"] == "FFSC specialist"

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
        b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    url = profiles.save_photo(user.user_id, png)
    assert url.startswith("/assets/profiles/")
    assert profiles.photo_url(user.user_id) == url
