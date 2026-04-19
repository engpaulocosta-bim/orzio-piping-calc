"""Loaders para datasets externos fornecidos pelo utilizador."""
from __future__ import annotations
import csv
from pathlib import Path
from ..exceptions import DatasetMissingError

_ROOT = Path(__file__).parent.parent.parent.parent


def load_user_pipe_catalog(catalog_name: str) -> list[dict]:
    """Carrega catálogo dimensional fornecido pelo utilizador (CSV)."""
    path = _ROOT / "data" / "user_supplied" / f"{catalog_name.lower()}_catalog.csv"
    if not path.exists():
        template = _ROOT / "data" / "templates" / f"{catalog_name.lower()}_catalog_template.csv"
        raise DatasetMissingError(
            catalog_name,
            f"Ficheiro não encontrado: {path}. "
            + (f"Template disponível em: {template}" if template.exists() else
               "Criar ficheiro CSV conforme template em /data/templates/")
        )
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_user_material_stresses(material: str) -> list[dict]:
    """Carrega tensões admissíveis fornecidas pelo utilizador."""
    path = _ROOT / "data" / "user_supplied" / f"stress_{material.lower()}.csv"
    if not path.exists():
        raise DatasetMissingError(
            f"stress_{material}",
            f"Tensões admissíveis para '{material}' não encontradas em {path}. "
            "Use o template em /data/templates/material_stress_template.csv"
        )
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows
