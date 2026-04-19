"""K-values para fittings e válvulas — Crane TP-410 / Idel'chik (literatura pública).

Valores típicos para fittings padrão. Para fittings de fabricante específico,
o utilizador deve fornecer K-value real.

Fonte: Crane Technical Paper 410 (2013) — valores de literatura pública.
"""
from __future__ import annotations

# Formato: {fitting_type: K_value}
# K-values baseados em velocidade na tubagem (não no fitting)

FITTING_K: dict[str, float] = {
    # Curvas (elbows)
    "90_LR_ELBOW": 0.3,       # 90° long radius elbow (R/D=1.5)
    "90_SR_ELBOW": 0.9,       # 90° short radius elbow (R/D=1.0)
    "45_LR_ELBOW": 0.2,       # 45° long radius elbow
    "45_ELBOW": 0.4,          # 45° standard elbow
    "180_RETURN_LR": 0.4,     # 180° return bend LR
    "180_RETURN_SR": 1.5,     # 180° return bend SR
    "90_MITER_1CUT": 1.8,     # 90° miter (1 cut)
    "90_MITER_2CUT": 0.9,     # 90° miter (2 cuts)
    "90_MITER_3CUT": 0.6,     # 90° miter (3 cuts)

    # Tees
    "TEE_FLOW_THROUGH": 0.2,  # Tee, escoamento directo
    "TEE_BRANCH": 1.0,        # Tee, escoamento por derivação

    # Reduções
    "CONCENTRIC_REDUCER": 0.1,
    "ECCENTRIC_REDUCER": 0.1,

    # Válvulas
    "GATE_VALVE_FULL_OPEN": 0.2,
    "GATE_VALVE_75PCT": 0.9,
    "GATE_VALVE_50PCT": 4.5,
    "GATE_VALVE_25PCT": 24.0,
    "BALL_VALVE_FULL_OPEN": 0.05,
    "BUTTERFLY_VALVE_FULL_OPEN": 0.6,
    "GLOBE_VALVE_FULL_OPEN": 6.0,
    "CHECK_VALVE_SWING": 2.5,
    "CHECK_VALVE_LIFT": 12.0,
    "ANGLE_VALVE": 4.0,
    "NEEDLE_VALVE": 0.8,
    "DIAPHRAGM_VALVE": 2.3,

    # Entradas e saídas
    "SHARP_ENTRY": 0.5,       # Entrada flush/afiada
    "SHARP_EXIT": 1.0,        # Saída para reservatório
    "REENTRANT_ENTRY": 0.8,
    "ROUNDED_ENTRY": 0.04,

    # Strainer / filtro
    "Y_STRAINER": 1.0,
    "BASKET_STRAINER": 1.5,
}

# Aliases para normalização de entrada
FITTING_ALIASES: dict[str, str] = {
    "90LR": "90_LR_ELBOW",
    "90LRELBOW": "90_LR_ELBOW",
    "90LR_ELBOW": "90_LR_ELBOW",
    "90_LR": "90_LR_ELBOW",
    "90ELBOW": "90_SR_ELBOW",
    "90SRELBOW": "90_SR_ELBOW",
    "45LR": "45_LR_ELBOW",
    "45ELBOW": "45_ELBOW",
    "TEE_THROUGH": "TEE_FLOW_THROUGH",
    "TEE_RUN": "TEE_FLOW_THROUGH",
    "TEE_SIDE": "TEE_BRANCH",
    "GATE": "GATE_VALVE_FULL_OPEN",
    "BALL": "BALL_VALVE_FULL_OPEN",
    "BUTTERFLY": "BUTTERFLY_VALVE_FULL_OPEN",
    "GLOBE": "GLOBE_VALVE_FULL_OPEN",
    "CHECK": "CHECK_VALVE_SWING",
    "SWING_CHECK": "CHECK_VALVE_SWING",
}


def get_k_value(fitting_type: str) -> float | None:
    """Retorna K-value para o tipo de fitting. None se não encontrado."""
    key = fitting_type.upper().replace(" ", "_").replace("-", "_")
    if key in FITTING_K:
        return FITTING_K[key]
    alias = FITTING_ALIASES.get(key)
    if alias:
        return FITTING_K.get(alias)
    return None


def calculate_total_k(
    fittings: list,
    valves: list,
) -> tuple[float, list[str]]:
    """
    Calcula K total para lista de fittings e válvulas.

    Returns (K_total, warnings)
    """
    K_total = 0.0
    warnings: list[str] = []

    for f in fittings:
        qty = getattr(f, "quantity", 1)
        k = getattr(f, "k_value", None)
        if k is None:
            k = get_k_value(f.fitting_type)
        if k is None:
            warnings.append(
                f"Fitting '{f.fitting_type}' não encontrado no catálogo — K=1.0 assumido"
            )
            k = 1.0
        K_total += qty * k

    for v in valves:
        qty = getattr(v, "quantity", 1)
        k = getattr(v, "k_value", None)
        if k is None:
            k = get_k_value(v.valve_type)
        if k is None:
            warnings.append(
                f"Válvula '{v.valve_type}' não encontrada no catálogo — K=6.0 assumido (globe)"
            )
            k = 6.0
        K_total += qty * k

    return K_total, warnings
