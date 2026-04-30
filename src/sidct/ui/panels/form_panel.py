"""Form panel base class for the desktop UI."""
from __future__ import annotations

try:
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    Signal = None  # type: ignore[assignment]
    QWidget = object  # type: ignore[assignment]


if Signal is not None:

    class FormPanel(QWidget):
        calculateRequested = Signal()
        changed = Signal()

        def __init__(self, form_widget: QWidget | None = None, parent=None):
            super().__init__(parent)
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            layout = QVBoxLayout(self)
            layout.addWidget(self.scroll_area)
            if form_widget is not None:
                self.set_form_widget(form_widget)

        def set_form_widget(self, form_widget: QWidget) -> None:
            self.scroll_area.setWidget(form_widget)

else:

    class FormPanel:  # type: ignore[no-redef]
        pass
