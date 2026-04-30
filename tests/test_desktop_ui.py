"""Headless smoke tests for the PySide desktop UI."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from sidct.project import Project
    from sidct.ui.desktop_app import MainWindow
except ImportError:  # pragma: no cover - optional desktop dependency.
    QApplication = None
    MainWindow = None
    Project = None


@pytest.fixture
def desktop_window(tmp_path):
    if QApplication is None or MainWindow is None:
        pytest.skip("PySide6 is not installed")
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.settings.clear()
    yield window
    window.window.hide()
    app.processEvents()


def test_desktop_opens_with_guidance_and_audit_tab(desktop_window):
    assert desktop_window.window.minimumWidth() == 900
    assert desktop_window.window.minimumHeight() == 600
    assert desktop_window.line_state_panel.text()
    assert desktop_window.tabs.count() >= 5


def test_desktop_language_switch_updates_visible_labels(desktop_window):
    desktop_window.set_language("en")
    assert desktop_window.project_panel.filter_box.placeholderText() == "Filter lines"
    desktop_window.set_language("pt-BR")
    assert desktop_window.project_panel.filter_box.placeholderText() == "Filtrar linhas"


def test_desktop_calculates_default_line_and_records_audit(desktop_window):
    desktop_window.calculate_current()
    line = desktop_window._current_line()
    assert line is not None
    assert line.last_report_context is not None
    assert desktop_window.project.audit_log
    assert "audit" in line.last_report_context.dataset_provenance


def test_desktop_save_and_open_roundtrip(tmp_path, desktop_window):
    desktop_window.calculate_current()
    path = tmp_path / "project.sidct.json"
    desktop_window.current_path = path
    assert desktop_window.save_project()

    second = MainWindow()
    second.project = Project.model_validate_json(path.read_text(encoding="utf-8"))
    assert second.project.audit_log
    second.window.hide()


def test_desktop_batch_reader_accepts_csv(tmp_path, desktop_window):
    path = tmp_path / "batch.csv"
    path.write_text(
        "project_name,line_tag,service,project_profile,material,P_oper_bar,T_oper_c,"
        "P_design_bar,T_design_c,flow_rate,flow_rate_basis,line_length_m,"
        "dimensional_catalog,jurisdiction\n"
        "P,L-B01,service_water,industrial_utilities_eu,A106 GrB,3,20,6,40,10,m3/h,50,"
        "ASME_B36_10M,EU\n",
        encoding="utf-8",
    )
    rows = desktop_window._read_batch_rows(path)
    assert rows[0]["line_tag"] == "L-B01"
