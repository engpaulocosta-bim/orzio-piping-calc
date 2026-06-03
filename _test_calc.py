import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\Repositorios\orzio-piping-calc") / "src"))

from sidct.models import LineInput, FittingItem, ValveItem
from sidct.engines.selector import run_full_calculation

inp = LineInput(
    project_name="PROJ-001",
    line_tag="L-001",
    service="compressed_air",
    project_profile="glass_factory_industrial_eu",
    jurisdiction="EU",
    fluid_name="Ar Comprimido",
    P_oper_bar=7.0,
    T_oper_c=25.0,
    P_design_bar=10.0,
    T_design_c=60.0,
    flow_rate=300.0,
    flow_rate_basis="Nm3/h",
    line_length_m=50.0,
    elevation_delta_m=0.0,
    material="A106 GrB",
    dimensional_catalog="B36.10M",
    corrosion_allowance_mm=1.5,
    insulation_thickness_mm=50.0,
    insulation_density_kgm3=100.0,
    fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=4)],
    valves=[ValveItem(valve_type="GATE_VALVE_FULL_OPEN", quantity=1)],
    allowable_pressure_drop_bar=0.5,
    required_residual_pressure_bar=None,
    DN_received_mm=None,
    schedule_or_wall_received=None,
    slope_mm_m=None,
    vacuum_target_mbara=None,
    design_notes="",
    operation_mode="calculate_new",
)

try:
    ctx = run_full_calculation(inp)
    print("CALC OK")
    print("DN:", getattr(ctx, "selected_dn", "?"))
except Exception:
    print("CALC FAILED:")
    traceback.print_exc()
