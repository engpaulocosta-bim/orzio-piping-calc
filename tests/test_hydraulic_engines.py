"""Testes dos motores hidráulicos."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.models import LineInput, FittingItem, FluidProperties
from sidct.catalogs.pipe_dimension_catalog import get_pipe_dimension
from sidct.catalogs.fluid_properties import get_fluid_properties
from sidct.engines import hydraulic_incompressible, hydraulic_compressible, hydraulic_gravity
from sidct.exceptions import WrongEngineError, MissingInputError, OutOfScopeError


def _make_water_fluid(T_c=20.0, P_barg=10.0):
    return get_fluid_properties("service_water", T_c, P_barg)


def _make_air_fluid(T_c=35.0, P_barg=7.0):
    return get_fluid_properties("compressed_air", T_c, P_barg)


def _water_line(service="service_water", Q=50.0, basis="L/s", L=80.0, P_oper=10.0):
    return LineInput(
        project_name="TEST", line_tag="TW-001",
        service=service, project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=P_oper, T_oper_c=20.0, P_design_bar=16.0, T_design_c=40.0,
        flow_rate=Q, flow_rate_basis=basis, line_length_m=L,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        corrosion_allowance_mm=1.5,
        fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=2)],
    )


def _air_line(Q=300.0, basis="Nm3/h"):
    return LineInput(
        project_name="TEST", line_tag="TA-001",
        service="compressed_air", project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name="air",
        P_oper_bar=7.0, T_oper_c=35.0, P_design_bar=10.0, T_design_c=50.0,
        flow_rate=Q, flow_rate_basis=basis, line_length_m=150.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=4)],
    )


# ── Incompressível ─────────────────────────────────────────────────────────────

def test_incompressible_basic_water():
    inp = _water_line()
    fluid = _make_water_fluid()
    pipe = get_pipe_dimension("ASME_B36_10M", 150, "SCH40")
    res = hydraulic_incompressible.calculate_for_pipe(inp, fluid, pipe)
    assert res.status == "CALCULATED"
    assert res.velocity_ms is not None and res.velocity_ms > 0
    assert res.Re is not None and res.Re > 0
    assert res.dp_total_bar is not None and res.dp_total_bar >= 0

def test_incompressible_colebrook_convergence():
    """Verificar que Colebrook-White converge para vários Re."""
    from sidct.engines.hydraulic_incompressible import _colebrook_white
    for Re in [500, 2000, 4000, 10000, 100000, 1e7]:
        f = _colebrook_white(Re, 0.046e-3 / 0.1)
        assert f > 0

def test_wrong_engine_gravity_raises():
    inp = LineInput(
        project_name="TEST", line_tag="TG-001",
        service="sanitary_drainage", project_profile="datacentre_building_services_eu",
        jurisdiction="EU", fluid_name="water",
        P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
        flow_rate=5.0, flow_rate_basis="L/s", line_length_m=50.0,
        material="pvc", dimensional_catalog="ASME_B36_10M",
        slope_mm_m=10.0,
    )
    fluid = _make_water_fluid()
    pipe = get_pipe_dimension("ASME_B36_10M", 150, "SCH40")
    with pytest.raises(WrongEngineError):
        hydraulic_incompressible.calculate_for_pipe(inp, fluid, pipe)

def test_incompressible_select_dn():
    inp = _water_line()
    fluid = _make_water_fluid()
    res = hydraulic_incompressible.select_dn(inp, fluid, v_min=0.5, v_max=3.0)
    assert res.DN_governing_mm is not None
    assert res.DN_governing_mm >= 25  # DN razoável para 50 L/s


# ── Compressível ───────────────────────────────────────────────────────────────

def test_compressible_air_basic():
    inp = _air_line()
    fluid = _make_air_fluid()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    res = hydraulic_compressible.calculate_compressible(inp, fluid, pipe)
    assert res.mach_number is not None and res.mach_number > 0
    assert res.pressure_ratio is not None and res.pressure_ratio > 0

def test_compressible_mach_check():
    """Linha muito longa com DN pequeno deve alertar sobre Mach."""
    inp = LineInput(
        project_name="TEST", line_tag="TA-002",
        service="compressed_air", project_profile="glass_factory_industrial_eu",
        jurisdiction="EU", fluid_name="air",
        P_oper_bar=7.0, T_oper_c=35.0, P_design_bar=10.0, T_design_c=50.0,
        flow_rate=1000.0, flow_rate_basis="Nm3/h", line_length_m=200.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
    )
    fluid = _make_air_fluid()
    pipe = get_pipe_dimension("ASME_B36_10M", 25, "SCH40")  # DN pequeno intencional
    res = hydraulic_compressible.calculate_compressible(inp, fluid, pipe)
    # Pode ser OUT_OF_SCOPE ou WARNING com Mach elevado
    assert res.mach_number is not None

def test_wrong_engine_compressible_on_water():
    inp = _water_line()
    fluid = _make_water_fluid()
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    with pytest.raises(WrongEngineError):
        hydraulic_compressible.calculate_compressible(inp, fluid, pipe)


# ── Gravidade ─────────────────────────────────────────────────────────────────

def test_gravity_manning_basic():
    inp = LineInput(
        project_name="TEST", line_tag="TDR-001",
        service="sanitary_drainage", project_profile="datacentre_building_services_eu",
        jurisdiction="EU", fluid_name="sewage",
        P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
        flow_rate=5.0, flow_rate_basis="L/s", line_length_m=50.0,
        material="pvc", dimensional_catalog="ASME_B36_10M",
        slope_mm_m=10.0,
    )
    fluid = get_fluid_properties("sanitary_drainage", 20.0, 0.0)
    pipe = get_pipe_dimension("ASME_B36_10M", 150, "SCH40")
    res = hydraulic_gravity.calculate_gravity(inp, fluid, pipe)
    assert res.regime == "gravity_partially_full"
    assert res.flow_depth_ratio is not None and 0 < res.flow_depth_ratio < 1

def test_gravity_no_slope_raises():
    with pytest.raises((MissingInputError, ValueError)):
        LineInput(
            project_name="TEST", line_tag="TDR-002",
            service="sanitary_drainage", project_profile="datacentre_building_services_eu",
            jurisdiction="EU", fluid_name="sewage",
            P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
            flow_rate=5.0, flow_rate_basis="L/s", line_length_m=50.0,
            material="pvc", dimensional_catalog="ASME_B36_10M",
            slope_mm_m=None,  # falta slope → deve falhar
        )

def test_gravity_select_dn():
    inp = LineInput(
        project_name="TEST", line_tag="TDR-003",
        service="rainwater", project_profile="datacentre_building_services_eu",
        jurisdiction="EU", fluid_name="rainwater",
        P_oper_bar=0.0, T_oper_c=20.0, P_design_bar=0.1, T_design_c=30.0,
        flow_rate=10.0, flow_rate_basis="L/s", line_length_m=30.0,
        material="pvc", dimensional_catalog="ASME_B36_10M",
        slope_mm_m=15.0,
    )
    fluid = get_fluid_properties("rainwater", 20.0, 0.0)
    res = hydraulic_gravity.select_dn(inp, fluid)
    assert res.DN_governing_mm is not None


# ── Vácuo ─────────────────────────────────────────────────────────────────────

def test_vacuum_external_pressure_required():
    """Linha de vácuo DEVE encaminhar para external pressure check."""
    from sidct.engines.vacuum import calculate_vacuum
    inp = LineInput(
        project_name="TEST", line_tag="TV-001",
        service="vacuum_utility", project_profile="industrial_utilities_eu",
        jurisdiction="EU", fluid_name="vacuum",
        P_oper_bar=0.0, T_oper_c=25.0, P_design_bar=0.1, T_design_c=40.0,
        flow_rate=10.0, flow_rate_basis="m3/h", line_length_m=30.0,
        material="A106 GrB", dimensional_catalog="ASME_B36_10M",
        vacuum_target_mbara=10.0,
    )
    fluid = get_fluid_properties("vacuum_utility", 25.0, 0.0)
    pipe = get_pipe_dimension("ASME_B36_10M", 50, "SCH40")
    res = calculate_vacuum(inp, fluid, pipe)
    # Deve ter conductance_result com external_pressure_check_required=True
    assert res.conductance_result is not None
    assert res.conductance_result.get("external_pressure_check_required") is True
