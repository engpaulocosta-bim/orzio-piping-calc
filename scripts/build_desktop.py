"""Build SIDCT desktop executable with PyInstaller."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "SIDCT",
        "--distpath",
        "dist_desktop_adaptive_v2",
        "--workpath",
        "build_desktop",
        "--paths",
        "src",
        "--add-data",
        "project_profiles.yaml;.",
        "--add-data",
        "service_matrix.yaml;.",
        "--add-data",
        "standards_registry.yaml;.",
        "--add-data",
        "assumptions.yaml;.",
        "--add-data",
        "system_pipe_mapping.yaml;.",
        "--add-data",
        "form_behavior_matrix.yaml;.",
        "app.py",
    ]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
