"""Refresh only a NEW, as-yet-unqualified package created by our builder.

Never updates the installed verified application or historical native receipts.
Runtime closure is unchanged; all software/native checks must run afterward.
"""

import argparse
import json
import shutil
from pathlib import Path

from scripts.build_standalone_desktop import PACKAGES, files


def refresh(repo, app):
    root = app / "Contents/Resources/app"
    marker = app / "Contents/Resources/desktop-stage.json"
    if (
        not app.is_absolute()
        or app.is_symlink()
        or not marker.is_file()
        or json.loads(marker.read_text())
        != {"schema": "cosmos.desktop-stage.v1", "source_root": str(repo)}
        or (root / "desktop-qualification").exists()
        or list(root.glob("desktop-verified*.json"))
    ):
        raise ValueError(
            "Only an explicitly task-built, not-yet-qualified desktop stage can be refreshed"
        )
    for package in PACKAGES:
        for source in files(repo / package):
            target = root / source.relative_to(repo)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for source in (repo / "scripts").glob("*"):
        if source.is_file() and source.suffix in {".py", ".c"}:
            shutil.copy2(source, root / "scripts" / source.name)
    print(
        "New unqualified desktop source stage refreshed; original app/data/receipts unchanged"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    args = parser.parse_args()
    refresh(Path(__file__).resolve().parents[1], args.app)


if __name__ == "__main__":
    main()
