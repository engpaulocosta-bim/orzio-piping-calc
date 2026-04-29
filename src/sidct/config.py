"""Configuração global do sistema SIDCT."""
from __future__ import annotations
import functools
import sys
import yaml
from pathlib import Path

_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))  # repo root or PyInstaller bundle


@functools.lru_cache(maxsize=16)
def _load_yaml(name: str) -> dict:
    path = _ROOT / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_project_profiles() -> dict:
    data = _load_yaml("project_profiles.yaml")
    return data.get("profiles", {})


def get_service_matrix() -> dict:
    data = _load_yaml("service_matrix.yaml")
    return data.get("services", {})


def get_standards_registry() -> dict:
    data = _load_yaml("standards_registry.yaml")
    return {s["id"]: s for s in data.get("standards", [])}


def get_profile(profile_id: str) -> dict:
    profiles = get_project_profiles()
    if profile_id not in profiles:
        from .exceptions import ProfileNotFoundError
        raise ProfileNotFoundError(profile_id)
    return profiles[profile_id]


def get_service_config(service_id: str) -> dict:
    matrix = get_service_matrix()
    if service_id not in matrix:
        from .exceptions import ValidationError
        raise ValidationError(f"Serviço '{service_id}' não encontrado na service_matrix", "service")
    return matrix[service_id]
