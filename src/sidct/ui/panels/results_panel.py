"""Results panel for the desktop UI."""
from __future__ import annotations

from collections.abc import Callable

from sidct.ui.theme import get_status_color
from sidct.ui.translations import RESULT_CARD_KEYS

try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Signal = None  # type: ignore[assignment]
    QWidget = object  # type: ignore[assignment]


if Signal is not None:

    class ResultsPanel(QWidget):
        resultsRendered = Signal()

        def __init__(self, language: str, translate: Callable[[str], str], status_label: Callable[[str], str], parent=None):
            super().__init__(parent)
            self.language = language
            self.translate = translate
            self.status_label = status_label
            self.result_cards: dict[str, object] = {}

            layout = QVBoxLayout(self)
            cards = QGridLayout()
            for index, (key, titles) in enumerate(RESULT_CARD_KEYS):
                frame = QFrame()
                frame.setObjectName("resultCard")
                card_layout = QVBoxLayout(frame)
                title = QLabel(titles.get(language, titles["en"]))
                title.setObjectName("resultCardTitle")
                value = QLabel("N/A")
                value.setObjectName("resultCardValue")
                value.setWordWrap(True)
                card_layout.addWidget(title)
                card_layout.addWidget(value)
                self.result_cards[f"{key}_frame"] = frame
                self.result_cards[f"{key}_title"] = title
                self.result_cards[key] = value
                cards.addWidget(frame, index // 3, index % 3)
            layout.addLayout(cards)

            self.tabs = QTabWidget()
            self.summary_table = QTableWidget(0, 2)
            self.results_table = QTableWidget(0, 2)
            self.warnings_box = QTextEdit()
            self.warnings_box.setReadOnly(True)
            self.assumptions_box = QTextEdit()
            self.assumptions_box.setReadOnly(True)
            self.audit_box = QTextEdit()
            self.audit_box.setReadOnly(True)
            self.tabs.addTab(self.summary_table, self.translate("summary"))
            self.tabs.addTab(self.results_table, self.translate("results"))
            self.tabs.addTab(self.warnings_box, self.translate("warnings"))
            self.tabs.addTab(self.assumptions_box, self.translate("assumptions"))
            self.tabs.addTab(self.audit_box, self.translate("audit"))
            layout.addWidget(self.tabs)
            self.set_language(language)

        def set_language(self, language: str) -> None:
            self.language = language
            for key, titles in RESULT_CARD_KEYS:
                title = self.result_cards.get(f"{key}_title")
                if title:
                    title.setText(titles.get(language, titles["en"]))
            self.tabs.setTabText(0, self.translate("summary"))
            self.tabs.setTabText(1, self.translate("results"))
            self.tabs.setTabText(2, self.translate("warnings"))
            self.tabs.setTabText(3, self.translate("assumptions"))
            self.tabs.setTabText(4, self.translate("audit"))
            self.summary_table.setHorizontalHeaderLabels([self.translate("field"), self.translate("value")])
            self.results_table.setHorizontalHeaderLabels([self.translate("metric"), self.translate("value")])

        def set_results(self, ctx) -> None:
            hyd = ctx.hydraulic_result
            thick = ctx.thickness_result
            status = ctx.checker_result.overall_status if ctx.checker_result else "N/A"
            criterion = "N/A"
            if hyd and hyd.governing_criterion:
                criterion = hyd.governing_criterion
            elif ctx.checker_result and ctx.checker_result.governing_issue:
                criterion = ctx.checker_result.governing_issue
            self.result_cards["status"].setText(self.status_label(status))
            self.result_cards["dn"].setText(str(hyd.DN_governing_mm) if hyd else "N/A")
            self.result_cards["material"].setText(ctx.line_input.material if ctx.line_input else "N/A")
            self.result_cards["schedule"].setText(thick.selected_schedule if thick else "N/A")
            self.result_cards["criterion"].setText(str(criterion))
            bg = get_status_color(status)
            for key, _titles in RESULT_CARD_KEYS:
                frame = self.result_cards.get(f"{key}_frame")
                if frame:
                    frame.setStyleSheet(
                        "QFrame#resultCard { "
                        f"background: {bg}; border: 1px solid #D7E2EA; "
                        "border-radius: 8px; padding: 8px; }"
                    )
            self.resultsRendered.emit()

        def fill_table(self, table, rows) -> None:
            table.setRowCount(len(rows))
            for row, (field, value) in enumerate(rows):
                table.setItem(row, 0, QTableWidgetItem(str(field)))
                if isinstance(value, float):
                    value = f"{value:.5g}"
                table.setItem(row, 1, QTableWidgetItem("" if value is None else str(value)))
            table.resizeColumnsToContents()

else:

    class ResultsPanel:  # type: ignore[no-redef]
        pass
