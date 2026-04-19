"""Testes unitários — catálogos dimensionais e materiais."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.catalogs.pipe_dimension_catalog import (
    get_pipe_dimension, get_available_schedules, get_available_dns, find_minimum_schedule
)
from sidct.catalogs.material_stress_catalog import (
    get_allowable_stress, is_material_supported, list_supported_materials
)
from sidct.catalogs.fitting_k_catalog import get_k_value, calculate_total_k
from sidct.exceptions import ValidationError, CodeMismatchError, DatasetMissingError, MaterialNotFoundError
from sidct.models import FittingItem, ValveItem


# ── Catálogo dimensional ──────────────────────────────────────────────────────

def test_b36_10m_dn100_sch40():
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    assert pipe.OD_mm == pytest.approx(114.3, abs=0.1)
    assert pipe.wall_thickness_mm == pytest.approx(6.02, abs=0.01)
    assert pipe.ID_mm == pytest.approx(114.3 - 2*6.02, abs=0.01)
    assert pipe.catalog == "ASME_B36_10M"

def test_b36_19m_dn100_sch10s():
    pipe = get_pipe_dimension("ASME_B36_19M", 100, "SCH10S")
    assert pipe.OD_mm == pytest.approx(114.3, abs=0.1)
    assert pipe.wall_thickness_mm == pytest.approx(3.05, abs=0.01)

def test_invalid_dn_raises():
    with pytest.raises(ValidationError):
        get_pipe_dimension("ASME_B36_10M", 999, "SCH40")

def test_invalid_schedule_raises():
    with pytest.raises(ValidationError):
        get_pipe_dimension("ASME_B36_10M", 100, "SCH_INVALID")

def test_inox_must_use_b36_19m():
    """REGRA: inox não deve usar B36.10M sem override explícito."""
    from sidct.validators import validate_line_input
    from sidct.models import LineInput
    with pytest.raises(CodeMismatchError):
        inp = LineInput(
            project_name="TEST", line_tag="T1", service="chilled_water",
            project_profile="datacentre_building_services_eu", jurisdiction="EU",
            fluid_name="water", P_oper_bar=6.0, T_oper_c=7.0,
            P_design_bar=10.0, T_design_c=20.0,
            flow_rate=100.0, flow_rate_basis="m3/h", line_length_m=100.0,
            material="A312 TP316", dimensional_catalog="ASME_B36_10M",
        )
        validate_line_input(inp)

def test_find_minimum_schedule():
    # t_req = 3.0 mm → SCH10S para DN100 B36.19M (3.05 mm)
    pipe = find_minimum_schedule("ASME_B36_19M", 100, 3.0)
    assert pipe is not None
    assert pipe.wall_thickness_mm >= 3.0

def test_available_dns_b36_10m():
    dns = get_available_dns("ASME_B36_10M")
    assert 100 in dns
    assert 200 in dns

def test_pipe_weight_positive():
    pipe = get_pipe_dimension("ASME_B36_10M", 100, "SCH40")
    assert pipe.weight_kgm > 0


# ── Material stresses ─────────────────────────────────────────────────────────

def test_a106grb_stress_at_38c():
    S, E, Y, key = get_allowable_stress("A106 GrB", 38.0, "seamless")
    assert S == pytest.approx(138.0, abs=0.1)
    assert E == pytest.approx(1.0, abs=0.01)

def test_a106grb_stress_at_200c():
    S, E, Y, key = get_allowable_stress("A106 GrB", 200.0)
    assert S == pytest.approx(138.0, abs=0.1)

def test_a312tp316_stress():
    # A T=50°C → entrada com T_max=93°C → S=110.3 MPa
    S, E, Y, key = get_allowable_stress("A312 TP316", 50.0)
    assert S == pytest.approx(110.3, abs=0.5)
    assert E == pytest.approx(1.0, abs=0.01)

def test_a312tp316_stress_at_20c():
    # A T=20°C → entrada com T_max=38°C → S=115.1 MPa
    S, E, Y, key = get_allowable_stress("A312 TP316", 20.0)
    assert S == pytest.approx(115.1, abs=0.5)

def test_material_out_of_temp_range():
    with pytest.raises(MaterialNotFoundError):
        get_allowable_stress("A53 GrB", 999.0)

def test_unsupported_material():
    assert not is_material_supported("FANTASIUM_ALLOY")

def test_supported_materials_list():
    mats = list_supported_materials()
    assert "A106GRB" in mats
    assert "A312TP316" in mats


# ── K-values ─────────────────────────────────────────────────────────────────

def test_k_90lr_elbow():
    k = get_k_value("90_LR_ELBOW")
    assert k == pytest.approx(0.3, abs=0.01)

def test_k_gate_valve():
    k = get_k_value("GATE_VALVE_FULL_OPEN")
    assert k is not None and k > 0

def test_k_unknown_returns_none():
    k = get_k_value("UNKNOWN_FITTING_XYZ")
    assert k is None

def test_calculate_total_k():
    fittings = [FittingItem(fitting_type="90_LR_ELBOW", quantity=4)]
    valves = [ValveItem(valve_type="GATE_VALVE_FULL_OPEN", quantity=1)]
    K, warnings = calculate_total_k(fittings, valves)
    # 4 × 0.3 + 1 × 0.2 = 1.4
    assert K == pytest.approx(4 * 0.3 + 0.2, abs=0.01)
