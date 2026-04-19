"""Motor hidráulico incompressível — Darcy-Weisbach + Colebrook-White.

Aplicável a: potable_water, service_water, osmotized_water,
             chilled_water, condenser_water, fire_water.

NUNCA usar para: compressed_air, natural_gas, sanitary_drainage,
                 rainwater, vacuum_utility.
"""
from __future__ import annotations
import math
import logging
from ..models import (LineInput, FluidProperties, HydraulicResult, PipeDimension,
                      FittingItem, ValveItem)
from ..catalogs.pipe_dimension_catalog import (
    get_available_dns, get_pipe_dimension, find_minimum_schedule
)
from ..catalogs.fitting_k_catalog import calculate_total_k
from ..units import m3h_to_m3s, ls_to_m3s, gpm_to_m3s, bar_to_pa, pa_to_bar, G_GRAVITY
from ..exceptions import (OutOfScopeError, WrongEngineError, ConvergenceError,
                           ValidationError)

logger = logging.getLogger("sidct.hydraulic_incompressible")

VALID_SERVICES = {
    "potable_water", "service_water", "osmotized_water",
    "chilled_water", "condenser_water", "fire_water",
}
GRAVITY_SERVICES = {"sanitary_drainage", "rainwater"}
COMPRESSIBLE_SERVICES = {"compressed_air", "natural_gas"}

_MAX_ITER = 200
_TOL = 1e-8


def _colebrook_white(Re: float, eps_D: float) -> float:
    """Resolve Colebrook-White para f (factor Darcy). Iteração Newton-Raphson."""
    if Re < 2300:
        return 64.0 / Re  # Hagen-Poiseuille

    # Estimativa inicial Swamee-Jain
    f = 0.25 / (math.log10(eps_D / 3.7 + 5.74 / Re**0.9))**2

    for _ in range(_MAX_ITER):
        lhs = -2.0 * math.log10(eps_D / 3.7 + 2.51 / (Re * math.sqrt(f)))
        f_new = (1.0 / lhs)**2
        if abs(f_new - f) < _TOL:
            return f_new
        f = f_new

    raise ConvergenceError("Colebrook-White", _MAX_ITER, _TOL)


def _flow_rate_m3s(flow_rate: float, basis: str) -> float:
    b = basis.lower().replace(" ", "").replace("/", "").replace("_", "")
    if b in ("m3/s", "m3s"):
        return flow_rate
    if b in ("m3/h", "m3h"):
        return m3h_to_m3s(flow_rate)
    if b in ("l/s", "ls"):
        return ls_to_m3s(flow_rate)
    if b == "gpm":
        return gpm_to_m3s(flow_rate)
    raise ValidationError(f"Unidade de caudal '{basis}' não suportada para líquidos", "flow_rate_basis")


def calculate_for_pipe(
    inp: LineInput,
    fluid: FluidProperties,
    pipe: PipeDimension,
    roughness_m: float | None = None,
) -> HydraulicResult:
    """Calcula hidráulica para um tubo específico."""
    svc = inp.service
    if svc in GRAVITY_SERVICES:
        raise WrongEngineError("hydraulic_incompressible", svc, "hydraulic_gravity")
    if svc in COMPRESSIBLE_SERVICES:
        raise WrongEngineError("hydraulic_incompressible", svc, "hydraulic_compressible")
    if svc not in VALID_SERVICES:
        raise WrongEngineError("hydraulic_incompressible", svc, "hydraulic_incompressible or other")

    Q_m3s = _flow_rate_m3s(inp.flow_rate, inp.flow_rate_basis)
    D_m = pipe.ID_m
    A_m2 = math.pi / 4.0 * D_m**2

    v = Q_m3s / A_m2  # velocidade [m/s]
    Re = fluid.rho_kgm3 * v * D_m / fluid.mu_pas

    # Rugosidade
    if roughness_m is not None:
        eps = roughness_m
    elif inp.roughness_m is not None:
        eps = inp.roughness_m
    else:
        eps = 0.046e-3  # aço carbono novo (default)
    eps_D = eps / D_m

    f = _colebrook_white(Re, eps_D)

    # Perda de carga Darcy-Weisbach
    dp_major_pa = f * (inp.line_length_m / D_m) * (fluid.rho_kgm3 * v**2 / 2.0)
    head_major_m = dp_major_pa / (fluid.rho_kgm3 * G_GRAVITY)

    # Perdas menores (K-method)
    K_total, k_warnings = calculate_total_k(inp.fittings, inp.valves)
    dp_minor_pa = K_total * fluid.rho_kgm3 * v**2 / 2.0

    # Pressão estática (elevação)
    dp_elevation_pa = fluid.rho_kgm3 * G_GRAVITY * inp.elevation_delta_m

    dp_total_pa = dp_major_pa + dp_minor_pa + dp_elevation_pa
    head_loss_m = dp_total_pa / (fluid.rho_kgm3 * G_GRAVITY)

    warnings: list[str] = list(k_warnings)

    # Verificação envelope
    if Re < 1000:
        warnings.append(f"Re = {Re:.0f} < 1000 — escoamento laminar incipiente, verificar condições")
    if Re > 1e8:
        warnings.append(f"Re = {Re:.2e} — fora do envelope validado (Re > 1e8)")

    # Verificação de incompressibilidade (ΔP/P < 10%)
    dp_pct = (dp_total_pa / (bar_to_pa(inp.P_oper_bar))) * 100.0
    if dp_pct > 10.0:
        warnings.append(
            f"ΔP/P = {dp_pct:.1f}% > 10% — confirmar que fluido é incompressível e "
            f"pressão dinâmica é desprezável"
        )

    return HydraulicResult(
        regime="pressurized_incompressible",
        service=svc,
        line_tag=inp.line_tag,
        velocity_ms=v,
        Re=Re,
        friction_factor=f,
        dp_major_pa=dp_major_pa,
        dp_minor_pa=dp_minor_pa,
        dp_total_pa=dp_total_pa,
        dp_total_bar=pa_to_bar(dp_total_pa),
        head_loss_m=head_loss_m,
        pipe_used=pipe,
        status="CALCULATED",
        warnings=warnings,
        assumptions_used=["A-HI-001", "A-HI-002", "A-HI-003", "A-HI-004"],
    )


def select_dn(
    inp: LineInput,
    fluid: FluidProperties,
    v_min: float,
    v_max: float,
    allowable_dp_bar: float | None = None,
    catalog: str = "ASME_B36_10M",
    schedule: str = "SCH40",
    roughness_m: float | None = None,
) -> HydraulicResult:
    """Selecciona DN por critério de velocidade e/ou queda de pressão."""
    Q_m3s = _flow_rate_m3s(inp.flow_rate, inp.flow_rate_basis)

    # DN por velocidade máxima: A = Q/v_max → D = sqrt(4A/π)
    D_min_by_v = math.sqrt(4.0 * Q_m3s / (math.pi * v_max))
    ID_min_by_v_mm = D_min_by_v * 1000.0

    dns = get_available_dns(catalog)
    warnings: list[str] = []
    DN_by_velocity = None
    DN_by_dp = None

    # Selecção por velocidade
    for dn in sorted(dns):
        try:
            pipe = get_pipe_dimension(catalog, dn, schedule)
        except Exception:
            continue
        if pipe.ID_m >= D_min_by_v:
            v = Q_m3s / (math.pi / 4.0 * pipe.ID_m**2)
            if v_min <= v <= v_max:
                DN_by_velocity = dn
                break
    if DN_by_velocity is None:
        for dn in sorted(dns):
            try:
                pipe = get_pipe_dimension(catalog, dn, schedule)
                if pipe.ID_m >= D_min_by_v:
                    DN_by_velocity = dn
                    break
            except Exception:
                continue

    # Selecção por queda de pressão
    if allowable_dp_bar is not None:
        for dn in sorted(dns):
            try:
                pipe = get_pipe_dimension(catalog, dn, schedule)
                res = calculate_for_pipe(inp, fluid, pipe, roughness_m)
                if res.dp_total_bar is not None and res.dp_total_bar <= allowable_dp_bar:
                    DN_by_dp = dn
                    break
            except Exception:
                continue

    # DN governante: maior dos dois critérios
    DN_governing = None
    governing_criterion = "velocity"
    if DN_by_velocity is not None and DN_by_dp is not None:
        DN_governing = max(DN_by_velocity, DN_by_dp)
        governing_criterion = "velocity" if DN_governing == DN_by_velocity else "pressure_drop"
    elif DN_by_velocity is not None:
        DN_governing = DN_by_velocity
    elif DN_by_dp is not None:
        DN_governing = DN_by_dp
        governing_criterion = "pressure_drop"
    else:
        warnings.append("Não foi possível seleccionar DN — verificar entradas")
        return HydraulicResult(
            regime="pressurized_incompressible",
            service=inp.service,
            line_tag=inp.line_tag,
            status="OUT_OF_SCOPE",
            warnings=["DN não seleccionado — verifique os critérios de velocidade e ΔP"],
        )

    # Calcular resultado com DN governante
    try:
        pipe_final = get_pipe_dimension(catalog, DN_governing, schedule)
        result = calculate_for_pipe(inp, fluid, pipe_final, roughness_m)
        result.DN_by_velocity_mm = DN_by_velocity
        result.DN_by_pressure_drop_mm = DN_by_dp
        result.DN_governing_mm = DN_governing
        result.governing_criterion = governing_criterion
        result.warnings.extend(warnings)
    except Exception as e:
        return HydraulicResult(
            regime="pressurized_incompressible",
            service=inp.service,
            line_tag=inp.line_tag,
            status="OUT_OF_SCOPE",
            warnings=[str(e)],
        )
    return result
