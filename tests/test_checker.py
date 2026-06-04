"""Testes do checker e selector."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.models import LineInput, HydraulicResult, ThicknessResult, ExternalPressureResult
from sidct.engines.checker import run_checker
from sidct.engines.selector import run_full_calculation


def _base_inp(service="service_water", extra=None):
    kw = dict(
        project_name="TEST", line_tag="TC-001",
        service=service, project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name=service,
        P_oper_bar=10.0, T_oper_c=20.0, P_design_bar=16.0, T_design_c=40.0,
        flow_rate=50.0, flow_rate_basis="L/s", line_length_m=80.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
    )
    if extra:
        kw.update(extra)
    return LineInput(**kw)


# ── Checker ────────────────────────────────────────────────────────────────────

def test_checker_no_data_is_dataset_missing():
    inp = _base_inp()
    res = run_checker(inp, None, None, None)
    assert res.overall_status == "DATASET_MISSING"

def test_checker_vacuum_without_ext_check_is_critical():
    """Linha de vácuo sem external_pressure_result deve ser DATASET_MISSING ou CRITICAL."""
    inp = LineInput(
        project_name="TEST", line_tag="TV-001",
        service="vacuum_utility", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="vacuum",
        P_oper_bar=0.0, T_oper_c=25.0, P_design_bar=0.1, T_design_c=40.0,
        flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=30.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        vacuum_target_mbara=10.0,
    )
    hr = HydraulicResult(
        regime="vacuum_conductance", service="vacuum_utility", line_tag="TV-001",
        DN_governing_mm=50.0, status="CALCULATED"
    )
    tr = ThicknessResult(
        line_tag="TV-001", design_code="ASME_B31_3", material="A106 GrB",
        t_after_mill_tolerance_mm=3.0, status="CALCULATED"
    )
    res = run_checker(inp, hr, tr, None)  # sem external_pressure_result
    assert res.overall_status in ("DATASET_MISSING", "CRITICAL")
    assert "external_pressure_check_not_performed" in " ".join(res.dataset_missing_items)

def test_checker_approved_when_received_larger():
    inp = _base_inp(extra={
        "operation_mode": "check_received",
        "DN_received_mm": 200.0,
        "schedule_or_wall_received": "8.18",
    })
    hr = HydraulicResult(
        regime="pressurized_incompressible", service="service_water",
        line_tag="TC-001", DN_governing_mm=150.0, status="CALCULATED"
    )
    tr = ThicknessResult(
        line_tag="TC-001", design_code="ASME_B31_3", material="A106 GrB",
        t_after_mill_tolerance_mm=4.0, status="CALCULATED"
    )
    res = run_checker(inp, hr, tr, None)
    assert res.overall_status in ("APPROVED", "CONSERVATIVE")

def test_checker_insufficient_when_received_smaller():
    inp = _base_inp(extra={
        "operation_mode": "check_received",
        "DN_received_mm": 50.0,
        "schedule_or_wall_received": "3.91",
    })
    hr = HydraulicResult(
        regime="pressurized_incompressible", service="service_water",
        line_tag="TC-001", DN_governing_mm=200.0, status="CALCULATED"
    )
    res = run_checker(inp, hr, None, None)
    assert res.overall_status in ("INSUFFICIENT", "CRITICAL")


def test_checker_calculate_new_ignores_accidental_received_fields():
    inp = _base_inp(extra={"DN_received_mm": 50.0, "schedule_or_wall_received": "3.91"})
    hr = HydraulicResult(
        regime="pressurized_incompressible", service="service_water",
        line_tag="TC-001", DN_governing_mm=200.0, status="CALCULATED"
    )
    tr = ThicknessResult(
        line_tag="TC-001", design_code="ASME_B31_3", material="A106 GrB",
        t_after_mill_tolerance_mm=8.0, status="CALCULATED"
    )
    res = run_checker(inp, hr, tr, None)
    assert res.overall_status == "CALCULATED"
    assert res.DN_received_mm is None
    assert res.wall_received_mm is None

def test_checker_never_approves_with_dataset_missing():
    inp = _base_inp()
    hr = HydraulicResult(
        regime="pressurized_incompressible", service="service_water",
        line_tag="TC-001", status="DATASET_MISSING",
    )
    res = run_checker(inp, hr, None, None)
    assert res.overall_status == "DATASET_MISSING"


# ── Selector / full calculation ────────────────────────────────────────────────

def test_full_calculation_water():
    inp = _base_inp()
    ctx = run_full_calculation(inp)
    assert ctx.hydraulic_result is not None
    assert ctx.thickness_result is not None
    assert ctx.checker_result is not None
    assert ctx.hydraulic_result.DN_governing_mm is not None

def test_full_calculation_air():
    inp = LineInput(
        project_name="TEST", line_tag="TA-001",
        service="compressed_air", project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name="air",
        P_oper_bar=7.0, T_oper_c=35.0, P_design_bar=10.0, T_design_c=50.0,
        flow_rate=300.0, flow_rate_basis="Nm3/h", line_length_m=150.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.0, insulation_thickness_mm=50.0,
    )
    ctx = run_full_calculation(inp)
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "compressible_gas"

def test_full_calculation_chilled_water():
    inp = LineInput(
        project_name="TEST", line_tag="TCW-001",
        service="chilled_water", project_profile="datacentre_building_services_eu",
        jurisdiction="EU", fluid_name="chilled_water",
        P_oper_bar=6.0, T_oper_c=7.0, P_design_bar=10.0, T_design_c=20.0,
        flow_rate=100.0, flow_rate_basis="m3/h", line_length_m=120.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
        allowable_pressure_drop_bar=0.3,
    )
    ctx = run_full_calculation(inp)
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.status in ("CALCULATED", "WARNING")


def test_full_calculation_rejects_invalid_flow_basis_for_service():
    inp = _base_inp(extra={"flow_rate_basis": "kg/s"})
    with pytest.raises(Exception, match="Unidade de caudal 'kg/s'"):
        run_full_calculation(inp)

def test_full_calculation_gravity_drainage():
    inp = LineInput(
        project_name="TEST", line_tag="TDR-001",
        service="sanitary_drainage", project_profile="datacentre_building_services_eu",
        jurisdiction="EU", fluid_name="sewage",
        P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
        flow_rate=5.0, flow_rate_basis="L/s", line_length_m=50.0,
        material="pvc", dimensional_catalog="ASME_B36_10M",
        slope_mm_m=10.0,
    )
    ctx = run_full_calculation(inp)
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "gravity_partially_full"

def test_full_calculation_vacuum():
    inp = LineInput(
        project_name="TEST", line_tag="TV-001",
        service="vacuum_utility", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="vacuum",
        P_oper_bar=0.0, T_oper_c=25.0, P_design_bar=0.1, T_design_c=40.0,
        flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=30.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        vacuum_target_mbara=10.0,
    )
    ctx = run_full_calculation(inp)
    assert ctx.hydraulic_result is not None
    assert ctx.hydraulic_result.regime == "vacuum_conductance"
    # Vácuo deve ter external pressure check
    assert ctx.external_pressure_result is not None
