"""Selector — consolida DN comercial e parede recomendados.

Critérios (por ordem):
1. Técnica (velocidade + ΔP + espessura + vácuo)
2. Comercialidade (schedule padrão preferencial)
3. Conservadorismo (margem mínima configurável)
4. Preferência do perfil
"""
from __future__ import annotations
import logging
from ..models import (LineInput, FluidProperties, HydraulicResult,
                       ThicknessResult, ExternalPressureResult, ReportContext,
                       WarningItem)
from ..catalogs.pipe_dimension_catalog import get_pipe_dimension, find_minimum_schedule
from ..engines import (hydraulic_incompressible, hydraulic_compressible,
                        hydraulic_gravity, vacuum as vacuum_engine,
                        thickness_internal, thickness_external, supports, checker)
from ..config import get_profile, get_service_config
from ..catalogs.fluid_properties import get_fluid_properties
from ..units import m3h_to_m3s, bar_to_pa, barg_to_pa_abs
from ..exceptions import ValidationError, DatasetMissingError, OutOfScopeError
from ..materials import resolve_catalog, get_material_spec

logger = logging.getLogger("sidct.selector")

GRAVITY_SERVICES = {"sanitary_drainage", "rainwater"}
COMPRESSIBLE_SERVICES = {"compressed_air", "natural_gas"}
VACUUM_SERVICES = {"vacuum_utility"}
FIRE_SERVICES = {"fire_water"}

_PREFERRED_SCHEDULES_CARBON = ["SCH40", "STD", "SCH80", "XS", "SCH20", "SCH10"]
_PREFERRED_SCHEDULES_STAINLESS = ["SCH40S", "SCH10S", "SCH5S", "SCH80S"]
_PREFERRED_SCHEDULES_PVC_EU = ["PN16", "PN10"]
_PREFERRED_SCHEDULES_PVC_US = ["SCH40", "SCH80"]
_PREFERRED_SCHEDULES_PE_EU = ["SDR17", "SDR13.6", "SDR11"]
_PREFERRED_SCHEDULES_PPR_EU = ["SDR11", "SDR7.4", "SDR6"]


def _preferred_schedule(material: str, catalog: str) -> list[str]:
    mat = material.lower()
    if "PVC_EN1452" in catalog.upper():
        return _PREFERRED_SCHEDULES_PVC_EU
    if "PVC_ASTMD1785" in catalog.upper():
        return _PREFERRED_SCHEDULES_PVC_US
    if "PE_EN12201" in catalog.upper():
        return _PREFERRED_SCHEDULES_PE_EU
    if "PPR_ISO15874" in catalog.upper():
        return _PREFERRED_SCHEDULES_PPR_EU
    is_ss = any(k in mat for k in ("316", "304", "tp3", "inox"))
    if is_ss or "19M" in catalog.upper():
        return _PREFERRED_SCHEDULES_STAINLESS
    return _PREFERRED_SCHEDULES_CARBON


def run_full_calculation(inp: LineInput) -> ReportContext:
    """Executa cálculo completo e retorna ReportContext."""
    import datetime
    profile = get_profile(inp.project_profile)
    service_cfg = get_service_config(inp.service)
    warnings_global: list[str] = []
    assumptions: list[str] = []
    citations: list = []
    catalog, catalog_warnings = resolve_catalog(inp.material, inp.dimensional_catalog, inp.jurisdiction)
    warnings_global.extend(catalog_warnings)
    material_spec = get_material_spec(inp.material, inp.jurisdiction)
    if catalog != inp.dimensional_catalog:
        inp = inp.model_copy(update={"dimensional_catalog": catalog})

    # ── Validação ─────────────────────────────────────────────────────────────
    from ..validators import validate_line_input, validate_profile_service_compatibility
    val_warnings = validate_line_input(inp)
    compat_warnings = validate_profile_service_compatibility(inp.project_profile, inp.service)
    warnings_global.extend(val_warnings + compat_warnings)

    # ── Propriedades do fluido ─────────────────────────────────────────────────
    fluid = get_fluid_properties(inp.service, inp.T_oper_c, inp.P_oper_bar)
    warnings_global.extend(fluid.warnings)

    # ── Velocidade e ΔP limites do perfil ─────────────────────────────────────
    v_limits = profile.get("velocity_limits", {})
    svc_key = inp.service.replace("_water", "_water").replace("water_", "water_")
    v_cfg = v_limits.get(inp.service, v_limits.get("water_general", {}))
    if isinstance(v_cfg, list):
        v_min, v_max = v_cfg
    elif isinstance(v_cfg, dict):
        v_max = v_cfg.get("normal_pipe", [3.0, 10.0])
        v_max = v_max[1] if isinstance(v_max, list) else float(v_max)
        v_min = 0.3
    else:
        v_max = 3.0
        v_min = 0.3

    dp_criteria = profile.get("max_pressure_drop_criteria", {})
    dp_key = "water_general" if inp.service in ("potable_water", "service_water",
                                                  "osmotized_water", "chilled_water",
                                                  "condenser_water", "fire_water") else inp.service
    allowable_dp = inp.allowable_pressure_drop_bar or dp_criteria.get(dp_key)

    # ── Schedules preferênciais ───────────────────────────────────────────────
    preferred_sch = _preferred_schedule(inp.material, catalog)

    # ── Motor hidráulico ───────────────────────────────────────────────────────
    hydraulic_result: HydraulicResult | None = None
    if inp.service in GRAVITY_SERVICES:
        for sch in preferred_sch:
            try:
                hydraulic_result = hydraulic_gravity.select_dn(inp, fluid, catalog=catalog, schedule=sch)
                if hydraulic_result.status not in ("OUT_OF_SCOPE", "INSUFFICIENT"):
                    break
            except (ValidationError, DatasetMissingError, OutOfScopeError):
                continue
            except Exception as e:
                logger.warning(f"Erro inesperado no motor gravitário: {e}")
                continue
    elif inp.service in COMPRESSIBLE_SERVICES:
        v_max_gas = v_max if isinstance(v_max, float) else 15.0
        for sch in preferred_sch:
            try:
                hydraulic_result = hydraulic_compressible.select_dn(
                    inp, fluid, v_max=v_max_gas,
                    allowable_dp_bar=allowable_dp,
                    catalog=catalog, schedule=sch)
                if hydraulic_result.status not in ("OUT_OF_SCOPE",):
                    break
            except (ValidationError, DatasetMissingError, OutOfScopeError):
                continue
            except Exception as e:
                logger.warning(f"Erro inesperado no motor compressível: {e}")
                continue
    elif inp.service in VACUUM_SERVICES:
        # Usar DN recebido ou DN mínimo
        dn_try = inp.DN_received_mm or 50.0
        for sch in preferred_sch:
            try:
                pipe_try = get_pipe_dimension(catalog, dn_try, sch)
                hydraulic_result = vacuum_engine.calculate_vacuum(inp, fluid, pipe_try)
                break
            except (ValidationError, DatasetMissingError, OutOfScopeError):
                continue
            except Exception as e:
                logger.warning(f"Erro inesperado no motor vácuo: {e}")
                continue
    else:
        for sch in preferred_sch:
            try:
                hydraulic_result = hydraulic_incompressible.select_dn(
                    inp, fluid, v_min=v_min, v_max=v_max,
                    allowable_dp_bar=allowable_dp,
                    catalog=catalog, schedule=sch,
                    roughness_m=material_spec.roughness_m if material_spec else None)
                if hydraulic_result.status not in ("OUT_OF_SCOPE",):
                    break
            except (ValidationError, DatasetMissingError, OutOfScopeError):
                continue
            except Exception as e:
                logger.warning(f"Erro inesperado no motor incompressível: {e}")
                continue

    if hydraulic_result is None:
        hydraulic_result = HydraulicResult(
            regime="unknown",
            service=inp.service,
            line_tag=inp.line_tag,
            status="DATASET_MISSING",
            warnings=["Motor hidráulico não executado"],
        )

    # ── Espessura interna ──────────────────────────────────────────────────────
    DN_final = (hydraulic_result.DN_governing_mm or inp.DN_received_mm or 50.0)
    thickness_result: ThicknessResult | None = None
    ext_result: ExternalPressureResult | None = None

    try:
        if hydraulic_result and hydraulic_result.pipe_used:
            pipe_for_thickness = hydraulic_result.pipe_used
        else:
            pipe_for_thickness = get_pipe_dimension(catalog, DN_final, preferred_sch[0])
        thickness_result = thickness_internal.calculate_thickness(
            inp, pipe_for_thickness, profile=profile
        )
        # Seleccionar schedule por espessura
        if thickness_result.t_after_mill_tolerance_mm:
            pipe_final = find_minimum_schedule(
                catalog, DN_final, thickness_result.t_after_mill_tolerance_mm
            )
            if pipe_final:
                thickness_result.selected_wall_mm = pipe_final.wall_thickness_mm
                thickness_result.selected_schedule = pipe_final.schedule
    except Exception as e:
        thickness_result = ThicknessResult(
            line_tag=inp.line_tag,
            design_code=inp.design_code or "N/A",
            material=inp.material,
            status="DATASET_MISSING",
            warnings=[str(e)],
        )

    # ── Pressão externa (vácuo) ────────────────────────────────────────────────
    if inp.service in VACUUM_SERVICES:
        try:
            pipe_ext = get_pipe_dimension(catalog, DN_final, preferred_sch[0])
            ext_result = thickness_external.calculate_external_pressure(inp, pipe_ext)
        except Exception as e:
            ext_result = ExternalPressureResult(
                line_tag=inp.line_tag,
                method_status="DATASET_MISSING",
                warnings=[str(e)],
            )

    # ── Suportes ──────────────────────────────────────────────────────────────
    support_result = None
    try:
        pipe_sup = get_pipe_dimension(catalog, DN_final, preferred_sch[0])
        support_result = supports.calculate_supports(inp, fluid, pipe_sup)
    except Exception:
        pass

    # ── Checker ───────────────────────────────────────────────────────────────
    checker_result = checker.run_checker(inp, hydraulic_result, thickness_result, ext_result)

    # ── Citações normativas ────────────────────────────────────────────────────
    from ..models import CitationItem
    code = inp.design_code or profile.get("primary_design_code", "ASME_B31_3")
    if "B31_3" in (code or ""):
        citations.append(CitationItem(
            standard_id="ASME_B31_3", edition="2022",
            clause="304.1.2",
            description="Minimum pipe wall thickness under internal pressure",
            equation_used="t = P·D / (2·(S·E + P·Y))",
        ))
    if "B31_9" in (code or ""):
        citations.append(CitationItem(
            standard_id="ASME_B31_9", edition="2022",
            clause="905.1.1",
            description="Minimum wall thickness — building services",
        ))
    if "EN_13480" in (code or ""):
        citations.append(CitationItem(
            standard_id="EN_13480", edition="2017+A1:2020",
            clause="6.1",
            description="Required wall thickness under internal pressure",
            equation_used="e = P·do / (2·f + P)",
        ))
    citations.append(CitationItem(
        standard_id="CRANE_TP410", edition="2013",
        clause="—",
        description="K-values for fittings and valves",
    ))

    warn_items = [
        WarningItem(code="W000", severity="WARNING", message=w, module="selector")
        for w in warnings_global
    ]

    return ReportContext(
        project_name=inp.project_name,
        line_tag=inp.line_tag,
        date=datetime.date.today().isoformat(),
        line_input=inp,
        fluid_properties=fluid,
        hydraulic_result=hydraulic_result,
        thickness_result=thickness_result,
        external_pressure_result=ext_result,
        support_result=support_result,
        checker_result=checker_result,
        citations=citations,
        warnings=warn_items,
        assumptions_declared=assumptions,
        profile_used=profile,
    )
