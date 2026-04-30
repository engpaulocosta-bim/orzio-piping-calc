"""System-to-pipe-material decision matrix."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

import yaml

from .exceptions import ValidationError
from .materials import normalize_material_key

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
MAPPING_PATH = ROOT / "system_pipe_mapping.yaml"

ALLOWED_GROUPS = ("preferred_materials", "allowed_materials", "conditional_materials")
BLOCKED_GROUP = "blocked_materials"


@dataclass(frozen=True)
class PipeMaterialOption:
    system_id: str
    region: str
    group: str
    material_id: str
    display_name: str
    sidct_material: str | None = None
    calculation_ready: bool = False
    contexts: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    reason: str | None = None
    selection_rank: int = 999

    @property
    def status(self) -> str:
        if self.group == "preferred_materials":
            return "preferred"
        if self.group == "allowed_materials":
            return "allowed"
        if self.group == "conditional_materials":
            return "conditional"
        return "blocked"

    @property
    def selectable(self) -> bool:
        return self.group in ALLOWED_GROUPS and self.sidct_material is not None


@lru_cache(maxsize=1)
def load_system_pipe_mapping() -> dict[str, Any]:
    if not MAPPING_PATH.exists():
        return {"systems": {}}
    with MAPPING_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {"systems": {}}


def normalize_region(region: str) -> str:
    value = (region or "EU").upper()
    if value in {"USA", "US", "UNITED_STATES"}:
        return "US"
    if value in {"EU", "EUROPE", "INTERNATIONAL", "BRAZIL"}:
        return "EU"
    return value


def get_system_mapping(system_id: str, region: str = "EU") -> dict[str, Any]:
    systems = load_system_pipe_mapping().get("systems", {})
    system = systems.get(system_id, {})
    regions = system.get("regions", {})
    normalized = normalize_region(region)
    selected = regions.get(normalized) or regions.get("EU") or {}
    return {
        "system_id": system_id,
        "system_name": system.get("system_name", system_id),
        "future_extension_ready": system.get("future_extension_ready", True),
        "engineering_notes": system.get("engineering_notes", []),
        "region": normalized,
        **selected,
    }


def _option_from_item(system_id: str, region: str, group: str, item: dict[str, Any]) -> PipeMaterialOption:
    return PipeMaterialOption(
        system_id=system_id,
        region=region,
        group=group,
        material_id=item.get("material_id", item.get("display_name", "")),
        display_name=item.get("display_name", item.get("material_id", "")),
        sidct_material=item.get("sidct_material"),
        calculation_ready=bool(item.get("calculation_ready", False)),
        contexts=tuple(item.get("contexts", []) or []),
        limitations=tuple(item.get("limitations", []) or []),
        warnings=tuple(item.get("warnings", []) or []),
        reason=item.get("reason"),
        selection_rank=int(item.get("selection_rank", 999)),
    )


def get_material_options(system_id: str, region: str = "EU", include_blocked: bool = False) -> list[PipeMaterialOption]:
    mapping = get_system_mapping(system_id, region)
    options: list[PipeMaterialOption] = []
    for group in ALLOWED_GROUPS:
        for item in mapping.get(group, []) or []:
            options.append(_option_from_item(system_id, mapping["region"], group, item))
    if include_blocked:
        for item in mapping.get(BLOCKED_GROUP, []) or []:
            options.append(_option_from_item(system_id, mapping["region"], BLOCKED_GROUP, item))
    return sorted(options, key=lambda item: (item.selection_rank, item.status, item.display_name))


def get_calculation_ready_materials(system_id: str, region: str = "EU") -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for option in get_material_options(system_id, region):
        if not option.calculation_ready or not option.sidct_material:
            continue
        key = (option.sidct_material, option.status)
        if str(key) in seen:
            continue
        seen.add(str(key))
        result.append(option.sidct_material)
    return result


def get_mapping_notes(system_id: str, region: str = "EU") -> list[str]:
    mapping = get_system_mapping(system_id, region)
    notes = list(mapping.get("engineering_notes", []) or [])
    for option in get_material_options(system_id, region):
        if option.status == "conditional":
            note_parts = list(option.warnings or []) + list(option.limitations or [])
            if note_parts:
                notes.append(f"{option.display_name}: {'; '.join(note_parts[:3])}")
        if option.calculation_ready:
            continue
        notes.append(f"{option.display_name}: {', '.join(option.warnings) or 'not calculation-ready in current dataset'}")
    return notes


def _material_matches(option: PipeMaterialOption, material: str, region: str) -> bool:
    normalized = normalize_material_key(material, region)
    if option.sidct_material and normalize_material_key(option.sidct_material, region) == normalize_material_key(material, region):
        return True
    if option.material_id in {"carbon_steel", "carbon_steel_black", "carbon_steel_pressure"}:
        return normalized in {"A106GRB", "A53GRB", "A333GR6"}
    if option.material_id.startswith("stainless_steel"):
        return normalized in {"A312TP304", "A312TP316"}
    if option.material_id.startswith("pvc") or option.material_id == "pvc_u":
        return normalized in {"PVCU_EU", "PVCU_US", "PVCU"}
    return option.material_id.lower() == material.lower().replace(" ", "_")


def validate_system_material_selection(
    system_id: str,
    material: str,
    region: str = "EU",
    require_calculation_ready: bool = True,
) -> list[str]:
    """Validate selected material against the engineering matrix."""
    options = get_material_options(system_id, region, include_blocked=True)
    matches = [option for option in options if _material_matches(option, material, region)]
    if not matches:
        return [
            f"Material '{material}' is not explicitly mapped for system '{system_id}'. "
            "Treat as engineering exception and verify project standards."
        ]

    option = matches[0]
    if option.group == BLOCKED_GROUP:
        raise ValidationError(
            f"Material '{material}' is blocked for system '{system_id}': {option.reason or 'not suitable'}",
            "material",
        )
    if require_calculation_ready and not option.calculation_ready:
        raise ValidationError(
            f"Material '{option.display_name}' is technically mapped for '{system_id}' "
            "but is not calculation-ready in this SIDCT dataset.",
            "material",
        )

    warnings = list(option.warnings)
    if option.status == "conditional":
        warnings.append(
            f"Material '{option.display_name}' is conditional for system '{system_id}'; "
            "engineering confirmation is required."
        )
    warnings.extend(option.limitations)
    return warnings
