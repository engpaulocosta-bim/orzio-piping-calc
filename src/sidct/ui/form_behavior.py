"""Adaptive form behavior rules for the SIDCT desktop UI."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
MATRIX_PATH = ROOT / "form_behavior_matrix.yaml"


@dataclass(frozen=True)
class FieldMeta:
    field_id: str
    label_en: str
    label_pt_BR: str
    help_en: str
    help_pt_BR: str

    def label(self, language: str) -> str:
        return self.label_pt_BR if language == "pt-BR" else self.label_en

    def help(self, language: str) -> str:
        return self.help_pt_BR if language == "pt-BR" else self.help_en


@dataclass(frozen=True)
class FormBehavior:
    system_id: str
    calc_mode: str
    regime_en: str
    regime_pt_BR: str
    visible_fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    disabled_fields: tuple[str, ...]
    hidden_fields: tuple[str, ...]
    warning_fields: tuple[str, ...]
    field_help: dict[str, str]
    validation_rules: tuple[str, ...]
    explanatory_note_en: str
    explanatory_note_pt_BR: str

    def regime(self, language: str) -> str:
        return self.regime_pt_BR if language == "pt-BR" else self.regime_en

    def explanatory_note(self, language: str) -> str:
        return self.explanatory_note_pt_BR if language == "pt-BR" else self.explanatory_note_en


def _resource_path() -> Path:
    if MATRIX_PATH.exists():
        return MATRIX_PATH
    fallback = Path.cwd() / "form_behavior_matrix.yaml"
    return fallback


@lru_cache(maxsize=1)
def load_form_behavior_matrix() -> dict[str, Any]:
    path = _resource_path()
    if not path.exists():
        return {"fields": {}, "systems": {}, "calc_modes": {}, "common": {}}
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {"fields": {}, "systems": {}, "calc_modes": {}, "common": {}}


def list_fields() -> tuple[str, ...]:
    return tuple(load_form_behavior_matrix().get("fields", {}).keys())


def get_field_meta(field_id: str) -> FieldMeta:
    data = load_form_behavior_matrix().get("fields", {}).get(field_id, {})
    return FieldMeta(
        field_id=field_id,
        label_en=data.get("label_en", field_id),
        label_pt_BR=data.get("label_pt_BR", data.get("label_en", field_id)),
        help_en=data.get("help_en", ""),
        help_pt_BR=data.get("help_pt_BR", data.get("help_en", "")),
    )


def get_calc_mode_label(calc_mode: str, language: str) -> str:
    data = load_form_behavior_matrix().get("calc_modes", {}).get(calc_mode, {})
    if language == "pt-BR":
        return data.get("label_pt_BR", data.get("label_en", calc_mode))
    return data.get("label_en", calc_mode)


def get_calc_modes() -> tuple[str, ...]:
    return tuple(load_form_behavior_matrix().get("calc_modes", {}).keys())


def _system_rule(system_id: str) -> dict[str, Any]:
    systems = load_form_behavior_matrix().get("systems", {})
    for rule in systems.values():
        if system_id in (rule.get("applies_to") or []):
            return rule
    return systems.get("default_pressurized", {})


def get_form_behavior(system_id: str, calc_mode: str = "calculate_new") -> FormBehavior:
    data = load_form_behavior_matrix()
    rule = _system_rule(system_id)
    common = data.get("common", {})

    visible = list(rule.get("visible_fields", []) or [])
    hidden = set(rule.get("hidden_fields", []) or [])
    disabled = set(rule.get("disabled_fields", []) or [])
    required = set(rule.get("required_fields", []) or [])
    optional = set(rule.get("optional_fields", []) or [])
    warning = set(rule.get("warning_fields", []) or [])

    for field_id in common.get("always_visible", []) or []:
        if field_id not in visible:
            visible.append(field_id)
        hidden.discard(field_id)

    for field_id in (common.get("mode_required", {}) or {}).get(calc_mode, []) or []:
        required.add(field_id)
        if field_id not in visible:
            visible.append(field_id)
        hidden.discard(field_id)
        optional.discard(field_id)

    all_fields = set(data.get("fields", {}).keys())
    visible_set = set(visible)
    hidden.update(all_fields - visible_set)

    field_help = {
        field_id: get_field_meta(field_id).help_en
        for field_id in visible
    }
    return FormBehavior(
        system_id=system_id,
        calc_mode=calc_mode,
        regime_en=rule.get("regime_en", "Pressurized incompressible"),
        regime_pt_BR=rule.get("regime_pt_BR", rule.get("regime_en", "Pressurizado incompressivel")),
        visible_fields=tuple(visible),
        required_fields=tuple(sorted(required)),
        optional_fields=tuple(sorted(optional)),
        disabled_fields=tuple(sorted(disabled)),
        hidden_fields=tuple(sorted(hidden)),
        warning_fields=tuple(sorted(warning)),
        field_help=field_help,
        validation_rules=tuple(rule.get("validation_rules", []) or []),
        explanatory_note_en=rule.get("explanatory_note_en", ""),
        explanatory_note_pt_BR=rule.get("explanatory_note_pt_BR", rule.get("explanatory_note_en", "")),
    )
