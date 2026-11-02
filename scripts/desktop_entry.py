"""Bundle bootstrap: import packaged sources only; logs never contain credentials."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

if __name__ == "__main__":
    import logging
    import traceback

    logs = Path.home() / "Library/Logs/COSMOS"
    logs.mkdir(parents=True, exist_ok=True, mode=0o700)
    logging.basicConfig(filename=logs / "desktop.log", level=logging.WARNING)
    try:
        from gui.desktop_app import main

        main()
    except Exception:
        logging.getLogger(__name__).exception("Desktop launch failed")
        if "--check" in sys.argv:
            raise
        from AppKit import NSAlert, NSAlertStyleCritical

        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(NSAlertStyleCritical)
        alert.setMessageText_("COSMOS could not open the desktop workspace")
        alert.setInformativeText_(
            "Your saved projects were not migrated or deleted. Details: "
            + str(logs / "desktop.log")
            + "\n\n"
            + traceback.format_exc().splitlines()[-1]
        )
        alert.runModal()
        sys.exit(1)
