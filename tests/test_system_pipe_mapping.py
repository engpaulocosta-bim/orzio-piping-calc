import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sidct.exceptions import DatasetMissingError, ValidationError
from sidct.materials import available_catalogs_for_material, resolve_catalog
from sidct.models import LineInput
from sidct.system_pipe_mapping import (
    get_calculation_ready_materials,
    get_material_options,
    validate_system_material_selection,
)
from sidct.validators import validate_line_input


def _inp(service: str, material: str, catalog: str = "ASME_B36_10M", jurisdiction: str = "EU") -> LineInput:
    return LineInput(
        project_name="MAP",
        line_tag="M-001",
        service=service,
        project_profile="industrial_utilities_eu",
        jurisdiction=jurisdiction,
        fluid_name=service,
        P_oper_bar=4.0,
        T_oper_c=20.0,
        P_design_bar=8.0,
        T_design_c=30.0,
        flow_rate=10.0,
        flow_rate_basis="m3/h",
        line_length_m=30.0,
        material=material,
        dimensional_catalog=catalog,
        corrosion_allowance_mm=1.5,
        slope_mm_m=10.0 if service in ("sanitary_drainage", "rainwater") else None,
        vacuum_target_mbara=10.0 if service == "vacuum_utility" else None,
    )


def test_potable_water_offers_stainless_and_pvc_but_blocks_black_steel():
    ready = get_calculation_ready_materials("potable_water", "EU")

    assert "A312 TP316" in ready
    assert "PVC" in ready
    assert "A53 GrB" in ready
    warnings = validate_system_material_selection("potable_water", "A53 GrB", "EU")
    assert any("potable" in warning.lower() for warning in warnings)
    with pytest.raises(ValidationError):
        validate_system_material_selection("potable_water", "A106 GrB", "EU")


def test_osmotized_water_blocks_carbon_steel_and_allows_316():
    validate_system_material_selection("osmotized_water", "A312 TP316", "EU")

    with pytest.raises(ValidationError):
        validate_system_material_selection("osmotized_water", "A106 GrB", "EU")


def test_natural_gas_matrix_includes_hdpe_as_conditional_future_option():
    options = get_material_options("natural_gas", "US")
    hdpe = [option for option in options if option.material_id == "pe_gas"]

    assert hdpe
    assert hdpe[0].status == "conditional"
    assert not hdpe[0].calculation_ready


def test_compressed_air_blocks_pvc_in_domain_validation():
    inp = _inp("compressed_air", "PVC", "PVC_EN1452")

    with pytest.raises(ValidationError):
        validate_line_input(inp)


def test_service_water_a53_is_accepted_by_family_mapping():
    inp = _inp("service_water", "A53 GrB")
    warnings = validate_line_input(inp)

    assert isinstance(warnings, list)


def test_service_water_exposes_pe100_and_ppr_after_catalog_expansion():
    ready = get_calculation_ready_materials("service_water", "EU")

    assert "HDPE" in ready
    assert "PPR" in ready
    assert available_catalogs_for_material("HDPE", "EU") == ["PE_EN12201"]
    assert available_catalogs_for_material("PPR", "EU") == ["PPR_ISO15874"]


def test_regional_pvc_catalogs_are_restricted_by_jurisdiction():
    eu_catalog, _ = resolve_catalog("PVC", "ASME_B36_10M", "EU")
    us_catalog, _ = resolve_catalog("PVC", "ASME_B36_10M", "US")

    assert eu_catalog == "PVC_EN1452"
    assert us_catalog == "PVC_ASTMD1785"
    assert available_catalogs_for_material("PVC", "EU") == ["PVC_EN1452"]
    assert available_catalogs_for_material("PVC", "US") == ["PVC_ASTMD1785"]
    with pytest.raises(ValidationError):
        validate_line_input(_inp("service_water", "PVCU_US", "PVC_ASTMD1785", jurisdiction="EU"))
    with pytest.raises(ValidationError):
        validate_line_input(_inp("service_water", "PVC", "PVC_EN1452", jurisdiction="US"))


def test_brazil_does_not_offer_eu_or_us_pvc_catalogs_without_dataset():
    ready = get_calculation_ready_materials("service_water", "Brazil")

    assert "PVC" not in ready
    assert "PVCU_US" not in ready
    assert available_catalogs_for_material("PVC", "Brazil") == []
    with pytest.raises(DatasetMissingError):
        validate_line_input(_inp("service_water", "PVC", "PVC_EN1452", jurisdiction="Brazil"))


def test_fire_water_generic_pvc_is_blocked():
    inp = _inp("fire_water", "PVC", "PVC_EN1452")

    with pytest.raises(ValidationError):
        validate_line_input(inp)
