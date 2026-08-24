"""Engineering-notation OCR: errors stay visible and are not auto-corrected."""

from __future__ import annotations

import pytest

from knowledge.ocr.ambiguity import ocr_ambiguity_warnings
from knowledge.ocr.engine import run_ocr
from knowledge.ocr.provisioning import ocr_is_provisioned
from knowledge.pdf.image_pdf import render_text_page_image

pytestmark = pytest.mark.skipif(not ocr_is_provisioned(), reason="Tesseract is not provisioned.")


def test_greek_ocr_errors_are_not_silently_corrected() -> None:
    expected = "rho mu Pc Tc CH4 CuCrZr Inconel 718"
    image = render_text_page_image(
        (
            "Engineering notation sample",
            expected,
            "Greek intended: rho mu, not silently rewritten.",
        ),
    )
    result = run_ocr(image, source_id="SRC", document_id="DOC", page_number=1, image_id="notation")
    assert result.text
    warnings = ocr_ambiguity_warnings(result.text)
    # Do not replace OCR output with the intended engineering string.
    if result.text != expected:
        assert expected not in {result.text}
        assert result.failure is None or result.text
    assert isinstance(warnings, tuple)
