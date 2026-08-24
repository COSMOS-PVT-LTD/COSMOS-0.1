"""Unit tests for export watermark helper."""

from __future__ import annotations

from infrastructure.watermark import apply_text_watermark, watermark_footer


def test_watermark_footer_contains_branding_and_user() -> None:
    footer = watermark_footer(login_id="engineer-1")
    assert "COSMOS 0.1" in footer
    assert "TO INFINITY AND BEYOND" in footer
    assert "engineer-1" in footer


def test_apply_text_watermark_is_idempotent() -> None:
    original = "export payload"
    once = apply_text_watermark(original, login_id="engineer-1")
    twice = apply_text_watermark(once, login_id="engineer-1")
    assert once == twice
    assert "COSMOS 0.1" in once
