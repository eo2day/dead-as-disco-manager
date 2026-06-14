from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup

SECTIONS = ["Home", "Browse", "Library"]


class Sidebar(QWidget):
    """Vertical navigation sidebar. Emits pageChanged(index) when selection changes."""

    pageChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(140)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for i, label in enumerate(SECTIONS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            self._group.addButton(btn, i)
            layout.addWidget(btn)

        layout.addStretch()
        self._group.idClicked.connect(self.pageChanged)
        self._group.button(0).setChecked(True)
