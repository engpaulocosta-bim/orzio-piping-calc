"""Project tree panel for the desktop UI."""
from __future__ import annotations

from collections.abc import Callable

from sidct.ui.translations import SERVICE_COLORS

try:
    from PySide6.QtCore import Signal
    from PySide6.QtGui import QBrush, QColor, QFont
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - imported only when desktop dependencies are present.
    Signal = None  # type: ignore[assignment]
    QWidget = object  # type: ignore[assignment]


if Signal is not None:

    class ProjectTreePanel(QWidget):
        lineSelected = Signal(str)
        routeSelected = Signal(str)
        removeRequested = Signal()
        recalculateRequested = Signal()

        def __init__(
            self,
            language: str,
            translate: Callable[[str], str],
            service_label: Callable[[str], str],
            status_label: Callable[[str], str],
            parent=None,
        ):
            super().__init__(parent)
            self.language = language
            self.translate = translate
            self.service_label = service_label
            self.status_label = status_label
            self._project = None
            self.label = QLabel(self.translate("project"))
            self.filter_box = QLineEdit()
            self.filter_box.setPlaceholderText(self.translate("filter_lines"))
            self.filter_box.textChanged.connect(self._apply_filter)
            self.summary_label = QLabel("")
            self.summary_label.setWordWrap(True)
            self.tree = QListWidget()
            self.tree.itemSelectionChanged.connect(self._selection_changed)
            self.recalculate_button = QPushButton(self.translate("recalculate"))
            self.remove_button = QPushButton(self.translate("remove_line"))
            self.recalculate_button.clicked.connect(self.recalculateRequested)
            self.remove_button.clicked.connect(self.removeRequested)

            layout = QVBoxLayout(self)
            layout.addWidget(self.label)
            layout.addWidget(self.filter_box)
            layout.addWidget(self.summary_label)
            layout.addWidget(self.tree)
            actions = QHBoxLayout()
            actions.addWidget(self.recalculate_button)
            actions.addWidget(self.remove_button)
            layout.addLayout(actions)

        def set_language(self, language: str) -> None:
            self.language = language
            self.filter_box.setPlaceholderText(self.translate("filter_lines"))
            self.recalculate_button.setText(self.translate("recalculate"))
            self.remove_button.setText(self.translate("remove_line"))
            if self._project is not None:
                self._update_summary(self._project)

        def refresh_tree(self, project) -> None:
            self._project = project
            self.tree.clear()
            self.label.setText(f"{self.translate('project')}: {project.name}")
            filter_text = self.filter_box.text().strip().lower()
            for route in project.routes:
                route_item = QListWidgetItem(f"[{self.translate('route_prefix')}] {route.name}")
                route_item.setData(256, ("route", route.route_id))
                route_font = QFont()
                route_font.setBold(True)
                route_item.setFont(route_font)
                route_item.setForeground(QBrush(QColor("#24455F")))
                self.tree.addItem(route_item)
                for line in route.lines:
                    color = SERVICE_COLORS.get(line.line_input.service, "#94A3B8")
                    status = self.status_label(line.validation_state.status)
                    service = self.service_label(line.line_input.service)
                    material = line.line_input.material
                    haystack = f"{line.tag} {service} {line.line_input.service} {material} {status}".lower()
                    if filter_text and filter_text not in haystack:
                        continue
                    item = QListWidgetItem(f"  # {line.tag}\n     {service} | {material} | {status}")
                    item.setData(256, ("line", line.line_id))
                    item.setForeground(QBrush(QColor("#172033")))
                    item.setBackground(QBrush(QColor(color + "22")))
                    item.setToolTip(f"{service} | {material} | {status}")
                    self.tree.addItem(item)
            self._update_summary(project)

        def _apply_filter(self) -> None:
            if self._project is not None:
                self.refresh_tree(self._project)

        def _update_summary(self, project) -> None:
            counts: dict[str, int] = {}
            for line in project.all_lines():
                label = self.status_label(line.validation_state.status)
                counts[label] = counts.get(label, 0) + 1
            if not counts:
                self.summary_label.setText("")
                return
            parts = [
                self.translate("status_summary").format(status=status, count=count)
                for status, count in sorted(counts.items())
            ]
            self.summary_label.setText(f"{self.translate('project_summary')}: " + " | ".join(parts))

        def _selection_changed(self) -> None:
            items = self.tree.selectedItems()
            if not items:
                return
            kind, ident = items[0].data(256)
            if kind == "line":
                self.lineSelected.emit(ident)
            elif kind == "route":
                self.routeSelected.emit(ident)

else:

    class ProjectTreePanel:  # type: ignore[no-redef]
        pass
