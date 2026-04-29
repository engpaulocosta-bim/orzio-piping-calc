"""SIDCT desktop application built with PySide6."""
from __future__ import annotations

import sys
from pathlib import Path

from sidct.materials import default_catalog_for_material
from sidct.models import FittingItem, LineInput
from sidct.project import Project, create_default_project, load_project, save_project
from sidct.reports.exports import export_project_csv, export_project_xlsx
from sidct.reports.memorial_pdf import generate_pdf
from sidct.system_pipe_mapping import get_calculation_ready_materials, get_mapping_notes, get_material_options
from sidct.ui.form_behavior import (
    get_calc_mode_label,
    get_calc_modes,
    get_field_meta,
    get_form_behavior,
    list_fields,
)


SERVICES = [
    "compressed_air",
    "natural_gas",
    "potable_water",
    "service_water",
    "osmotized_water",
    "chilled_water",
    "condenser_water",
    "vacuum_utility",
    "sanitary_drainage",
    "rainwater",
    "fire_water",
]

PROFILES = [
    "glass_factory_industrial_eu",
    "glass_factory_industrial_us",
    "industrial_utilities_eu",
    "datacentre_building_services_eu",
    "datacentre_building_services_us",
    "fire_protection_en",
    "fire_protection_us",
]

CATALOGS = ["ASME_B36_10M", "ASME_B36_19M", "PVC_EN1452", "PVC_ASTMD1785"]
MATERIALS = ["A106 GrB", "A53 GrB", "A312 TP304", "A312 TP316", "PVC", "PVCU_US"]

SERVICE_COLORS = {
    "potable_water": "#2FBF9F",
    "service_water": "#0F8B8D",
    "osmotized_water": "#7DD3FC",
    "chilled_water": "#2563EB",
    "condenser_water": "#38BDF8",
    "compressed_air": "#0079B8",
    "natural_gas": "#F5B700",
    "vacuum_utility": "#8A8F98",
    "sanitary_drainage": "#9A6A2F",
    "rainwater": "#4F8A10",
    "fire_water": "#D62828",
}

SERVICE_LABELS = {
    "en": {
        "compressed_air": "Compressed air",
        "natural_gas": "Natural gas",
        "potable_water": "Potable water",
        "service_water": "Service water",
        "osmotized_water": "Osmotized / treated water",
        "chilled_water": "Chilled water",
        "condenser_water": "Condenser water",
        "vacuum_utility": "Vacuum",
        "sanitary_drainage": "Sanitary drainage",
        "rainwater": "Rainwater",
        "fire_water": "Fire protection",
    },
    "pt-BR": {
        "compressed_air": "Ar comprimido",
        "natural_gas": "Gas natural",
        "potable_water": "Agua potavel",
        "service_water": "Agua de servico",
        "osmotized_water": "Agua osmotizada / tratada",
        "chilled_water": "Agua gelada",
        "condenser_water": "Agua de condensacao",
        "vacuum_utility": "Vacuo",
        "sanitary_drainage": "Esgoto sanitario",
        "rainwater": "Aguas pluviais",
        "fire_water": "Anti-incendio",
    },
}

STATUS_LABELS = {
    "en": {
        "DRAFT": "Draft",
        "CALCULATED": "Calculated",
        "APPROVED": "Approved",
        "CONSERVATIVE": "Conservative",
        "INSUFFICIENT": "Insufficient",
        "ERROR": "Error",
    },
    "pt-BR": {
        "DRAFT": "Rascunho",
        "CALCULATED": "Calculada",
        "APPROVED": "Aprovada",
        "CONSERVATIVE": "Conservadora",
        "INSUFFICIENT": "Insuficiente",
        "ERROR": "Erro",
    },
}

TRANSLATIONS = {
    "en": {
        "title": "SIDCT - Industrial Piping Desktop",
        "file": "File",
        "project_menu": "Project",
        "export": "Export",
        "options": "Options",
        "language": "Language",
        "new": "New",
        "open": "Open",
        "save": "Save",
        "save_as": "Save As",
        "add_line": "Add Line",
        "duplicate": "Duplicate",
        "export_pdf": "Export PDF",
        "export_csv": "Export CSV",
        "export_xlsx": "Export XLSX",
        "calculate": "Calculate Line",
        "project_and_line": "Project and Line",
        "service_and_material": "Service and Material",
        "system_requirements": "System Requirements",
        "operating_conditions": "Operating Conditions",
        "flow_geometry": "Flow and Geometry",
        "criteria_received": "Criteria and Received Line",
        "notes": "Notes",
        "project": "Project",
        "line_tag": "Line tag",
        "service": "Service",
        "profile": "Profile",
        "jurisdiction": "Jurisdiction",
        "material": "Material",
        "catalog": "Catalog",
        "guidance": "Guidance",
        "p_oper": "P operating [barg]",
        "t_oper": "T operating [C]",
        "p_design": "P design [barg]",
        "t_design": "T design [C]",
        "flow": "Flow",
        "flow_unit": "Flow unit",
        "length": "Length [m]",
        "elevation": "Elevation delta [m]",
        "slope": "Slope [mm/m]",
        "vacuum": "Vacuum target [mbar abs]",
        "ca": "Corrosion allowance [mm]",
        "dp_allow": "Allowable dP [bar]",
        "dn_received": "DN received [mm]",
        "schedule_received": "Schedule received",
        "elbows": "90 LR elbows",
        "summary": "Summary",
        "results": "Results",
        "warnings": "Warnings",
        "assumptions": "Assumptions",
        "field": "Field",
        "value": "Value",
        "metric": "Metric",
        "ready": "Ready",
        "no_warnings": "No warnings.",
        "no_assumptions": "No assumptions declared.",
        "validation_missing_title": "Required fields missing",
        "validation_missing_intro": "Missing required fields for this calculation:",
    },
    "pt-BR": {
        "title": "SIDCT - Tubagens Industriais",
        "file": "Arquivo",
        "project_menu": "Projeto",
        "export": "Exportar",
        "options": "Opcoes",
        "language": "Idioma",
        "new": "Novo",
        "open": "Abrir",
        "save": "Guardar",
        "save_as": "Guardar Como",
        "add_line": "Adicionar Linha",
        "duplicate": "Duplicar",
        "export_pdf": "Exportar PDF",
        "export_csv": "Exportar CSV",
        "export_xlsx": "Exportar XLSX",
        "calculate": "Calcular Linha",
        "project_and_line": "Projeto e Linha",
        "service_and_material": "Sistema e Material",
        "system_requirements": "Requisitos do Sistema",
        "operating_conditions": "Condicoes de Operacao",
        "flow_geometry": "Caudal e Geometria",
        "criteria_received": "Criterios e Linha Recebida",
        "notes": "Notas",
        "project": "Projeto",
        "line_tag": "Tag da linha",
        "service": "Sistema",
        "profile": "Perfil",
        "jurisdiction": "Jurisdicao",
        "material": "Material",
        "catalog": "Catalogo",
        "guidance": "Orientacao",
        "p_oper": "P operacao [barg]",
        "t_oper": "T operacao [C]",
        "p_design": "P projeto [barg]",
        "t_design": "T projeto [C]",
        "flow": "Caudal",
        "flow_unit": "Unidade",
        "length": "Comprimento [m]",
        "elevation": "Desnivel [m]",
        "slope": "Declive [mm/m]",
        "vacuum": "Vacio alvo [mbar abs]",
        "ca": "Sobreespessura corrosao [mm]",
        "dp_allow": "dP admissivel [bar]",
        "dn_received": "DN recebido [mm]",
        "schedule_received": "Schedule recebido",
        "elbows": "Cotovelos 90 LR",
        "summary": "Resumo",
        "results": "Resultados",
        "warnings": "Avisos",
        "assumptions": "Premissas",
        "field": "Campo",
        "value": "Valor",
        "metric": "Metrica",
        "ready": "Pronto",
        "no_warnings": "Sem avisos.",
        "no_assumptions": "Sem premissas declaradas.",
        "validation_missing_title": "Campos obrigatorios em falta",
        "validation_missing_intro": "Faltam campos obrigatorios para calcular esta linha:",
    },
}


class MissingDesktopDependency(RuntimeError):
    pass


def _require_qt():
    try:
        from PySide6.QtCore import QSettings, Qt
        from PySide6.QtGui import QAction, QBrush, QColor, QFont
        from PySide6.QtWidgets import (
            QApplication,
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QFrame,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QSplitter,
            QStatusBar,
            QTableWidget,
            QTableWidgetItem,
            QTabWidget,
            QTextEdit,
            QToolBar,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise MissingDesktopDependency(
            "PySide6 is required for the desktop app. Install it with: pip install PySide6"
        ) from exc
    return locals()


def _spin(value: float, minimum: float = -1e6, maximum: float = 1e6, step: float = 1.0, decimals: int = 3):
    qt = _require_qt()
    widget = qt["QDoubleSpinBox"]()
    widget.setRange(minimum, maximum)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    return widget


class MainWindow:
    def __init__(self):
        qt = _require_qt()
        self.qt = qt
        QMainWindow = qt["QMainWindow"]

        class _Window(QMainWindow):
            pass

        QSettings = qt["QSettings"]
        self.settings = QSettings("SIDCT", "SIDCT Desktop")
        self.language = self.settings.value("language", "pt-BR")
        if self.language not in TRANSLATIONS:
            self.language = "pt-BR"
        self.actions: dict[str, object] = {}
        self.form_labels: dict[str, object] = {}
        self.form_rows: dict[str, tuple[object, object]] = {}
        self.field_widgets: dict[str, object] = {}
        self.group_boxes: dict[str, object] = {}
        self.result_cards: dict[str, object] = {}

        self.window = _Window()
        self.window.setWindowTitle(self.tr("title"))
        self.window.resize(1360, 820)
        self.project: Project = create_default_project("SIDCT Project")
        self.current_path: Path | None = None
        self.current_line_id: str | None = None
        self._build_ui()
        self._seed_default_line()
        self.refresh_project_tree()

    def tr(self, key: str) -> str:
        return TRANSLATIONS.get(self.language, TRANSLATIONS["en"]).get(key, key)

    def service_label(self, service_id: str) -> str:
        labels = SERVICE_LABELS.get(self.language, SERVICE_LABELS["en"])
        return labels.get(service_id, service_id)

    def status_label(self, status: str) -> str:
        labels = STATUS_LABELS.get(self.language, STATUS_LABELS["en"])
        return labels.get(str(status).upper(), str(status))

    def _field_label_text(self, field_id: str, required: bool = False) -> str:
        label = get_field_meta(field_id).label(self.language)
        if required:
            return f"{label} <span style='color:#B42318;font-weight:800'>*</span>"
        return label

    def _selected_service(self) -> str:
        if not hasattr(self, "service"):
            return SERVICES[0]
        data = self.service.currentData()
        return data if data else self.service.currentText()

    def _selected_mode(self) -> str:
        if not hasattr(self, "operation_mode"):
            return "calculate_new"
        data = self.operation_mode.currentData()
        return data if data else self.operation_mode.currentText()

    def show(self) -> None:
        self.window.show()

    def _build_ui(self) -> None:
        qt = self.qt
        QWidget = qt["QWidget"]
        QHBoxLayout = qt["QHBoxLayout"]
        QVBoxLayout = qt["QVBoxLayout"]
        QGridLayout = qt["QGridLayout"]
        QSplitter = qt["QSplitter"]
        Qt = qt["Qt"]
        QListWidget = qt["QListWidget"]
        QTabWidget = qt["QTabWidget"]
        QTableWidget = qt["QTableWidget"]
        QTextEdit = qt["QTextEdit"]
        QStatusBar = qt["QStatusBar"]

        self._apply_light_theme()
        self._build_actions()

        central = QWidget()
        root = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.project_label = qt["QLabel"]("Project")
        self.project_tree = QListWidget()
        self.project_tree.itemSelectionChanged.connect(self._on_tree_selection)
        left_layout.addWidget(self.project_label)
        left_layout.addWidget(self.project_tree)
        splitter.addWidget(left)

        self.form_panel = self._build_form()
        splitter.addWidget(self.form_panel)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        cards = QGridLayout()
        for index, (key, title) in enumerate([
            ("status", "Status"),
            ("dn", "DN"),
            ("material", "Material"),
            ("schedule", "Schedule"),
            ("criterion", "Criterion"),
        ]):
            frame = qt["QFrame"]()
            frame.setObjectName("resultCard")
            card_layout = QVBoxLayout(frame)
            card_title = qt["QLabel"](title)
            card_title.setObjectName("resultCardTitle")
            card_value = qt["QLabel"]("N/A")
            card_value.setObjectName("resultCardValue")
            card_value.setWordWrap(True)
            card_layout.addWidget(card_title)
            card_layout.addWidget(card_value)
            self.result_cards[f"{key}_title"] = card_title
            self.result_cards[key] = card_value
            cards.addWidget(frame, index // 3, index % 3)
        right_layout.addLayout(cards)
        self.tabs = QTabWidget()
        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels([self.tr("field"), self.tr("value")])
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels([self.tr("metric"), self.tr("value")])
        self.warnings_box = QTextEdit()
        self.warnings_box.setReadOnly(True)
        self.assumptions_box = QTextEdit()
        self.assumptions_box.setReadOnly(True)
        self.tabs.addTab(self.summary_table, self.tr("summary"))
        self.tabs.addTab(self.results_table, self.tr("results"))
        self.tabs.addTab(self.warnings_box, self.tr("warnings"))
        self.tabs.addTab(self.assumptions_box, self.tr("assumptions"))
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right)
        splitter.setSizes([260, 560, 540])

        self.window.setCentralWidget(central)
        self.window.setStatusBar(QStatusBar())
        self._set_status(self.tr("ready"))

    def _apply_light_theme(self) -> None:
        self.window.setStyleSheet("""
            QMainWindow, QWidget {
                background: #EEF4F8;
                color: #172033;
                font-size: 10pt;
            }
            QMenuBar, QMenu {
                background: #F7FAFC;
                color: #172033;
                border-bottom: 1px solid #D7E2EA;
            }
            QToolBar {
                background: #F7FAFC;
                border: 0;
                border-bottom: 1px solid #D7E2EA;
                spacing: 6px;
                padding: 6px;
            }
            QToolButton, QPushButton {
                background: #FFFFFF;
                border: 1px solid #CBD8E3;
                border-radius: 6px;
                padding: 6px 10px;
                color: #172033;
                min-width: 76px;
            }
            QPushButton#calculateButton {
                background: #146C94;
                color: white;
                border: 1px solid #0F5D80;
                font-weight: 700;
                padding: 10px 14px;
            }
            QPushButton#calculateButton:hover {
                background: #0F5D80;
            }
            QGroupBox {
                background: #FFFFFF;
                border: 1px solid #D7E2EA;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #24455F;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit {
                background: #FFFFFF;
                border: 1px solid #C9D6E2;
                border-radius: 5px;
                padding: 4px 7px;
                color: #172033;
            }
            QListWidget, QTableWidget, QTabWidget::pane {
                background: #FFFFFF;
                border: 1px solid #D7E2EA;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 7px;
                border-radius: 5px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #DDEEFF;
                color: #0B3551;
            }
            QHeaderView::section {
                background: #E3ECF3;
                color: #172033;
                border: 0;
                padding: 5px;
                font-weight: 700;
            }
            QFrame#resultCard {
                background: #FFFFFF;
                border: 1px solid #D7E2EA;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel#resultCardTitle {
                color: #52677A;
                font-size: 8.5pt;
                font-weight: 700;
            }
            QLabel#resultCardValue {
                color: #0B3551;
                font-size: 12pt;
                font-weight: 800;
            }
            QLabel#requirementsPanel {
                background: #F4F9FC;
                border: 1px solid #CFE0EC;
                border-left: 4px solid #146C94;
                border-radius: 7px;
                padding: 8px;
                color: #172033;
            }
            QTabBar::tab {
                background: #E6EEF5;
                border: 1px solid #D7E2EA;
                border-bottom: 0;
                padding: 7px 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #146C94;
                font-weight: 700;
            }
        """)

    def _build_actions(self) -> None:
        qt = self.qt
        QAction = qt["QAction"]
        QToolBar = qt["QToolBar"]
        toolbar = QToolBar("Main")
        self.window.addToolBar(toolbar)
        menu_file = self.window.menuBar().addMenu(self.tr("file"))
        menu_project = self.window.menuBar().addMenu(self.tr("project_menu"))
        menu_export = self.window.menuBar().addMenu(self.tr("export"))
        menu_options = self.window.menuBar().addMenu(self.tr("options"))
        self.menus = {
            "file": menu_file,
            "project_menu": menu_project,
            "export": menu_export,
            "options": menu_options,
        }

        action_groups = [
            [
                ("new", self.new_project, menu_file),
                ("open", self.open_project, menu_file),
                ("save", self.save_project, menu_file),
                ("save_as", self.save_project_as, menu_file),
            ],
            [
                ("add_line", self.add_line, menu_project),
                ("duplicate", self.duplicate_line, menu_project),
            ],
            [
                ("export_pdf", self.export_pdf, menu_export),
                ("export_csv", self.export_csv, menu_export),
                ("export_xlsx", self.export_xlsx, menu_export),
            ],
        ]
        for group_index, actions in enumerate(action_groups):
            if group_index:
                toolbar.addSeparator()
            for key, slot, menu in actions:
                act = QAction(self.tr(key), self.window)
                act.triggered.connect(slot)
                menu.addAction(act)
                toolbar.addAction(act)
                self.actions[key] = act

        language_menu = menu_options.addMenu(self.tr("language"))
        self.menus["language"] = language_menu
        for language_key, label in [("en", "English"), ("pt-BR", "Portugues (PT-BR)")]:
            act = QAction(label, self.window)
            act.setCheckable(True)
            act.setChecked(self.language == language_key)
            act.triggered.connect(lambda checked=False, lang=language_key: self.set_language(lang))
            language_menu.addAction(act)
            self.actions[f"language_{language_key}"] = act

    def set_language(self, language: str) -> None:
        if language not in TRANSLATIONS:
            return
        self.language = language
        self.settings.setValue("language", language)
        self._apply_language()

    def _apply_language(self) -> None:
        self.window.setWindowTitle(self.tr("title"))
        for key, menu in getattr(self, "menus", {}).items():
            if key in ("language",):
                menu.setTitle(self.tr(key))
            elif key in TRANSLATIONS[self.language]:
                menu.setTitle(self.tr(key))
        for key, action in self.actions.items():
            if key.startswith("language_"):
                language = key.removeprefix("language_")
                action.setChecked(language == self.language)
            elif key in TRANSLATIONS[self.language]:
                action.setText(self.tr(key))
        if hasattr(self, "service"):
            self._refresh_service_labels()
        if hasattr(self, "operation_mode"):
            self._refresh_mode_labels()
        for key, box in self.group_boxes.items():
            box.setTitle(self.tr(key))
        if hasattr(self, "calculate_button"):
            self.calculate_button.setText(self.tr("calculate"))
        if "guidance" in self.form_labels:
            self.form_labels["guidance"].setText(self.tr("guidance"))
        if self.result_cards:
            for key, title in [
                ("status_title", "Status"),
                ("dn_title", "DN"),
                ("material_title", self.tr("material")),
                ("schedule_title", "Schedule"),
                ("criterion_title", "Criterio" if self.language == "pt-BR" else "Criterion"),
            ]:
                if key in self.result_cards:
                    self.result_cards[key].setText(title)
        if hasattr(self, "tabs"):
            self.tabs.setTabText(0, self.tr("summary"))
            self.tabs.setTabText(1, self.tr("results"))
            self.tabs.setTabText(2, self.tr("warnings"))
            self.tabs.setTabText(3, self.tr("assumptions"))
        if hasattr(self, "summary_table"):
            self.summary_table.setHorizontalHeaderLabels([self.tr("field"), self.tr("value")])
        if hasattr(self, "results_table"):
            self.results_table.setHorizontalHeaderLabels([self.tr("metric"), self.tr("value")])
        if hasattr(self, "material"):
            self._refresh_material_options(self._selected_material())
        if hasattr(self, "field_widgets"):
            self._apply_form_behavior()
        self.refresh_project_tree()
        self._set_status(self.tr("ready"))

    def _build_form(self):
        qt = self.qt
        QWidget = qt["QWidget"]
        QVBoxLayout = qt["QVBoxLayout"]
        QFormLayout = qt["QFormLayout"]
        QGroupBox = qt["QGroupBox"]
        QComboBox = qt["QComboBox"]
        QLineEdit = qt["QLineEdit"]
        QTextEdit = qt["QTextEdit"]
        QSpinBox = qt["QSpinBox"]

        panel = QWidget()
        layout = QVBoxLayout(panel)

        def group(title: str):
            box = QGroupBox(title)
            form = QFormLayout(box)
            layout.addWidget(box)
            return form

        def add_row(form, field_id: str, widget) -> None:
            label = qt["QLabel"](self._field_label_text(field_id))
            label.setTextFormat(self.qt["Qt"].RichText)
            meta = get_field_meta(field_id)
            help_text = meta.help(self.language)
            label.setToolTip(help_text)
            widget.setToolTip(help_text)
            self.form_labels[field_id] = label
            self.form_rows[field_id] = (label, widget)
            self.field_widgets[field_id] = widget
            form.addRow(label, widget)

        self.project_name = QLineEdit("SIDCT Project")
        self.line_tag = QLineEdit("L-001")
        form = group(self.tr("project_and_line"))
        self.group_boxes["project_and_line"] = form.parentWidget()
        self.operation_mode = QComboBox()
        for mode in get_calc_modes():
            self.operation_mode.addItem(get_calc_mode_label(mode, self.language), mode)
        self.operation_mode.currentIndexChanged.connect(self._apply_form_behavior)
        add_row(form, "project_name", self.project_name)
        add_row(form, "line_tag", self.line_tag)
        add_row(form, "operation_mode", self.operation_mode)

        self.service = QComboBox()
        for service in SERVICES:
            self.service.addItem(self.service_label(service), service)
        self.service.currentIndexChanged.connect(self._service_or_region_changed)
        self.profile = QComboBox()
        self.profile.addItems(PROFILES)
        self.jurisdiction = QComboBox()
        self.jurisdiction.addItems(["EU", "US", "Brazil", "international"])
        self.jurisdiction.currentTextChanged.connect(self._service_or_region_changed)
        self.material = QComboBox()
        self.material.currentTextChanged.connect(self._material_changed)
        self.catalog = QComboBox()
        self.catalog.addItems(CATALOGS)
        self.material_guidance = qt["QLabel"]("")
        self.material_guidance.setWordWrap(True)
        form = group(self.tr("service_and_material"))
        self.group_boxes["service_and_material"] = form.parentWidget()
        add_row(form, "service", self.service)
        add_row(form, "project_profile", self.profile)
        add_row(form, "jurisdiction", self.jurisdiction)
        add_row(form, "material", self.material)
        add_row(form, "dimensional_catalog", self.catalog)
        guidance_label = qt["QLabel"](self.tr("guidance"))
        self.form_labels["guidance"] = guidance_label
        form.addRow(guidance_label, self.material_guidance)

        requirements = group("Requisitos do Sistema" if self.language == "pt-BR" else "System Requirements")
        self.group_boxes["system_requirements"] = requirements.parentWidget()
        self.requirements_panel = qt["QLabel"]("")
        self.requirements_panel.setObjectName("requirementsPanel")
        self.requirements_panel.setWordWrap(True)
        requirements.addRow(self.requirements_panel)

        form = group(self.tr("operating_conditions"))
        self.group_boxes["operating_conditions"] = form.parentWidget()
        self.P_oper = _spin(6.0, minimum=0.0, step=0.5, decimals=3)
        self.T_oper = _spin(20.0, step=1.0, decimals=2)
        self.P_design = _spin(10.0, minimum=0.0, step=0.5, decimals=3)
        self.T_design = _spin(40.0, step=1.0, decimals=2)
        add_row(form, "P_oper_bar", self.P_oper)
        add_row(form, "T_oper_c", self.T_oper)
        add_row(form, "P_design_bar", self.P_design)
        add_row(form, "T_design_c", self.T_design)

        form = group(self.tr("flow_geometry"))
        self.group_boxes["flow_geometry"] = form.parentWidget()
        self.flow = _spin(100.0, minimum=0.0001, step=1.0, decimals=3)
        self.flow_basis = QComboBox()
        self.flow_basis.addItems(["m3/h", "L/s", "gpm", "Nm3/h", "Sm3/h", "kg/s"])
        self.length = _spin(100.0, minimum=0.01, step=1.0, decimals=3)
        self.elevation = _spin(0.0, step=0.5, decimals=3)
        self.slope = _spin(10.0, minimum=0.0, step=1.0, decimals=3)
        self.vacuum = _spin(10.0, minimum=0.0, step=1.0, decimals=3)
        add_row(form, "flow_rate", self.flow)
        add_row(form, "flow_rate_basis", self.flow_basis)
        add_row(form, "line_length_m", self.length)
        add_row(form, "elevation_delta_m", self.elevation)
        add_row(form, "slope_mm_m", self.slope)
        add_row(form, "vacuum_target_mbara", self.vacuum)

        form = group(self.tr("criteria_received"))
        self.group_boxes["criteria_received"] = form.parentWidget()
        self.ca = _spin(1.5, minimum=0.0, step=0.5, decimals=3)
        self.dp_allow = _spin(0.5, minimum=0.0, step=0.05, decimals=4)
        self.dn_received = _spin(100.0, minimum=0.0, step=25.0, decimals=3)
        self.schedule_received = QLineEdit("")
        self.elbows = QSpinBox()
        self.elbows.setRange(0, 999)
        self.elbows.setValue(2)
        add_row(form, "corrosion_allowance_mm", self.ca)
        add_row(form, "allowable_pressure_drop_bar", self.dp_allow)
        add_row(form, "DN_received_mm", self.dn_received)
        add_row(form, "schedule_or_wall_received", self.schedule_received)
        add_row(form, "fittings_90lr", self.elbows)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        form = group(self.tr("notes"))
        self.group_boxes["notes"] = form.parentWidget()
        add_row(form, "design_notes", self.notes)

        self.calculate_button = qt["QPushButton"](self.tr("calculate"))
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.clicked.connect(self.calculate_current)
        layout.addWidget(self.calculate_button)
        layout.addStretch(1)
        self._refresh_material_options()
        self._apply_form_behavior()
        return panel

    def _seed_default_line(self) -> None:
        route = self.project.routes[0]
        line = route.add_line(self._form_to_input())
        self.current_line_id = line.line_id

    def _refresh_service_labels(self) -> None:
        current = self._selected_service()
        self.service.blockSignals(True)
        self.service.clear()
        for service in SERVICES:
            self.service.addItem(self.service_label(service), service)
        index = self.service.findData(current)
        if index >= 0:
            self.service.setCurrentIndex(index)
        self.service.blockSignals(False)

    def _refresh_mode_labels(self) -> None:
        current = self._selected_mode()
        self.operation_mode.blockSignals(True)
        self.operation_mode.clear()
        for mode in get_calc_modes():
            self.operation_mode.addItem(get_calc_mode_label(mode, self.language), mode)
        index = self.operation_mode.findData(current)
        if index >= 0:
            self.operation_mode.setCurrentIndex(index)
        self.operation_mode.blockSignals(False)

    def _active_form_behavior(self):
        return get_form_behavior(self._selected_service(), self._selected_mode())

    def _apply_form_behavior(self) -> None:
        if not getattr(self, "field_widgets", None):
            return
        behavior = self._active_form_behavior()
        visible = set(behavior.visible_fields)
        required = set(behavior.required_fields)
        disabled = set(behavior.disabled_fields)
        warning = set(behavior.warning_fields)
        for field_id in list_fields():
            row = self.form_rows.get(field_id)
            if not row:
                continue
            label, widget = row
            is_visible = field_id in visible and field_id not in set(behavior.hidden_fields)
            label.setVisible(is_visible)
            widget.setVisible(is_visible)
            widget.setEnabled(is_visible and field_id not in disabled)
            label.setText(self._field_label_text(field_id, field_id in required))
            meta = get_field_meta(field_id)
            help_text = meta.help(self.language)
            if field_id in warning:
                help_text = f"{help_text}\nWarning: confirm applicability for this system."
            label.setToolTip(help_text)
            widget.setToolTip(help_text)
        self._update_requirements_panel(behavior)

    def _update_requirements_panel(self, behavior) -> None:
        if not hasattr(self, "requirements_panel"):
            return
        hidden = [get_field_meta(field).label(self.language) for field in behavior.hidden_fields if field in self.form_rows]
        required = [get_field_meta(field).label(self.language) for field in behavior.required_fields if field in self.form_rows]
        if self.language == "pt-BR":
            text = (
                f"<b>Sistema:</b> {self.service_label(behavior.system_id)}<br>"
                f"<b>Regime:</b> {behavior.regime(self.language)}<br>"
                f"<b>Obrigatorios:</b> {', '.join(required) if required else 'Nenhum'}<br>"
                f"<b>Nao utilizados:</b> {', '.join(hidden[:8]) if hidden else 'Nenhum'}<br>"
                f"<b>Nota:</b> {behavior.explanatory_note(self.language)}"
            )
        else:
            text = (
                f"<b>System:</b> {self.service_label(behavior.system_id)}<br>"
                f"<b>Regime:</b> {behavior.regime(self.language)}<br>"
                f"<b>Required:</b> {', '.join(required) if required else 'None'}<br>"
                f"<b>Not used:</b> {', '.join(hidden[:8]) if hidden else 'None'}<br>"
                f"<b>Note:</b> {behavior.explanatory_note(self.language)}"
            )
        self.requirements_panel.setText(text)

    def _material_changed(self) -> None:
        catalog = default_catalog_for_material(self._selected_material(), self.jurisdiction.currentText())
        if catalog:
            idx = self.catalog.findText(catalog)
            if idx >= 0:
                self.catalog.setCurrentIndex(idx)

    def _selected_material(self) -> str:
        data = self.material.currentData()
        return data if data else self.material.currentText()

    def _service_or_region_changed(self) -> None:
        self._refresh_material_options()
        self._apply_form_behavior()

    def _refresh_material_options(self, preferred_material: str | None = None) -> None:
        if not hasattr(self, "material"):
            return
        service = self._selected_service()
        region = self.jurisdiction.currentText()
        current = preferred_material or self._selected_material()
        options = get_material_options(service, region)
        ready = [option for option in options if option.calculation_ready and option.sidct_material]
        self.material.blockSignals(True)
        self.material.clear()
        for option in ready:
            label = f"{option.display_name} ({option.status})"
            self.material.addItem(label, option.sidct_material)
        if not ready:
            for material in MATERIALS:
                self.material.addItem(material, material)
        target = -1
        for idx in range(self.material.count()):
            if self.material.itemData(idx) == current or self.material.itemText(idx) == current:
                target = idx
                break
            if self.material.itemText(idx).startswith(str(current)):
                target = idx
                break
        if target >= 0:
            self.material.setCurrentIndex(target)
        self.material.blockSignals(False)
        notes = get_mapping_notes(service, region)
        fallback = "Sem orientacao de material disponivel." if self.language == "pt-BR" else "No material guidance available."
        self.material_guidance.setText(" | ".join(notes[:3]) if notes else fallback)
        self._material_changed()

    def _form_to_input(self) -> LineInput:
        fittings = []
        if self.elbows.value() > 0:
            fittings.append(FittingItem(fitting_type="90_LR_ELBOW", quantity=self.elbows.value()))
        service = self._selected_service()
        return LineInput(
            project_name=self.project_name.text().strip() or "SIDCT Project",
            line_tag=self.line_tag.text().strip() or "L-001",
            service=service,
            project_profile=self.profile.currentText(),
            jurisdiction=self.jurisdiction.currentText(),
            fluid_name=service,
            P_oper_bar=self.P_oper.value(),
            T_oper_c=self.T_oper.value(),
            P_design_bar=self.P_design.value(),
            T_design_c=self.T_design.value(),
            flow_rate=self.flow.value(),
            flow_rate_basis=self.flow_basis.currentText(),
            line_length_m=self.length.value(),
            elevation_delta_m=self.elevation.value(),
            material=self._selected_material(),
            dimensional_catalog=self.catalog.currentText(),
            corrosion_allowance_mm=self.ca.value(),
            fittings=fittings,
            allowable_pressure_drop_bar=self.dp_allow.value() or None,
            DN_received_mm=self.dn_received.value() or None,
            schedule_or_wall_received=self.schedule_received.text().strip() or None,
            slope_mm_m=self.slope.value() if service in ("sanitary_drainage", "rainwater") else None,
            vacuum_target_mbara=self.vacuum.value() if service == "vacuum_utility" else None,
            design_notes=self.notes.toPlainText(),
            operation_mode=self._selected_mode(),
        )

    def _input_to_form(self, inp: LineInput) -> None:
        self.project_name.setText(inp.project_name)
        self.line_tag.setText(inp.line_tag)
        mode_idx = self.operation_mode.findData(inp.operation_mode)
        if mode_idx >= 0:
            self.operation_mode.setCurrentIndex(mode_idx)
        service_idx = self.service.findData(inp.service)
        if service_idx >= 0:
            self.service.setCurrentIndex(service_idx)
        for combo, value in [
            (self.profile, inp.project_profile),
            (self.jurisdiction, inp.jurisdiction),
            (self.catalog, inp.dimensional_catalog),
            (self.flow_basis, inp.flow_rate_basis),
        ]:
            idx = combo.findText(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        self._refresh_material_options(inp.material)
        self.P_oper.setValue(inp.P_oper_bar)
        self.T_oper.setValue(inp.T_oper_c)
        self.P_design.setValue(inp.P_design_bar)
        self.T_design.setValue(inp.T_design_c)
        self.flow.setValue(inp.flow_rate)
        self.length.setValue(inp.line_length_m)
        self.elevation.setValue(inp.elevation_delta_m)
        self.ca.setValue(inp.corrosion_allowance_mm or 0.0)
        self.dp_allow.setValue(inp.allowable_pressure_drop_bar or 0.0)
        self.dn_received.setValue(inp.DN_received_mm or 0.0)
        self.schedule_received.setText(inp.schedule_or_wall_received or "")
        self.slope.setValue(inp.slope_mm_m or 0.0)
        self.vacuum.setValue(inp.vacuum_target_mbara or 0.0)
        self.notes.setPlainText(inp.design_notes)
        self._apply_form_behavior()

    def refresh_project_tree(self) -> None:
        qt = self.qt
        QListWidgetItem = qt["QListWidgetItem"]
        QColor = qt["QColor"]
        QBrush = qt["QBrush"]
        QFont = qt["QFont"]
        self.project_tree.clear()
        self.project_label.setText(f"{self.tr('project')}: {self.project.name}")
        for route in self.project.routes:
            route_item = QListWidgetItem(f"[Route] {route.name}")
            route_item.setData(256, ("route", route.route_id))
            route_font = QFont()
            route_font.setBold(True)
            route_item.setFont(route_font)
            route_item.setForeground(QBrush(QColor("#24455F")))
            self.project_tree.addItem(route_item)
            for line in route.lines:
                color = SERVICE_COLORS.get(line.line_input.service, "#94A3B8")
                status = self.status_label(line.validation_state.status)
                service = self.service_label(line.line_input.service)
                material = line.line_input.material
                item = QListWidgetItem(f"  # {line.tag}\n     {service} | {material} | {status}")
                item.setData(256, ("line", line.line_id))
                item.setForeground(QBrush(QColor("#172033")))
                item.setBackground(QBrush(QColor(color + "22")))
                item.setToolTip(f"{service} | {material} | {status}")
                self.project_tree.addItem(item)

    def _on_tree_selection(self) -> None:
        items = self.project_tree.selectedItems()
        if not items:
            return
        kind, ident = items[0].data(256)
        if kind != "line":
            return
        line = next((line for line in self.project.all_lines() if line.line_id == ident), None)
        if line is None:
            return
        self.current_line_id = ident
        self._input_to_form(line.line_input)
        if line.last_report_context:
            self._render_context(line.last_report_context)

    def _current_line(self):
        if not self.current_line_id:
            return None
        return next((line for line in self.project.all_lines() if line.line_id == self.current_line_id), None)

    def _sync_current_line(self) -> None:
        line = self._current_line()
        if line:
            line.line_input = self._form_to_input()
            line.tag = line.line_input.line_tag
            self.project.name = line.line_input.project_name

    def _field_has_value(self, field_id: str) -> bool:
        widget = self.field_widgets.get(field_id)
        if widget is None:
            return True
        if hasattr(widget, "text"):
            return bool(widget.text().strip())
        if hasattr(widget, "toPlainText"):
            return True
        if hasattr(widget, "currentText"):
            return bool(widget.currentText().strip())
        if hasattr(widget, "value"):
            value = widget.value()
            if field_id in {"flow_rate", "line_length_m", "slope_mm_m", "vacuum_target_mbara", "DN_received_mm"}:
                return value > 0
            return value is not None
        return True

    def _validate_form_before_calculation(self) -> bool:
        behavior = self._active_form_behavior()
        missing = [
            get_field_meta(field_id).label(self.language)
            for field_id in behavior.required_fields
            if field_id in self.form_rows and not self._field_has_value(field_id)
        ]
        issues = []
        if self.P_design.value() < self.P_oper.value() and "P_design_bar >= P_oper_bar" in behavior.validation_rules:
            issues.append(
                "A pressao de projeto deve ser maior ou igual a pressao de operacao."
                if self.language == "pt-BR"
                else "Design pressure must be greater than or equal to operating pressure."
            )
        if missing or issues:
            lines = []
            if missing:
                lines.append(self.tr("validation_missing_intro"))
                lines.extend([f"- {name}" for name in missing])
            if issues:
                if lines:
                    lines.append("")
                lines.extend([f"- {issue}" for issue in issues])
            QMessageBox = self.qt["QMessageBox"]
            QMessageBox.warning(self.window, self.tr("validation_missing_title"), "\n".join(lines))
            self._set_status(self.tr("validation_missing_title"))
            return False
        return True

    def calculate_current(self) -> None:
        line = self._current_line()
        if line is None:
            return
        if not self._validate_form_before_calculation():
            return
        try:
            self._sync_current_line()
            ctx = line.calculate()
            self._render_context(ctx)
            self.refresh_project_tree()
            self._set_status(f"Calculated {line.tag}")
        except Exception as exc:
            self._error("Calculation failed", str(exc))

    def _render_context(self, ctx) -> None:
        hyd = ctx.hydraulic_result
        thick = ctx.thickness_result
        status = ctx.checker_result.overall_status if ctx.checker_result else "N/A"
        criterion = "N/A"
        if hyd and hyd.governing_criterion:
            criterion = hyd.governing_criterion
        elif ctx.checker_result and ctx.checker_result.governing_issue:
            criterion = ctx.checker_result.governing_issue
        if self.result_cards:
            self.result_cards["status"].setText(self.status_label(status))
            self.result_cards["dn"].setText(str(hyd.DN_governing_mm) if hyd else "N/A")
            self.result_cards["material"].setText(ctx.line_input.material if ctx.line_input else "N/A")
            self.result_cards["schedule"].setText(thick.selected_schedule if thick else "N/A")
            self.result_cards["criterion"].setText(str(criterion))
        self._fill_table(self.summary_table, [
            ("Projeto" if self.language == "pt-BR" else "Project", ctx.project_name),
            ("Linha" if self.language == "pt-BR" else "Line", ctx.line_tag),
            ("Status", self.status_label(status)),
            ("Criterio governante" if self.language == "pt-BR" else "Governing issue", ctx.checker_result.governing_issue if ctx.checker_result else "N/A"),
            ("Catalogo" if self.language == "pt-BR" else "Catalog", ctx.line_input.dimensional_catalog if ctx.line_input else "N/A"),
        ])
        rows = []
        if hyd:
            hyd_labels = {
                "regime": "Regime",
                "dn": "DN governante [mm]" if self.language == "pt-BR" else "DN governing [mm]",
                "velocity": "Velocidade [m/s]" if self.language == "pt-BR" else "Velocity [m/s]",
                "dp": "dP total [bar]",
                "criterion": "Criterio" if self.language == "pt-BR" else "Criterion",
            }
            rows.extend([
                (hyd_labels["regime"], hyd.regime),
                (hyd_labels["dn"], hyd.DN_governing_mm),
                (hyd_labels["velocity"], hyd.velocity_ms),
                (hyd_labels["dp"], hyd.dp_total_bar),
                (hyd_labels["criterion"], hyd.governing_criterion),
            ])
        if thick:
            thick_labels = {
                "schedule": "Schedule",
                "selected": "Espessura selecionada [mm]" if self.language == "pt-BR" else "Selected wall [mm]",
                "required": "Espessura requerida [mm]" if self.language == "pt-BR" else "Required wall [mm]",
                "status": "Estado da espessura" if self.language == "pt-BR" else "Thickness status",
            }
            rows.extend([
                (thick_labels["schedule"], thick.selected_schedule),
                (thick_labels["selected"], thick.selected_wall_mm),
                (thick_labels["required"], thick.t_after_mill_tolerance_mm),
                (thick_labels["status"], thick.status),
            ])
        self._fill_table(self.results_table, rows)

        warnings = []
        assumptions = []
        for src in [
            ctx.fluid_properties,
            ctx.hydraulic_result,
            ctx.thickness_result,
            ctx.external_pressure_result,
            ctx.support_result,
            ctx.checker_result,
        ]:
            if src and hasattr(src, "warnings"):
                warnings.extend(src.warnings or [])
            if src and hasattr(src, "assumptions_used"):
                assumptions.extend(src.assumptions_used or [])
        warnings.extend([w.message for w in ctx.warnings])
        self.warnings_box.setPlainText("\n".join(warnings) or self.tr("no_warnings"))
        self.assumptions_box.setPlainText("\n".join(sorted(set(assumptions))) or self.tr("no_assumptions"))

    def _fill_table(self, table, rows) -> None:
        qt = self.qt
        QTableWidgetItem = qt["QTableWidgetItem"]
        table.setRowCount(len(rows))
        for row, (field, value) in enumerate(rows):
            table.setItem(row, 0, QTableWidgetItem(str(field)))
            if isinstance(value, float):
                value = f"{value:.5g}"
            table.setItem(row, 1, QTableWidgetItem("" if value is None else str(value)))
        table.resizeColumnsToContents()

    def new_project(self) -> None:
        self.project = create_default_project("SIDCT Project")
        self.current_path = None
        self.current_line_id = None
        self._seed_default_line()
        self.refresh_project_tree()
        self._set_status("New project")

    def open_project(self) -> None:
        QFileDialog = self.qt["QFileDialog"]
        path, _ = QFileDialog.getOpenFileName(self.window, "Open project", "", "SIDCT Project (*.sidct.json *.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.current_path = Path(path)
            self.current_line_id = self.project.all_lines()[0].line_id if self.project.all_lines() else None
            self.refresh_project_tree()
            if self.current_line_id:
                line = self._current_line()
                if line:
                    self._input_to_form(line.line_input)
            self._set_status(f"Opened {path}")
        except Exception as exc:
            self._error("Open failed", str(exc))

    def save_project(self) -> None:
        if self.current_path is None:
            self.save_project_as()
            return
        self._sync_current_line()
        save_project(self.project, self.current_path)
        self._set_status(f"Saved {self.current_path}")

    def save_project_as(self) -> None:
        QFileDialog = self.qt["QFileDialog"]
        path, _ = QFileDialog.getSaveFileName(self.window, "Save project", "", "SIDCT Project (*.sidct.json)")
        if not path:
            return
        self.current_path = Path(path)
        self.save_project()

    def add_line(self) -> None:
        self._sync_current_line()
        route = self.project.routes[0] if self.project.routes else self.project.add_route("Route A")
        count = len(self.project.all_lines()) + 1
        inp = self._form_to_input().model_copy(update={"line_tag": f"L-{count:03d}"})
        line = route.add_line(inp)
        self.current_line_id = line.line_id
        self._input_to_form(inp)
        self.refresh_project_tree()

    def duplicate_line(self) -> None:
        line = self._current_line()
        if not line:
            return
        new_tag = f"{line.tag}-COPY"
        duplicated = self.project.duplicate_line(line.line_id, new_tag)
        self.current_line_id = duplicated.line_id
        self._input_to_form(duplicated.line_input)
        self.refresh_project_tree()

    def export_pdf(self) -> None:
        line = self._current_line()
        if not line:
            return
        if line.last_report_context is None:
            self.calculate_current()
        if line.last_report_context is None:
            return
        QFileDialog = self.qt["QFileDialog"]
        path, _ = QFileDialog.getSaveFileName(self.window, "Export PDF", f"{line.tag}.pdf", "PDF (*.pdf)")
        if path:
            generate_pdf(line.last_report_context, path)
            self._set_status(f"Exported {path}")

    def export_csv(self) -> None:
        QFileDialog = self.qt["QFileDialog"]
        path, _ = QFileDialog.getSaveFileName(self.window, "Export CSV", "sidct_results.csv", "CSV (*.csv)")
        if path:
            export_project_csv(self.project, path)
            self._set_status(f"Exported {path}")

    def export_xlsx(self) -> None:
        QFileDialog = self.qt["QFileDialog"]
        path, _ = QFileDialog.getSaveFileName(self.window, "Export XLSX", "sidct_results.xlsx", "Excel (*.xlsx)")
        if path:
            export_project_xlsx(self.project, path)
            self._set_status(f"Exported {path}")

    def _error(self, title: str, message: str) -> None:
        QMessageBox = self.qt["QMessageBox"]
        QMessageBox.critical(self.window, title, message)
        self._set_status(message)

    def _set_status(self, message: str) -> None:
        self.window.statusBar().showMessage(message)


def main() -> int:
    qt = _require_qt()
    QApplication = qt["QApplication"]
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("SIDCT")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
