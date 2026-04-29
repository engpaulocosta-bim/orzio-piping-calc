"""Catálogo de tensões admissíveis — subset de literatura pública.

AVISO: Estes valores são de referência pública para materiais comuns.
Para projeto real, verificar Appendix A da norma aplicável (ASME B31.3,
B31.9, EN 13480) com a edição contratual.

Fonte: publicações técnicas de domínio público, literatura de engenharia.
"""
from __future__ import annotations
from ..exceptions import MaterialNotFoundError, DatasetMissingError

# ─── Estrutura: {material_key: [(T_max_C, S_MPa, E_seamless, E_ERW, Y)]}
# S = tensão admissível [MPa]
# E = eficiência de junta soldada (seamless=1.0, ERW=0.85)
# Y = factor Y para espessura (ASME B31.3 Table 304.1.1)

MATERIAL_STRESS: dict[str, list[tuple]] = {
    # A106 Grade B — Carbon steel seamless
    # Ref: ASME B31.3 Appendix A (valores de literatura pública)
    "A106GRB": [
        # (T_max_C, S_MPa, E_seamless, E_ERW, Y)
        (38,   138.0, 1.0, 0.85, 0.4),
        (93,   138.0, 1.0, 0.85, 0.4),
        (150,  138.0, 1.0, 0.85, 0.4),
        (200,  138.0, 1.0, 0.85, 0.4),
        (260,  131.7, 1.0, 0.85, 0.4),
        (315,  117.9, 1.0, 0.85, 0.4),
        (370,  110.3, 1.0, 0.85, 0.4),
        (425,   96.5, 1.0, 0.85, 0.4),
        (480,   82.7, 1.0, 0.85, 0.5),
        (538,   58.6, 1.0, 0.85, 0.7),
    ],

    # A53 Grade B — Carbon steel (ERW ou seamless)
    "A53GRB": [
        (38,   103.4, 1.0, 0.85, 0.4),
        (93,   103.4, 1.0, 0.85, 0.4),
        (150,  103.4, 1.0, 0.85, 0.4),
        (200,  103.4, 1.0, 0.85, 0.4),
        (260,   96.5, 1.0, 0.85, 0.4),
        (315,   82.7, 1.0, 0.85, 0.4),
        (370,   72.4, 1.0, 0.85, 0.4),
    ],

    # A312 TP304 — Stainless 304
    "A312TP304": [
        (38,   115.1, 1.0, 1.0, 0.4),
        (93,   108.2, 1.0, 1.0, 0.4),
        (150,  101.3, 1.0, 1.0, 0.4),
        (200,   98.6, 1.0, 1.0, 0.4),
        (260,   94.5, 1.0, 1.0, 0.4),
        (315,   90.3, 1.0, 1.0, 0.4),
        (370,   88.0, 1.0, 1.0, 0.4),
        (425,   86.2, 1.0, 1.0, 0.4),
        (480,   84.1, 1.0, 1.0, 0.4),
        (540,   79.3, 1.0, 1.0, 0.5),
    ],

    # A312 TP316 — Stainless 316
    "A312TP316": [
        (38,   115.1, 1.0, 1.0, 0.4),
        (93,   110.3, 1.0, 1.0, 0.4),
        (150,  103.4, 1.0, 1.0, 0.4),
        (200,  100.0, 1.0, 1.0, 0.4),
        (260,   96.5, 1.0, 1.0, 0.4),
        (315,   93.1, 1.0, 1.0, 0.4),
        (370,   90.3, 1.0, 1.0, 0.4),
        (425,   88.0, 1.0, 1.0, 0.4),
        (480,   86.2, 1.0, 1.0, 0.4),
        (540,   82.7, 1.0, 1.0, 0.5),
    ],

    # A333 Grade 6 — Low-temperature carbon steel (criogénico)
    "A333GR6": [
        (-46,  138.0, 1.0, 0.85, 0.4),
        (38,   138.0, 1.0, 0.85, 0.4),
        (93,   138.0, 1.0, 0.85, 0.4),
        (150,  138.0, 1.0, 0.85, 0.4),
        (200,  138.0, 1.0, 0.85, 0.4),
    ],

    # PVC-U — conservative public engineering placeholder for pressure-class checks.
    # Final design must use manufacturer/standard derating tables.
    "PVCU": [
        (20,  10.0, 1.0, 1.0, 0.4),
        (40,   8.0, 1.0, 1.0, 0.4),
        (60,   5.0, 1.0, 1.0, 0.4),
    ],
}

# Aliases (normalização)
MATERIAL_ALIASES: dict[str, str] = {
    "A106B": "A106GRB",
    "A106 GRB": "A106GRB",
    "A106-GRB": "A106GRB",
    "A106GR.B": "A106GRB",
    "A53B": "A53GRB",
    "A53 GRB": "A53GRB",
    "A53-GRB": "A53GRB",
    "A53GR.B": "A53GRB",
    "TP304": "A312TP304",
    "304": "A312TP304",
    "A312-TP304": "A312TP304",
    "TP316": "A312TP316",
    "316": "A312TP316",
    "316L": "A312TP316",
    "304L": "A312TP304",
    "A312-TP316": "A312TP316",
    "A333-6": "A333GR6",
    "A333GR.6": "A333GR6",
    "PVC": "PVCU",
    "PVC-U": "PVCU",
    "PVCU": "PVCU",
    "PVCU_EU": "PVCU",
    "PVCU_US": "PVCU",
}


def _normalize_material(material: str) -> str:
    key = material.upper().replace(" ", "").replace("-", "").replace(".", "")
    return MATERIAL_ALIASES.get(key, key)


def get_allowable_stress(
    material: str,
    T_design_c: float,
    weld_joint: str = "seamless",
) -> tuple[float, float, float, str]:
    """
    Retorna (S_MPa, E_factor, Y_factor, normalized_key).

    Raises MaterialNotFoundError quando material ou T fora do dataset.
    """
    key = _normalize_material(material)
    if key not in MATERIAL_STRESS:
        raise MaterialNotFoundError(material, T_design_c)

    data = MATERIAL_STRESS[key]
    # Encontrar a entrada com T_max_C >= T_design_c
    valid = [(t, s, ee_s, ee_e, y) for (t, s, ee_s, ee_e, y) in data if t >= T_design_c]
    if not valid:
        T_max = max(t for (t, _, __, ___, ____) in data)
        raise MaterialNotFoundError(
            material,
            T_design_c,
        )

    # Pegar o primeiro (menor T_max >= T_design_c)
    t_max, S, E_s, E_e, Y = min(valid, key=lambda x: x[0])

    E = E_s if weld_joint.lower() in ("seamless", "smls") else E_e
    return S, E, Y, key


def list_supported_materials() -> list[str]:
    return sorted(MATERIAL_STRESS.keys())


def is_material_supported(material: str) -> bool:
    key = _normalize_material(material)
    return key in MATERIAL_STRESS
