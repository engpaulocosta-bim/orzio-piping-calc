from sidct.ui.form_behavior import get_calc_mode_label, get_form_behavior, get_field_meta


def test_gravity_system_hides_pressure_and_requires_slope():
    behavior = get_form_behavior("rainwater", "calculate_new")

    assert "slope_mm_m" in behavior.visible_fields
    assert "slope_mm_m" in behavior.required_fields
    assert "P_oper_bar" in behavior.hidden_fields
    assert "P_design_bar" in behavior.hidden_fields
    assert "vacuum_target_mbara" in behavior.hidden_fields


def test_check_received_mode_requires_received_line_fields():
    behavior = get_form_behavior("potable_water", "check_received")

    assert "DN_received_mm" in behavior.required_fields
    assert "schedule_or_wall_received" in behavior.required_fields
    assert "DN_received_mm" in behavior.visible_fields
    assert "schedule_or_wall_received" in behavior.visible_fields


def test_vacuum_system_requires_vacuum_target_and_hides_slope():
    behavior = get_form_behavior("vacuum_utility", "calculate_new")

    assert "vacuum_target_mbara" in behavior.required_fields
    assert "slope_mm_m" in behavior.hidden_fields
    assert "allowable_pressure_drop_bar" in behavior.hidden_fields


def test_field_metadata_and_mode_labels_are_localized():
    assert get_field_meta("service").label("pt-BR") == "Sistema"
    assert get_calc_mode_label("check_received", "pt-BR") == "Conferir linha recebida"
