"""Testes dos motores de espessura."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.models import LineInput
from sidct.catalogs.pipe_dimension_catalog import get_pipe_dimension
from sidct.engines.thickness_internal import calculate_thickness
from sidct.engines.thickness_external import calculate_external_pressure


def _base_inp(service="compressed_air", material="A106 GrB",
              P_design=10.0, T_design=50.0, catalog="ASME_B36_10M"):
    return LineInput(
        project_name="TEST", line_tag="TE-001",
        service=service, project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name=service,
        P_oper_bar=7.0, T_oper_c=35.0,
        P_design_bar=P_design, T_design_c=T_design,
        flow_rate=300.0, flow_rate_basis="Nm3/h", line_length_m=100.0,
        material=material, dimensional_catalog=catalog,
        corrosion_allowance_mm=1.0,
        vacuum_target_mbara=10.0 if service == "vacuum_utility" else None,
    )


# ── Espessura interna ─────────────────────────────────────────────────────────

def test_thickness_b31_3_basic():
    inp = _base_inp()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_3")
    assert res.status == "CALCULATED"
    assert res.t_pressure_only_mm is not None and res.t_pressure_only_mm > 0
    assert res.t_after_mill_tolerance_mm > res.t_pressure_only_mm

def test_thickness_mill_tolerance():
    """t_after_mill deve ser t_plus_ca / (1 - 0.125)."""
    inp = _base_inp()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_3")
    assert res.t_after_mill_tolerance_mm is not None
    assert res.t_plus_ca_mm is not None
    expected = res.t_plus_ca_mm / (1.0 - 0.125)
    assert abs(res.t_after_mill_tolerance_mm - expected) < 0.001

def test_thickness_b31_9_pressure_limit():
    """B31.9 deve rejeitar P > 20.7 barg."""
    inp = _base_inp(P_design=25.0)  # > 20.7 barg
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_9")
    assert res.status == "OUT_OF_SCOPE"

def test_thickness_b31_9_ok():
    inp = _base_inp(service="chilled_water", P_design=10.0,
                    material="A106 GrB")
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_9")
    assert res.status == "CALCULATED"

def test_thickness_en_13480():
    inp = _base_inp()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="EN_13480")
    assert res.status == "CALCULATED"
    assert res.governing_code == "EN 13480"

def test_thickness_unsupported_material():
    inp = _base_inp(material="FANTASIUM_ALLOY")
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_3")
    assert res.status == "DATASET_MISSING"

def test_thickness_stainless():
    inp = LineInput(
        project_name="TEST", line_tag="TSS-001",
        service="osmotized_water", project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=6.0, T_oper_c=20.0, P_design_bar=10.0, T_design_c=30.0,
        flow_rate=20.0, flow_rate_basis="m3/h", line_length_m=50.0,
        material="A312 TP316", dimensional_catalog="ASME_B36_19M",
        corrosion_allowance_mm=0.0,
    )
    pipe = get_pipe_dimension("ASME_B36_19M", 50, "SCH40S")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_3")
    assert res.status == "CALCULATED"

def test_thickness_schedule_selected():
    inp = _base_inp()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_thickness(inp, pipe, design_code="ASME_B31_3")
    # Deve ter seleccionado um schedule
    assert res.selected_schedule is not None


# ── Pressão externa ────────────────────────────────────────────────────────────

def test_external_pressure_vacuum():
    inp = LineInput(
        project_name="TEST", line_tag="TV-001",
        service="vacuum_utility", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="vacuum",
        P_oper_bar=0.0, T_oper_c=25.0, P_design_bar=0.1, T_design_c=40.0,
        flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=30.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        vacuum_target_mbara=10.0,
    )
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = calculate_external_pressure(inp, pipe)
    assert res.P_external_design_bar is not None and res.P_external_design_bar > 0
    assert res.P_allow_bar is not None and res.P_allow_bar > 0
    assert res.utilization_ratio is not None
    assert "Windenburg" in " ".join(res.warnings)

def test_external_not_applicable_to_water():
    inp = LineInput(
        project_name="TEST", line_tag="TW-001",
        service="service_water", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=10.0, T_oper_c=20.0, P_design_bar=16.0, T_design_c=40.0,
        flow_rate=50.0, flow_rate_basis="L/s", line_length_m=80.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
    )
    pipe = get_pipe_dimension("ASME_B36_10M", 200, "SCH40")
    res = calculate_external_pressure(inp, pipe)
    assert res.method_status == "NOT_APPLICABLE"
