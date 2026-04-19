"""Cálculo preliminar de suportes.

CLASSIFICAÇÃO: Ferramenta preliminar / semi-detalhada.
NÃO substitui análise completa de flexibilidade e tensões.

Calcula:
- Peso por metro (tubo + fluido + isolação)
- Vão máximo por flecha admissível
- Carga sísmica horizontal paramétrica
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, FluidProperties, SupportResult, PipeDimension
from ..units import G_GRAVITY

logger = logging.getLogger("sidct.supports")

# Densidades típicas [kg/m³]
FLUID_DENSITY_DEFAULTS: dict[str, float] = {
    "compressed_air": 10.0,      # ~ ar a 7 barg
    "natural_gas": 7.0,
    "potable_water": 1000.0,
    "service_water": 1000.0,
    "osmotized_water": 1000.0,
    "chilled_water": 1000.0,
    "condenser_water": 1000.0,
    "vacuum_utility": 0.1,       # vácuo ~ ar rarefeito
    "sanitary_drainage": 1000.0,
    "rainwater": 1000.0,
    "fire_water": 1000.0,
}

# Deflexão admissível típica [mm/m de comprimento] — referência
DEFLECTION_LIMIT_MM_M = 2.0  # 2 mm/m — critério conservativo

# Módulo de elasticidade do aço [Pa]
E_STEEL_PA = 200e9

# Momento de inércia de secção anular I = π/64*(OD^4 - ID^4)
def _moment_of_inertia_m4(OD_m: float, ID_m: float) -> float:
    return math.pi / 64.0 * (OD_m**4 - ID_m**4)


def calculate_supports(
    inp: LineInput,
    fluid: FluidProperties,
    pipe: PipeDimension,
    max_deflection_mm_m: float = DEFLECTION_LIMIT_MM_M,
    seismic_factor_g: float = 0.1,
    E_steel_pa: float = E_STEEL_PA,
) -> SupportResult:
    """Calcula suportes preliminares."""
    warnings: list[str] = []
    assumptions: list[str] = ["A-SUP-001", "A-SUP-002", "A-SUP-003"]

    # Peso por metro
    w_pipe = pipe.weight_kgm  # kg/m
    rho_fluid = fluid.rho_kgm3 if fluid.rho_kgm3 > 0 else FLUID_DENSITY_DEFAULTS.get(inp.service, 1000.0)
    A_fluid = math.pi / 4.0 * pipe.ID_m**2
    w_fluid = rho_fluid * A_fluid  # kg/m

    # Isolação (casca cilíndrica)
    w_insul = 0.0
    if inp.insulation_thickness_mm > 0:
        t_ins = inp.insulation_thickness_mm / 1000.0
        OD_ins = pipe.OD_m + 2 * t_ins
        A_ins = math.pi / 4.0 * (OD_ins**2 - pipe.OD_m**2)
        rho_ins = inp.insulation_density_kgm3
        w_insul = rho_ins * A_ins  # kg/m

    w_total = w_pipe + w_fluid + w_insul  # kg/m

    # Carga distribuída [N/m]
    q = w_total * G_GRAVITY

    # Vão máximo por deflexão admissível (viga biapoiada, carga distribuída)
    # δ_max = 5*q*L^4 / (384*E*I)  → L_max = (384*E*I*δ_max / (5*q))^(1/4)
    I_m4 = _moment_of_inertia_m4(pipe.OD_m, pipe.ID_m)
    delta_max_m = max_deflection_mm_m / 1000.0 * inp.line_length_m  # δ = f * L

    if q > 0 and I_m4 > 0:
        # δ_max = max_deflection_mm_m/1000 * L_max  → substitui na equação
        # L_max^5 = 384 * E * I * (delta_per_L * L) / (5 * q)
        # L_max = (384 * E * I * delta_per_m / (5 * q))^(1/4)
        delta_per_m = max_deflection_mm_m / 1000.0  # m/m
        L_max_m = (384.0 * E_steel_pa * I_m4 * delta_per_m / (5.0 * q))**0.25
    else:
        L_max_m = None
        warnings.append("Não foi possível calcular vão máximo — verificar entradas de carga")

    # Deflexão governante
    if L_max_m:
        deflection_governing = f"δ/L ≤ {max_deflection_mm_m:.1f} mm/m (critério de projecto)"
    else:
        deflection_governing = "N/A"

    # Carga sísmica horizontal
    if L_max_m:
        mass_per_span = w_total * L_max_m  # kg
        F_seismic_N = mass_per_span * G_GRAVITY * seismic_factor_g
        F_seismic_kN = F_seismic_N / 1000.0
    else:
        F_seismic_kN = None

    if seismic_factor_g == 0.1:
        warnings.append(
            f"Factor sísmico padrão: {seismic_factor_g}g. "
            "Substituir por factor local conforme zonamento sísmico."
        )

    warnings.append("AVISO: Cálculo de suportes classificado como PRELIMINAR. "
                    "Não substituir análise de flexibilidade e tensões.")

    return SupportResult(
        line_tag=inp.line_tag,
        weight_pipe_kgm=w_pipe,
        weight_fluid_kgm=w_fluid,
        weight_insulation_kgm=w_insul,
        total_weight_kgm=w_total,
        L_max_m=L_max_m,
        deflection_governing=deflection_governing,
        seismic_horizontal_kN=F_seismic_kN,
        classification_level="PRELIMINARY",
        warnings=warnings,
        assumptions_used=assumptions,
    )
