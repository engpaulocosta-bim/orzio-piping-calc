"""Motor hidráulico gravitário — Manning, tubo parcialmente cheio.

Aplicável a: sanitary_drainage, rainwater.
NUNCA usar Darcy-Weisbach como motor primário para estes serviços.

Refs:
- Manning, R. (1891) — equação de escoamento gravitário
- EN 12056-2: 2000 — Gravity drainage inside buildings
- Chaudhry, Open Channel Hydraulics (2008)
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, FluidProperties, HydraulicResult, PipeDimension
from ..catalogs.pipe_dimension_catalog import get_available_dns, get_pipe_dimension
from ..units import m3h_to_m3s, ls_to_m3s
from ..exceptions import MissingInputError, WrongEngineError, OutOfScopeError, ValidationError

logger = logging.getLogger("sidct.hydraulic_gravity")

VALID_SERVICES = {"sanitary_drainage", "rainwater"}
INCOMPRESSIBLE_SERVICES = {"potable_water", "service_water", "chilled_water",
                            "condenser_water", "osmotized_water", "fire_water"}

SELF_CLEANSING_V_MIN = 0.6  # m/s
MAX_FILL_RATIO = 0.8        # y/D máximo recomendado
MIN_FILL_RATIO = 0.1        # y/D mínimo verificado

# Coeficientes de Manning por material
MANNING_N: dict[str, float] = {
    "pvc": 0.010,
    "hdpe": 0.010,
    "concrete_smooth": 0.013,
    "concrete_rough": 0.016,
    "carbon_steel": 0.013,
    "stainless_steel": 0.011,
    "galvanized_steel": 0.015,
    "cast_iron": 0.013,
    "default": 0.013,
}


def _manning_n(material: str) -> float:
    m = material.lower().replace(" ", "_").replace("-", "_")
    for k, v in MANNING_N.items():
        if k in m:
            return v
    return MANNING_N["default"]


def _flow_rate_m3s(flow_rate: float, basis: str) -> float:
    b = basis.lower().replace(" ", "").replace("/", "").replace("_", "")
    if b in ("m3/s", "m3s"):
        return flow_rate
    if b in ("m3/h", "m3h"):
        return m3h_to_m3s(flow_rate)
    if b in ("l/s", "ls"):
        return ls_to_m3s(flow_rate)
    raise ValidationError(f"Unidade '{basis}' não suportada para escoamento gravitário", "flow_rate_basis")


def _full_flow_capacity(D_m: float, slope: float, n: float) -> float:
    """Caudal a secção cheia (Manning) [m³/s]."""
    A = math.pi * D_m**2 / 4.0
    R_h = D_m / 4.0  # raio hidráulico para secção cheia
    return (1.0 / n) * A * R_h**(2/3) * slope**0.5


def _partial_flow_depth(Q_m3s: float, D_m: float, slope: float, n: float,
                        max_iter: int = 100, tol: float = 1e-8) -> float:
    """
    Calcula profundidade de escoamento y (m) para caudal Q em tubo circular.
    Método iterativo sobre ângulo θ (rad) que define a secção molhada.
    """
    Q_full = _full_flow_capacity(D_m, slope, n)
    q_ratio = Q_m3s / Q_full  # Q/Q_full

    # Bisecção sobre ângulo θ ∈ (0, 2π)
    # Secção molhada: A = D²/8 * (θ - sin θ), P = D/2 * θ, R = D/4*(1 - sinθ/θ)
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    lo, hi = 1e-6, 2.0 * math.pi - 1e-6
    R = D_m / 2.0

    def q_at_theta(theta: float) -> float:
        A = R**2 / 2.0 * (theta - math.sin(theta))
        P = R * theta
        if P < 1e-12:
            return 0.0
        Rh = A / P
        return (1.0 / n) * A * Rh**(2/3) * slope**0.5

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        q_mid = q_at_theta(mid)
        if abs(q_mid - Q_m3s) < tol * Q_m3s:
            theta_sol = mid
            break
        if q_mid < Q_m3s:
            lo = mid
        else:
            hi = mid
    else:
        theta_sol = (lo + hi) / 2.0

    y = R * (1.0 - math.cos(theta_sol / 2.0))
    # Clampar y ao intervalo [0, D_m] para evitar y/D > 1.0 em casos limite
    y = max(0.0, min(y, D_m))
    return y


def calculate_gravity(
    inp: LineInput,
    fluid: FluidProperties,
    pipe: PipeDimension,
) -> HydraulicResult:
    """Cálculo gravitário Manning para tubo dado."""
    svc = inp.service
    if svc in INCOMPRESSIBLE_SERVICES:
        raise WrongEngineError("hydraulic_gravity", svc, "hydraulic_incompressible")
    if svc not in VALID_SERVICES:
        raise WrongEngineError("hydraulic_gravity", svc, "hydraulic_gravity")

    if inp.slope_mm_m is None or inp.slope_mm_m <= 0:
        raise MissingInputError("slope_mm_m", svc)

    slope = inp.slope_mm_m / 1000.0  # m/m

    Q_m3s = _flow_rate_m3s(inp.flow_rate, inp.flow_rate_basis)
    D_m = pipe.ID_m
    n = _manning_n(inp.material)

    Q_full = _full_flow_capacity(D_m, slope, n)
    warnings: list[str] = []

    if Q_m3s > Q_full:
        warnings.append(
            f"Caudal Q = {Q_m3s:.4f} m³/s excede capacidade a secção cheia "
            f"Q_full = {Q_full:.4f} m³/s — tubo subdimensionado"
        )
        return HydraulicResult(
            regime="gravity_partially_full",
            service=svc,
            line_tag=inp.line_tag,
            status="INSUFFICIENT",
            warnings=warnings + ["Tubo insuficiente — aumentar DN"],
            pipe_used=pipe,
            assumptions_used=["A-HG-001", "A-HG-002", "A-HG-003"],
        )

    y = _partial_flow_depth(Q_m3s, D_m, slope, n)
    y_D = y / D_m

    # Secção molhada para profundidade y
    theta = 2.0 * math.acos(1.0 - 2.0 * y / D_m)
    R = D_m / 2.0
    A_wet = R**2 / 2.0 * (theta - math.sin(theta))
    P_wet = R * theta
    R_h = A_wet / P_wet if P_wet > 0 else 0.0
    v = Q_m3s / A_wet if A_wet > 0 else 0.0

    # Verificações
    self_cleansing = v >= SELF_CLEANSING_V_MIN
    slope_ok = "OK"
    if slope < 0.001:
        warnings.append(f"Inclinação {inp.slope_mm_m:.1f} mm/m muito baixa — risco de sedimentação")
        slope_ok = "LOW"
    if y_D > MAX_FILL_RATIO:
        warnings.append(f"y/D = {y_D:.2f} > {MAX_FILL_RATIO} — escoamento próximo de secção cheia")
    if y_D < MIN_FILL_RATIO:
        warnings.append(f"y/D = {y_D:.2f} < {MIN_FILL_RATIO} — escoamento muito raso")
    if not self_cleansing:
        warnings.append(
            f"Velocidade v = {v:.2f} m/s < {SELF_CLEANSING_V_MIN} m/s — "
            f"sem auto-limpeza. Aumentar inclinação ou reduzir DN."
        )

    return HydraulicResult(
        regime="gravity_partially_full",
        service=svc,
        line_tag=inp.line_tag,
        velocity_ms=v,
        flow_depth_ratio=y_D,
        slope_adequacy=slope_ok,
        self_cleansing_ok=self_cleansing,
        pipe_used=pipe,
        status="CALCULATED",
        warnings=warnings,
        assumptions_used=["A-HG-001", "A-HG-002", "A-HG-003", "A-HG-004"],
    )


def select_dn(
    inp: LineInput,
    fluid: FluidProperties,
    target_fill_ratio: float = 0.6,
    catalog: str = "ASME_B36_10M",
    schedule: str = "SCH40",
) -> HydraulicResult:
    """Selecciona DN para escoamento gravitário com ratio de enchimento alvo."""
    if inp.slope_mm_m is None:
        raise MissingInputError("slope_mm_m", inp.service)
    slope = inp.slope_mm_m / 1000.0
    Q_m3s = _flow_rate_m3s(inp.flow_rate, inp.flow_rate_basis)
    n = _manning_n(inp.material)

    dns = get_available_dns(catalog)
    for dn in sorted(dns):
        try:
            pipe = get_pipe_dimension(catalog, dn, schedule)
        except Exception:
            continue
        Q_full = _full_flow_capacity(pipe.ID_m, slope, n)
        # Com ratio alvo, Q_design / Q_full ≈ 0.83 para y/D=0.6 (Manning)
        # Simplificação: Q_full > Q / 0.75 (margen conservativa)
        if Q_full >= Q_m3s / 0.75:
            result = calculate_gravity(inp, fluid, pipe)
            result.DN_governing_mm = dn
            result.governing_criterion = "fill_ratio"
            return result

    return HydraulicResult(
        regime="gravity_partially_full",
        service=inp.service,
        line_tag=inp.line_tag,
        status="OUT_OF_SCOPE",
        warnings=["DN não encontrado no catálogo para as condições de escoamento gravitário"],
    )
