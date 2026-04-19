"""Validação de entradas do sistema SIDCT."""
from __future__ import annotations
from typing import Any
from .enums import (Service, ProjectProfile, DimensionalCatalog,
                    MaterialFamily, FlowRateBasis, DesignCode)
from .exceptions import (ValidationError, MissingInputError, OutOfScopeError,
                          CodeMismatchError, WrongEngineError)
from .models import LineInput


GRAVITY_SERVICES = {Service.SANITARY_DRAINAGE, Service.RAINWATER}
COMPRESSIBLE_SERVICES = {Service.COMPRESSED_AIR, Service.NATURAL_GAS}
VACUUM_SERVICES = {Service.VACUUM_UTILITY}
STAINLESS_MATERIALS = {"a312", "a358", "316l", "304l", "316", "304", "tp304", "tp316"}
CARBON_MATERIALS = {"a106", "a53", "a333", "a335", "a106grb", "a53grb"}


def validate_line_input(inp: LineInput) -> list[str]:
    """Valida dados de entrada. Retorna lista de warnings (vazia = OK)."""
    warnings: list[str] = []

    # Pressão e temperatura
    if inp.P_design_bar < inp.P_oper_bar:
        raise ValidationError(
            f"P_design ({inp.P_design_bar} barg) deve ser >= P_oper ({inp.P_oper_bar} barg)",
            "P_design_bar"
        )
    if inp.T_design_c < inp.T_oper_c:
        warnings.append(f"T_design ({inp.T_design_c}°C) < T_oper ({inp.T_oper_c}°C) — verificar")

    if inp.P_design_bar < 0:
        raise ValidationError("P_design_bar deve ser >= 0 (barg)", "P_design_bar")

    if inp.T_design_c < -200 or inp.T_design_c > 800:
        raise OutOfScopeError(
            "Temperatura de projeto fora do envelope suportado [-200, 800]°C",
            "T_design_c", inp.T_design_c, "[-200, 800]"
        )

    # Caudal
    if inp.flow_rate <= 0:
        raise ValidationError("flow_rate deve ser > 0", "flow_rate")

    # Comprimento
    if inp.line_length_m <= 0:
        raise ValidationError("line_length_m deve ser > 0", "line_length_m")

    # Serviços gravitários
    svc = inp.service
    if svc in (Service.SANITARY_DRAINAGE.value, Service.RAINWATER.value):
        if inp.slope_mm_m is None or inp.slope_mm_m <= 0:
            raise MissingInputError("slope_mm_m", svc)
        if inp.slope_mm_m < 0.5:
            warnings.append(f"slope {inp.slope_mm_m} mm/m muito baixo — risco de sedimentação")
        if inp.slope_mm_m > 100:
            warnings.append(f"slope {inp.slope_mm_m} mm/m muito alto — verificar erosão")

    # Vácuo
    if svc == Service.VACUUM_UTILITY.value:
        if inp.vacuum_target_mbara is None:
            raise MissingInputError("vacuum_target_mbara", svc)
        if inp.vacuum_target_mbara <= 0:
            raise ValidationError("vacuum_target_mbara deve ser > 0 mbar abs", "vacuum_target_mbara")

    # Catálogo vs material
    mat_lower = inp.material.lower().replace(" ", "").replace("-", "")
    is_stainless = any(k in mat_lower for k in STAINLESS_MATERIALS)
    catalog = inp.dimensional_catalog

    if is_stainless and catalog == DimensionalCatalog.ASME_B36_10M.value:
        raise CodeMismatchError(
            "ASME_B36_10M",
            "ASME_B36_19M",
            f"Material '{inp.material}' identificado como inox — deve usar B36.19M"
        )

    # Corrosion allowance
    if inp.corrosion_allowance_mm is not None and inp.corrosion_allowance_mm < 0:
        raise ValidationError("corrosion_allowance_mm deve ser >= 0", "corrosion_allowance_mm")
    if inp.corrosion_allowance_mm == 0.0 and not is_stainless:
        warnings.append("CA = 0 para aço carbono — confirmar política de corrosão do projecto")

    # Mode check
    if inp.operation_mode == "check_received":
        if inp.DN_received_mm is None:
            warnings.append("Modo check_received sem DN_received_mm — apenas cálculo será feito")
        if inp.schedule_or_wall_received is None:
            warnings.append("Modo check_received sem schedule_or_wall_received — espessura não será verificada")

    return warnings


def validate_profile_service_compatibility(profile: str, service: str) -> list[str]:
    """Verifica compatibilidade perfil × serviço. Retorna warnings."""
    warnings: list[str] = []

    dc_only_services = {Service.CHILLED_WATER.value, Service.CONDENSER_WATER.value}
    industrial_only = {Service.COMPRESSED_AIR.value, Service.NATURAL_GAS.value,
                       Service.OSMOTIZED_WATER.value}

    if service in dc_only_services and profile in (
        ProjectProfile.GLASS_FACTORY_EU.value,
        ProjectProfile.GLASS_FACTORY_US.value
    ):
        warnings.append(
            f"Serviço '{service}' é tipicamente de building services — "
            f"verifique se perfil '{profile}' é o correcto"
        )

    if (service in industrial_only and
            profile in (ProjectProfile.DATACENTRE_EU.value, ProjectProfile.DATACENTRE_US.value)):
        warnings.append(
            f"Serviço '{service}' é tipicamente industrial — "
            f"verifique se perfil '{profile}' é o correcto"
        )

    return warnings


def validate_pressure_design_limits(P_design_bar: float, profile: str) -> list[str]:
    """Verifica P_design contra limites do perfil."""
    warnings: list[str] = []
    b31_9_profiles = {ProjectProfile.DATACENTRE_EU.value, ProjectProfile.DATACENTRE_US.value}

    if profile in b31_9_profiles and P_design_bar > 20.7:
        warnings.append(
            f"P_design {P_design_bar} barg excede limite B31.9 (20.7 barg) — "
            f"considerar B31.3 ou EN 13480"
        )
    return warnings
