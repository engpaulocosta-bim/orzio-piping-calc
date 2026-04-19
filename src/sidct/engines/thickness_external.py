"""Verificação de espessura por pressão externa / colapso.

Aplicável a: vacuum_utility (e qualquer linha sujeita a pressão externa).

REGRA ABSOLUTA: nunca reutilizar fórmula de pressão interna com sinal invertido.
O problema de colapso é fundamentalmente diferente (instabilidade geométrica).

Status desta implementação:
- Fórmula de Lamé para colapso elástico: implementada (domínio público)
- Método ASME (charts L/D vs Do/t, Fig. G): requer dataset externo (DATASET_MISSING)
- Método Windenburg-Trilling (curto/longo): implementado como alternativa
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, ExternalPressureResult, PipeDimension
from ..units import bar_to_pa, pa_to_bar, mpa_to_pa, pa_to_mpa

logger = logging.getLogger("sidct.thickness_external")

# Módulo de elasticidade E [MPa] para aço
E_STEEL_MPA = 200_000.0
# Coeficiente de Poisson ν para aço
NU_STEEL = 0.3


def _p_collapse_lame(OD_mm: float, ID_mm: float, E_mpa: float = E_STEEL_MPA,
                     nu: float = NU_STEEL) -> float:
    """Pressão de colapso elástico de Lamé para cilindro de parede espessa [MPa].

    P_cr = 2E * (t/D)^3 / (1 - ν²) — aproximação cilindro fino
    Valida para t/D < 0.1. Para t/D > 0.1: usar fórmula de parede espessa.
    """
    t_mm = (OD_mm - ID_mm) / 2.0
    D_mm = OD_mm
    ratio = t_mm / D_mm
    # Fórmula de colapso elástico (cilindro fino)
    P_cr = 2.0 * E_mpa * ratio**3 / (1.0 - nu**2)
    return P_cr  # MPa


def _p_collapse_windenburg(OD_mm: float, wt_mm: float, L_mm: float,
                             E_mpa: float = E_STEEL_MPA, nu: float = NU_STEEL) -> float:
    """Windenburg-Trilling (1934) — pressão crítica de colapso.

    Para tubos longos: P_cr = 2E * (t/Do)^3 / (1-ν²)
    Para tubos curtos: inclui efeito do comprimento.
    """
    D_o = OD_mm
    t = wt_mm
    L = L_mm

    # Razão L/D e t/D
    L_D = L / D_o
    t_D = t / D_o

    if L_D > 20:
        # Tubo longo — fórmula cilindro infinito
        P_cr = 2.0 * E_mpa * (t_D)**3 / (1.0 - nu**2)
    else:
        # Windenburg-Trilling generalizado (aproximação)
        n_min = max(2, int(math.pi * D_o / L + 0.5))  # modo de colapso estimado
        # Pressão crítica pelo modo n
        alpha = n_min**2 - 1.0
        beta = (n_min * math.pi * D_o / (2.0 * L))**2
        P_cr = (E_mpa * (t_D)**3 / (4.0 * (1.0 - nu**2))) * (
            alpha + beta)**2 / (alpha * (1.0 + beta)**2)

    return P_cr  # MPa


def calculate_external_pressure(
    inp: LineInput,
    pipe: PipeDimension,
    P_external_bar: float | None = None,
    safety_factor: float = 3.0,
    E_mpa: float = E_STEEL_MPA,
    nu: float = NU_STEEL,
) -> ExternalPressureResult:
    """
    Verifica resistência ao colapso por pressão externa.

    safety_factor: factor de segurança sobre P_cr elástico.
    Tipicamente 3.0 (ASME) — conservativo.
    """
    if inp.service != "vacuum_utility":
        return ExternalPressureResult(
            line_tag=inp.line_tag,
            method_status="NOT_APPLICABLE",
            warnings=["Verificação de pressão externa apenas aplicável a vacuum_utility"],
        )

    # Pressão externa de projecto
    if P_external_bar is not None:
        P_ext_bar = P_external_bar
    else:
        # Vácuo completo: P_ext = P_atm
        from ..units import P_ATM_PA, pa_to_bar
        P_ext_bar = pa_to_bar(P_ATM_PA)  # ≈ 1.01325 bar

    P_ext_mpa = P_ext_bar / 10.0

    OD_mm = pipe.OD_mm
    ID_mm = pipe.ID_mm
    wt_mm = pipe.wall_thickness_mm
    L_mm = inp.line_length_m * 1000.0  # m → mm

    warnings: list[str] = []
    required_data: list[str] = []

    # Verificar regime elástico vs plástico
    # t/D para escoamento plástico
    t_D = wt_mm / OD_mm
    if t_D > 0.10:
        warnings.append(
            f"t/D = {t_D:.3f} > 0.10 — parede espessa. "
            "Usar fórmula de parede espessa para maior precisão."
        )

    # Cálculo de P_cr por Windenburg-Trilling
    P_cr_mpa = _p_collapse_windenburg(OD_mm, wt_mm, L_mm, E_mpa, nu)

    # Pressão admissível (com factor de segurança)
    P_allow_mpa = P_cr_mpa / safety_factor
    P_allow_bar = P_allow_mpa * 10.0

    utilization = P_ext_mpa / P_allow_mpa

    # Status
    if utilization > 1.0:
        collapse_warning = (
            f"COLAPSO PROVÁVEL: P_ext = {P_ext_bar:.3f} bar > P_allow = {P_allow_bar:.3f} bar "
            f"(P_cr/{safety_factor:.0f}). Aumentar espessura ou adicionar stiffeners."
        )
        status = "CRITICAL"
    elif utilization > 0.8:
        collapse_warning = (
            f"Margem reduzida: P_ext/P_allow = {utilization:.2f}. Verificar cuidadosamente."
        )
        status = "WARNING"
    else:
        collapse_warning = f"OK: P_ext/P_allow = {utilization:.2f} < 1.0"
        status = "APPROVED"

    warnings.append(
        f"AVISO: Método Windenburg-Trilling (1934) — aproximação de domínio público. "
        f"Para projeto definitivo: usar charts ASME UG-28 / ASME B31.3 App. D ou software FEA."
    )
    warnings.append(
        f"Factor de segurança aplicado: {safety_factor:.1f} sobre P_cr elástico."
    )
    required_data.append("Dataset ASME Fig. G (charts L/D vs Do/t) para método rigoroso ASME")
    required_data.append("EN 13480-3 Sec. 8 para método EN")

    return ExternalPressureResult(
        line_tag=inp.line_tag,
        P_external_design_bar=P_ext_bar,
        P_allow_bar=P_allow_bar,
        utilization_ratio=utilization,
        collapse_warning=collapse_warning,
        method_status=status,
        required_additional_data=required_data,
        warnings=warnings,
    )
