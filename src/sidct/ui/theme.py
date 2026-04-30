"""Styles used by the SIDCT desktop application."""
from __future__ import annotations

STATUS_CARD_COLORS = {
    "APPROVED": "#E6F7EC",
    "CONSERVATIVE": "#FFF8E1",
    "INSUFFICIENT": "#FDE7E7",
    "CRITICAL": "#FFCDD2",
    "DRAFT": "#F5F5F5",
    "CALCULATED": "#E3F2FD",
    "DATASET_MISSING": "#FFF3E0",
    "OUT_OF_SCOPE": "#F3E5F5",
    "CODE_MISMATCH": "#F3E5F5",
    "WARNING": "#FFF8E1",
    "ERROR": "#FDE7E7",
}


def get_status_color(status: str) -> str:
    return STATUS_CARD_COLORS.get(str(status).upper(), "#FFFFFF")


def get_light_theme_stylesheet() -> str:
    return """
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
    """
