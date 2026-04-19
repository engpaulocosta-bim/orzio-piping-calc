"""PASSO 11 — Casos de teste obrigatórios.

Cobre os 8 cenários definidos no PROMPT MASTER:
1. Ar comprimido industrial
2. Água de serviço industrial
3. Chilled water data centre
4. Gás natural industrial
5. Vácuo (com external pressure)
6. Drenagem sanitária
7. Água pluvial
8. Fire water
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.models import LineInput, FittingItem
from sidct.engines.selector import run_full_calculation


# ── Caso 1: Ar comprimido industrial ─────────────────────────────────────────

def test_case_1_compressed_air():
    inp = LineInput(
        project_name="CASO-1",
        line_tag="CA-001",
        service="compressed_air",
        project_profile="glass_factory_industrial_eu",
        jurisdiction="EU",
        fluid_name="Ar comprimido",
        P_oper_bar=7.0, T_oper_c=35.0,
        P_design_bar=10.0, T_design_c=50.0,
        flow_rate=300.0, flow_rate_basis="Nm3/h",
        line_length_m=150.0, elevation_delta_m=0.0,
        material="A106 GrB",
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.0,
        insulation_thickness_mm=50.0, insulation_density_kgm3=100.0,
        fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=4)],
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "compressible_gas"
    assert ctx.hydraulic_result.mach_number is not None
    assert ctx.thickness_result is not None
    # Checker deve concluir (não DATASET_MISSING por falta de motor)
    assert ctx.checker_result is not None
    assert ctx.checker_result.overall_status != "ERROR"


# ── Caso 2: Água de serviço industrial ───────────────────────────────────────

def test_case_2_service_water():
    inp = LineInput(
        project_name="CASO-2",
        line_tag="SW-001",
        service="service_water",
        project_profile="industrial_utilities_eu",
        jurisdiction="EU",
        fluid_name="Água de serviço",
        P_oper_bar=10.0, T_oper_c=20.0,
        P_design_bar=16.0, T_design_c=40.0,
        flow_rate=50.0, flow_rate_basis="L/s",
        line_length_m=80.0, elevation_delta_m=0.0,
        material="A53 GrB",
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
        fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=2)],
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "pressurized_incompressible"
    assert ctx.hydraulic_result.DN_governing_mm is not None
    assert ctx.hydraulic_result.velocity_ms is not None
    assert ctx.hydraulic_result.velocity_ms > 0
    assert ctx.thickness_result is not None
    assert ctx.thickness_result.status == "CALCULATED"


# ── Caso 3: Chilled water data centre ─────────────────────────────────────────

def test_case_3_chilled_water_dc():
    inp = LineInput(
        project_name="CASO-3",
        line_tag="CW-001",
        service="chilled_water",
        project_profile="datacentre_building_services_eu",
        jurisdiction="EU",
        fluid_name="Chilled water",
        P_oper_bar=6.0, T_oper_c=7.0,
        P_design_bar=10.0, T_design_c=20.0,
        flow_rate=120.0, flow_rate_basis="m3/h",
        line_length_m=120.0, elevation_delta_m=3.0,
        material="A106 GrB",
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
        allowable_pressure_drop_bar=0.3,
        fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=3)],
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "pressurized_incompressible"
    assert ctx.hydraulic_result.DN_governing_mm is not None
    assert ctx.thickness_result is not None


# ── Caso 4: Gás natural industrial ────────────────────────────────────────────

def test_case_4_natural_gas():
    inp = LineInput(
        project_name="CASO-4",
        line_tag="NG-001",
        service="natural_gas",
        project_profile="glass_factory_industrial_eu",
        jurisdiction="EU",
        fluid_name="Gás natural",
        P_oper_bar=3.0, T_oper_c=20.0,
        P_design_bar=5.0, T_design_c=40.0,
        flow_rate=500.0, flow_rate_basis="Nm3/h",
        line_length_m=100.0, elevation_delta_m=0.0,
        material="A106 GrB",
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.0,
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "compressible_gas"
    # CH4 warning deve estar presente
    fluid_warnings = ctx.fluid_properties.warnings if ctx.fluid_properties else []
    assert any("CH4" in w or "gás natural" in w.lower() for w in fluid_warnings)


# ── Caso 5: Vácuo (com external pressure) ─────────────────────────────────────

def test_case_5_vacuum():
    inp = LineInput(
        project_name="CASO-5",
        line_tag="VAC-001",
        service="vacuum_utility",
        project_profile="industrial_utilities_eu",
        jurisdiction="EU",
        fluid_name="Vácuo utilitário",
        P_oper_bar=0.0, T_oper_c=25.0,
        P_design_bar=0.1, T_design_c=40.0,
        flow_rate=10.0, flow_rate_basis="m3/h",
        line_length_m=30.0, elevation_delta_m=0.0,
        material="A106 GrB",
        dimensional_catalog="ASME_B36_10M",
        vacuum_target_mbara=10.0,
    )
    ctx = run_full_calculation(inp)

    # Deve ter hydraulic com regime vacuum_conductance
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "vacuum_conductance"

    # OBRIGATÓRIO: external_pressure_result presente
    assert ctx.external_pressure_result is not None
    assert ctx.external_pressure_result.P_external_design_bar is not None

    # Checker nunca pode aprovar vácuo sem external check
    assert ctx.checker_result is not None
    cr = ctx.checker_result
    if cr.overall_status == "APPROVED":
        # Se APPROVED, external deve estar OK também
        assert cr.external_pressure_status in ("APPROVED", "WARNING", None)


# ── Caso 6: Drenagem sanitária ─────────────────────────────────────────────────

def test_case_6_sanitary_drainage():
    inp = LineInput(
        project_name="CASO-6",
        line_tag="DR-001",
        service="sanitary_drainage",
        project_profile="datacentre_building_services_eu",
        jurisdiction="EU",
        fluid_name="Drenagem sanitária",
        P_oper_bar=0.0, T_oper_c=20.0,
        P_design_bar=0.1, T_design_c=30.0,
        flow_rate=8.0, flow_rate_basis="L/s",
        line_length_m=60.0, elevation_delta_m=0.0,
        material="pvc",
        dimensional_catalog="ASME_B36_10M",
        slope_mm_m=10.0,
    )
    ctx = run_full_calculation(inp)

    # Motor DEVE ser gravitário
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "gravity_partially_full"
    assert ctx.hydraulic_result.flow_depth_ratio is not None


# ── Caso 7: Água pluvial ──────────────────────────────────────────────────────

def test_case_7_rainwater():
    inp = LineInput(
        project_name="CASO-7",
        line_tag="RW-001",
        service="rainwater",
        project_profile="datacentre_building_services_eu",
        jurisdiction="EU",
        fluid_name="Água pluvial",
        P_oper_bar=0.0, T_oper_c=15.0,
        P_design_bar=0.1, T_design_c=25.0,
        flow_rate=12.0, flow_rate_basis="L/s",
        line_length_m=40.0, elevation_delta_m=0.0,
        material="pvc",
        dimensional_catalog="ASME_B36_10M",
        slope_mm_m=15.0,
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "gravity_partially_full"
    assert ctx.hydraulic_result.DN_governing_mm is not None


# ── Caso 8: Fire water ────────────────────────────────────────────────────────

def test_case_8_fire_water():
    inp = LineInput(
        project_name="CASO-8",
        line_tag="FW-001",
        service="fire_water",
        project_profile="fire_protection_en",
        jurisdiction="EU",
        fluid_name="Água incêndio",
        P_oper_bar=6.0, T_oper_c=20.0,
        P_design_bar=10.0, T_design_c=30.0,
        flow_rate=30.0, flow_rate_basis="L/s",
        line_length_m=100.0, elevation_delta_m=5.0,
        material="A53 GrB",
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
    )
    ctx = run_full_calculation(inp)

    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "pressurized_incompressible"
    assert ctx.hydraulic_result.DN_governing_mm is not None
    assert ctx.thickness_result is not None


# ── Testes de segurança ───────────────────────────────────────────────────────

def test_security_gravity_without_slope_raises():
    """Drenagem sem slope deve falhar na validação."""
    with pytest.raises((ValueError, Exception)):
        LineInput(
            project_name="SEC-1", line_tag="S1",
            service="sanitary_drainage", project_profile="datacentre_building_services_eu",
            jurisdiction="EU", fluid_name="sewage",
            P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
            flow_rate=5.0, flow_rate_basis="L/s", line_length_m=50.0,
            material="pvc", dimensional_catalog="ASME_B36_10M",
            slope_mm_m=None,  # SEM slope
        )

def test_security_inox_wrong_catalog():
    """Inox com B36.10M deve levantar CodeMismatchError."""
    from sidct.validators import validate_line_input
    from sidct.exceptions import CodeMismatchError
    inp = LineInput(
        project_name="SEC-2", line_tag="S2",
        service="osmotized_water", project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=6.0, T_oper_c=20.0, P_design_bar=10.0, T_design_c=30.0,
        flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=50.0,
        material="A312 TP304", dimensional_catalog="ASME_B36_10M",
    )
    with pytest.raises(CodeMismatchError):
        validate_line_input(inp)

def test_security_vacuum_without_target_raises():
    """Vácuo sem vacuum_target_mbara deve falhar."""
    with pytest.raises((ValueError, Exception)):
        LineInput(
            project_name="SEC-3", line_tag="S3",
            service="vacuum_utility", project_profile="industrial_utilities_eu",
            jurisdiction="EU", fluid_name="vacuum",
            P_oper_bar=0.0, T_oper_c=25.0, P_design_bar=0.1, T_design_c=40.0,
            flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=30.0,
            material="A106 GrB", dimensional_catalog="ASME_B36_10M",
            vacuum_target_mbara=None,  # SEM target
        )

def test_security_dataset_missing_not_approved():
    """Sistema nunca deve marcar APPROVED quando há DATASET_MISSING."""
    inp = LineInput(
        project_name="SEC-4", line_tag="S4",
        service="service_water", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=10.0, T_oper_c=20.0, P_design_bar=16.0, T_design_c=40.0,
        flow_rate=50.0, flow_rate_basis="L/s", line_length_m=80.0,
        material="FANTASIUM_ALLOY",  # material desconhecido
        dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
    )
    ctx = run_full_calculation(inp)
    assert ctx.checker_result is not None
    # Não pode ser APPROVED com material sem dataset
    assert ctx.checker_result.overall_status != "APPROVED"
