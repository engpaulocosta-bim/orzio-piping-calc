"""Motor hidráulico compressível — modelo isotérmico.

Aplicável a: compressed_air, natural_gas.

Modelo: escoamento isotérmico compressível em tubo circular.
Equação de impulso integrada com atrito (modelo de Fanno simplificado).
Envelope: Ma < 0.3, pressure ratio P2/P1 > 0.5.

Refs:
- White, Fluid Mechanics (McGraw-Hill) — Chapter 9
- Crane TP-410 — gas flow formulas
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, FluidProperties, HydraulicResult, PipeDimension
from ..catalogs.pipe_dimension_catalog import get_available_dns, get_pipe_dimension
from ..catalogs.fitting_k_catalog import calculate_total_k
from ..units import (nm3h_to_m3s_at_tp, sm3h_to_m3s_at_tp, m3h_to_m3s,
                     barg_to_pa_abs, pa_to_bar, R_UNIVERSAL, P_ATM_PA)
from ..exceptions import OutOfScopeError, WrongEngineError, ValidationError
from .colebrook import colebrook_white as _colebrook_white

logger = logging.getLogger("sidct.hydraulic_compressible")

VALID_SERVICES = {"compressed_air", "natural_gas"}
MA_LIMIT = 0.3
PRESSURE_RATIO_LIMIT = 0.5


def _mass_flow_kgs(flow_rate: float, basis: str, fluid: FluidProperties) -> float:
    """Converte caudal para kg/s."""
    b = basis.lower().replace(" ", "").replace("/", "").replace("_", "")
    if b == "kg/s" or b == "kgs":
        return flow_rate
    if b in ("nm3/h", "nm3h"):
        m3s = nm3h_to_m3s_at_tp(flow_rate, fluid.T_K, fluid.P_pa)
        return m3s * fluid.rho_kgm3
    if b in ("sm3/h", "sm3h"):
        m3s = sm3h_to_m3s_at_tp(flow_rate, fluid.T_K, fluid.P_pa)
        return m3s * fluid.rho_kgm3
    if b in ("m3/h", "m3h"):
        m3s = m3h_to_m3s(flow_rate)
        return m3s * fluid.rho_kgm3
    raise ValidationError(f"Unidade de caudal '{basis}' não suportada para gases", "flow_rate_basis")


def calculate_compressible(
    inp: LineInput,
    fluid: FluidProperties,
    pipe: PipeDimension,
    roughness_m: float | None = None,
) -> HydraulicResult:
    """Cálculo compressível isotérmico para tubo dado."""
    svc = inp.service
    if svc not in VALID_SERVICES:
        raise WrongEngineError("hydraulic_compressible", svc, "hydraulic_incompressible or other")

    mdot = _mass_flow_kgs(inp.flow_rate, inp.flow_rate_basis, fluid)
    D_m = pipe.ID_m
    A_m2 = math.pi / 4.0 * D_m**2

    # Propriedades do gás
    rho1 = fluid.rho_kgm3
    P1_pa = fluid.P_pa
    T_K = fluid.T_K
    gamma = fluid.gamma or 1.4
    mw = fluid.molecular_weight_kgkmol or 29.0
    R_specific = R_UNIVERSAL * 1000.0 / mw  # J/(kg·K)
    a_sound = math.sqrt(gamma * R_specific * T_K)  # velocidade do som

    # Velocidade e Mach na secção 1
    v1 = mdot / (rho1 * A_m2)
    Ma1 = v1 / a_sound

    warnings: list[str] = []
    status = "CALCULATED"

    if Ma1 > MA_LIMIT:
        warnings.append(
            f"Ma = {Ma1:.3f} > {MA_LIMIT} — modelo isotérmico pode subestimar ΔP. "
            f"Verificar adequação do modelo. Considerando continuar com Ma elevado."
        )
        if Ma1 > 0.8:
            return HydraulicResult(
                regime="compressible_gas",
                service=svc,
                line_tag=inp.line_tag,
                mach_number=Ma1,
                status="OUT_OF_SCOPE",
                warnings=[
                    f"Ma = {Ma1:.3f} >> 0.3 — modelo isotérmico inválido para regime sónico. "
                    "Usar modelo Fanno completo ou software especializado."
                ],
                compressible_model_valid=False,
            )

    # Rugosidade
    eps = roughness_m or inp.roughness_m or 0.046e-3
    eps_D = eps / D_m

    # Atrito
    Re = rho1 * v1 * D_m / fluid.mu_pas
    f = _colebrook_white(Re, eps_D)

    # Comprimento equivalente de fittings (ΔP_minor por Le/D equivalente)
    K_total, k_warnings = calculate_total_k(inp.fittings, inp.valves)
    warnings.extend(k_warnings)
    Le_equiv_m = K_total * D_m / f  # Le = K*D/f

    L_total = inp.line_length_m + Le_equiv_m

    # Equação de Weymouth/isotérmico simplificado:
    # P1² - P2² = (f * L * ρ1 * v1² * P1) / (D * R_specific * T_K) × (2 P1/ρ1)
    # Forma compacta (derivada de integração isotérmica):
    # P1² - P2² = f * (L/D) * G² * R * T / (M_mol/1000)  [onde G = mdot/A = fluxo mássico]
    # → P2² = P1² - f*(L/D)*(mdot/A)²*(R_specific*T_K)

    G = mdot / A_m2  # fluxo mássico [kg/(m²·s)]
    # Para escoamento isotérmico: P1² - P2² = f*(L/D)*G²*(R_specific*T_K)
    P2_sq = P1_pa**2 - f * (L_total / D_m) * G**2 * R_specific * T_K

    if P2_sq <= 0:
        warnings.append("P2² ≤ 0: linha demasiado longa ou caudal demasiado alto para as condições dadas")
        status = "OUT_OF_SCOPE"
        return HydraulicResult(
            regime="compressible_gas",
            service=svc,
            line_tag=inp.line_tag,
            mach_number=Ma1,
            status=status,
            warnings=warnings,
            compressible_model_valid=False,
        )

    P2_pa = math.sqrt(P2_sq)
    dp_pa = P1_pa - P2_pa

    pressure_ratio = P2_pa / P1_pa
    if pressure_ratio < PRESSURE_RATIO_LIMIT:
        warnings.append(
            f"P2/P1 = {pressure_ratio:.3f} < {PRESSURE_RATIO_LIMIT} — "
            f"queda de pressão excessiva. Modelo isotérmico pode ser impreciso."
        )
        status = "OUT_OF_SCOPE"

    # Velocidade na saída (P2, ρ2 = P2*M/(R*T))
    rho2 = P2_pa / (R_specific * T_K)
    v2 = mdot / (rho2 * A_m2)
    Ma2 = v2 / a_sound

    # ΔP elevação (componente estática)
    dp_elevation_pa = rho1 * 9.80665 * inp.elevation_delta_m

    dp_total_pa = dp_pa + dp_elevation_pa

    model_valid = (Ma1 <= MA_LIMIT and pressure_ratio >= PRESSURE_RATIO_LIMIT)
    if not model_valid and status == "CALCULATED":
        status = "WARNING"

    return HydraulicResult(
        regime="compressible_gas",
        service=svc,
        line_tag=inp.line_tag,
        velocity_ms=v1,
        Re=Re,
        friction_factor=f,
        dp_major_pa=dp_pa,
        dp_minor_pa=0.0,
        dp_total_pa=dp_total_pa,
        dp_total_bar=pa_to_bar(dp_total_pa),
        mach_number=Ma1,
        pressure_ratio=pressure_ratio,
        compressible_model_valid=model_valid,
        pipe_used=pipe,
        status=status,
        warnings=warnings,
        assumptions_used=["A-HC-001", "A-HC-004"],
    )


def select_dn(
    inp: LineInput,
    fluid: FluidProperties,
    v_max: float = 15.0,
    allowable_dp_bar: float | None = None,
    catalog: str = "ASME_B36_10M",
    schedule: str = "SCH40",
    roughness_m: float | None = None,
) -> HydraulicResult:
    """Selecciona DN para escoamento compressível."""
    mdot = _mass_flow_kgs(inp.flow_rate, inp.flow_rate_basis, fluid)
    A_min = mdot / (fluid.rho_kgm3 * v_max)
    D_min = math.sqrt(4.0 * A_min / math.pi)

    dns = get_available_dns(catalog)
    DN_by_velocity = None
    DN_by_dp = None

    for dn in sorted(dns):
        try:
            pipe = get_pipe_dimension(catalog, dn, schedule)
        except Exception:
            continue
        if pipe.ID_m >= D_min:
            DN_by_velocity = dn
            break

    if allowable_dp_bar is not None:
        for dn in sorted(dns):
            try:
                pipe = get_pipe_dimension(catalog, dn, schedule)
                res = calculate_compressible(inp, fluid, pipe, roughness_m)
                if (res.dp_total_bar is not None and
                        res.dp_total_bar <= allowable_dp_bar and
                        res.status not in ("OUT_OF_SCOPE",)):
                    DN_by_dp = dn
                    break
            except Exception:
                continue

    DN_governing = None
    governing_criterion = "velocity"
    if DN_by_velocity and DN_by_dp:
        DN_governing = max(DN_by_velocity, DN_by_dp)
        governing_criterion = "velocity" if DN_governing == DN_by_velocity else "pressure_drop"
    elif DN_by_velocity:
        DN_governing = DN_by_velocity
    elif DN_by_dp:
        DN_governing = DN_by_dp
        governing_criterion = "pressure_drop"
    else:
        return HydraulicResult(
            regime="compressible_gas",
            service=inp.service,
            line_tag=inp.line_tag,
            status="OUT_OF_SCOPE",
            warnings=["Não foi possível seleccionar DN para as condições dadas"],
        )

    pipe_final = get_pipe_dimension(catalog, DN_governing, schedule)
    result = calculate_compressible(inp, fluid, pipe_final, roughness_m)
    result.DN_by_velocity_mm = DN_by_velocity
    result.DN_by_pressure_drop_mm = DN_by_dp
    result.DN_governing_mm = DN_governing
    result.governing_criterion = governing_criterion
    return result
