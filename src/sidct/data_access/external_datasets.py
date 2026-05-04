"""Optional user-supplied engineering datasets.

These helpers deliberately do not invent normative or manufacturer data. They
look for project/user datasets and return explicit audit messages when the data
is absent.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
PLASTIC_DERATING_FILE = "plastic_derating.yaml"
EXTERNAL_PRESSURE_FILE = "external_pressure_charts.yaml"


def _user_data_dirs() -> list[Path]:
    candidates = [
        Path.cwd() / "data" / "user_supplied",
        ROOT / "data" / "user_supplied",
    ]
    if getattr(sys, "frozen", False):
        candidates.insert(1, Path(sys.executable).resolve().parent / "data" / "user_supplied")

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def _preferred_user_path(file_name: str) -> Path:
    for directory in _user_data_dirs():
        path = directory / file_name
        if path.exists():
            return path
    return _user_data_dirs()[0] / file_name


@lru_cache(maxsize=8)
def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def plastic_derating_notice(material_key: str) -> str | None:
    """Return a notice when no user derating dataset exists for a plastic."""
    path = _preferred_user_path(PLASTIC_DERATING_FILE)
    data = _load_yaml(path)
    materials = data.get("materials", {}) if isinstance(data, dict) else {}
    if material_key in materials:
        return None
    return (
        f"No user plastic derating dataset found for {material_key}. "
        f"Add manufacturer data at {path} for final design."
    )


def external_pressure_chart_notice(code: str = "ASME") -> str | None:
    """Return a notice when no rigorous external-pressure chart dataset exists."""
    path = _preferred_user_path(EXTERNAL_PRESSURE_FILE)
    data = _load_yaml(path)
    charts = data.get("charts", {}) if isinstance(data, dict) else {}
    if code.upper() in {str(key).upper() for key in charts}:
        return None
    return (
        f"No user external-pressure chart dataset found for {code}. "
        f"Add chart data at {path} for final certification checks."
    )
