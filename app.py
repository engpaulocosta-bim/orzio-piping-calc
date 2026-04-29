"""SIDCT desktop entry point."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sidct.ui.desktop_app import MissingDesktopDependency, main


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MissingDesktopDependency as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2)
