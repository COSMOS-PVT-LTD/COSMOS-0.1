"""Required CI quality checks must remain blocking and include workflow packages."""

from pathlib import Path


def test_ci_has_blocking_workflow_quality_checks() -> None:
    repository = Path(__file__).resolve().parents[2]
    workflow = (repository / ".github/workflows/ci.yml").read_text()
    assert "continue-on-error" not in workflow
    ruff_command = next(
        line for line in workflow.splitlines() if "python -m ruff check" in line
    )
    for package in ("core", "knowledge", "physics", "numerics", "systems", "api", "gui", "tests"):
        assert package in ruff_command.split()
    assert "python -m mypy core physics numerics systems api" in workflow
    assert "python -m pytest" in workflow
