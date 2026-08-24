"""User profile updates and photo storage."""

from __future__ import annotations

from pathlib import Path

from api.authentication import AuthService, AuthenticationError, UserAccount

__all__ = ("ProfileService",)

ALLOWED_IMAGE_KINDS = {"jpeg", "png", "webp"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def _detect_image_kind(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


class ProfileService:
    def __init__(self, auth: AuthService) -> None:
        self.auth = auth
        self.photo_dir = auth.root / "profiles"
        self.photo_dir.mkdir(parents=True, exist_ok=True)

    def profile_mapping(self, user: UserAccount) -> dict[str, object]:
        payload = self.auth.user_to_mapping(user)
        payload["bio"] = user.bio
        payload["profile_photo_url"] = self.photo_url(user.user_id)
        return payload

    def photo_url(self, user_id: str) -> str | None:
        for suffix in (".jpg", ".jpeg", ".png", ".webp"):
            if (self.photo_dir / f"{user_id}{suffix}").is_file():
                return f"/assets/profiles/{user_id}{suffix}"
        return None

    def update_profile(
        self,
        user_id: str,
        *,
        display_name: str | None = None,
        designation: str | None = None,
        team: str | None = None,
        bio: str | None = None,
    ) -> UserAccount:
        fields: dict[str, str] = {}
        if display_name is not None:
            fields["display_name"] = display_name.strip()
        if designation is not None:
            fields["designation"] = designation.strip()
        if team is not None:
            fields["team"] = team.strip()
        if bio is not None:
            fields["bio"] = bio.strip()[:500]
        if not fields:
            raise AuthenticationError("No profile fields supplied.")
        return self.auth.update_user_profile(user_id, **fields)

    def save_photo(self, user_id: str, content: bytes) -> str:
        if not content or len(content) > MAX_PHOTO_BYTES:
            raise AuthenticationError("Profile photo must be under 5 MB.")
        kind = _detect_image_kind(content)
        if kind not in ALLOWED_IMAGE_KINDS:
            raise AuthenticationError("Profile photo must be JPEG, PNG, or WebP.")
        suffix = ".jpg" if kind == "jpeg" else f".{kind}"
        for existing in self.photo_dir.glob(f"{user_id}.*"):
            existing.unlink(missing_ok=True)
        target = self.photo_dir / f"{user_id}{suffix}"
        target.write_bytes(content)
        self.auth.set_profile_photo(user_id, f"{user_id}{suffix}")
        return f"/assets/profiles/{user_id}{suffix}"

    def resolve_photo_path(self, relative: str) -> Path | None:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            return None
        resolved = self.photo_dir / candidate.name
        if resolved.is_file():
            return resolved
        return None
