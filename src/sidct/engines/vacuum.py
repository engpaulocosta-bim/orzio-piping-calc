"""Motor de vácuo — condutância + encaminhamento para external pressure check.

Aplicável a: vacuum_utility.

REGRA: toda linha de vácuo DEVE ser encaminhada para external_pressure_check.
Nunca aprovar linha de vácuo sem verificação de colapso.
"""
from __future__ import annotations
import math
import logging
from ..models import LineInput, FluidProperties, HydraulicResult, PipeDimension
from ..exceptions import MissingInputError, ExternalPressureRequiredError
from ..units import P_ATM_PA, pa_to_bar, bar_to_pa

logger = logging.getLogger("sidct.vacuum")

VALID_SERVICES = {"vacuum_utility"}
KN_VISCOUS_LIMIT = 0.01  # Knudsen number limit for viscous regime


def calculate_vacuum(
    inp: LineInput,
    fluid: FluidProperties,
    pipe: PipeDimension,
) -> HydraulicResult:
    """
    Calcula condutância da linha de vácuo em regime viscoso.
    Encaminha obrigatoriamente para external_pressure_check.
    """
    if inp.service not in VALID_SERVICES:
        raise ValueError(f"Serviço '{inp.service}' não é vacuum_utility")

    if inp.vacuum_target_mbara is None:
        raise MissingInputError("vacuum_target_mbara", "vacuum_utility")

    P_target_pa = inp.vacuum_target_mbara * 100.0  # mbar → Pa
    P_atm_pa = P_ATM_PA
    D_m = pipe.ID_m
    L_m = inp.line_length_m
    T_K = fluid.T_K
    mu = fluid.mu_pas
    warnings: list[str] = []

    # Número de Knudsen (estimativa para ar)
    # Kn = lambda / D, onde lambda = mean free path
    # lambda ≈ kT/(sqrt(2)*pi*d²*P), d = 3.7e-10 m para N2/ar
    k_B = 1.380649e-23
    d_mol = 3.7e-10
    P_mean = (P_atm_pa + P_target_pa) / 2.0
    lambda_mfp = k_B * T_K / (math.sqrt(2) * math.pi * d_mol**2 * P_mean)
    Kn = lambda_mfp / D_m

    if Kn > KN_VISCOUS_LIMIT:
        warnings.append(
            f"Kn = {Kn:.4f} > {KN_VISCOUS_LIMIT} — regime pode ser molecular ou transição. "
            f"Modelo viscoso pode subestimar resistência ao escoamento."
        )
        if Kn > 1.0:
            return HydraulicResult(
                regime="vacuum_conductance",
                service=inp.service,
                line_tag=inp.line_tag,
                status="OUT_OF_SCOPE",
                warnings=warnings + [
                    f"Kn = {Kn:.2f} >> 1 — regime molecular. Modelo viscoso inválido. "
                    "Usar equações de Knudsen para condutância molecular."
                ],
                conductance_result={
                    "external_pressure_check_required": True,
                    "P_external_bar": pa_to_bar(P_atm_pa),
                },
            )

    # Condutância viscosa para tubo circular (Hagen-Poiseuille regime viscoso)
    # C = pi * D^4 * P_mean / (128 * mu * L) [m³·Pa/s / Pa = m³/s]
    C_viscous = (math.pi * D_m**4 * P_mean) / (128.0 * mu * L_m)  # m³/s

    # Fluxo de throughput Q [Pa·m³/s]
    delta_P = P_atm_pa - P_target_pa
    Q_throughput = C_viscous * delta_P  # Pa·m³/s (throughput)

    # Pressão na entrada do sistema de vácuo
    # P2 = P1 - Q/C (P1 = P_atm, P2 = pressão resultante na câmara)
    P2_pa = P_atm_pa - Q_throughput / C_viscous

    warnings.append(
        "AVISO OBRIGATÓRIO: Esta linha de vácuo requer verificação de pressão externa/colapso. "
        "Ver secção external_pressure_check no relatório."
    )

    return HydraulicResult(
        regime="vacuum_conductance",
        service=inp.service,
        line_tag=inp.line_tag,
        velocity_ms=None,
        dp_total_pa=delta_P,
        dp_total_bar=pa_to_bar(delta_P),
        pipe_used=pipe,
        status="CALCULATED",
        warnings=warnings,
        assumptions_used=["A-VAC-001", "A-VAC-002"],
        conductance_result={
            "C_viscous_m3s": C_viscous,
            "Q_throughput_pa_m3s": Q_throughput,
            "Kn": Kn,
            "P_target_pa": P_target_pa,
            "P_target_mbar_abs": inp.vacuum_target_mbara,
            "P_mean_pa": P_mean,
            "external_pressure_check_required": True,
            "P_external_bar": pa_to_bar(P_atm_pa),
        },
    )
