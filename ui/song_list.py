from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QStyle, QStyledItemDelegate,
)

COLUMNS = ["Song Name", "Artist", "Length", "BPM", "Offset"]

ROW_HOVER_COLOR = QColor(124, 92, 255, 40)
ROW_CHECKED_COLOR = QColor(124, 92, 255, 70)


class _RowHoverDelegate(QStyledItemDelegate):
    """Paints a highlight across checked rows, and rows the mouse hovers over."""

    def __init__(self, table):
        super().__init__(table)
        self.hover_row = -1

    def paint(self, painter, option, index):
        option.state &= ~QStyle.StateFlag.State_HasFocus

        checked = index.sibling(index.row(), 0).data(Qt.ItemDataRole.CheckStateRole) \
            == Qt.CheckState.Checked.value
        if checked:
            painter.save()
            painter.fillRect(option.rect, ROW_CHECKED_COLOR)
            painter.restore()
        elif index.row() == self.hover_row:
            painter.save()
            painter.fillRect(option.rect, ROW_HOVER_COLOR)
            painter.restore()
        super().paint(painter, option, index)


class NumericTableWidgetItem(QTableWidgetItem):
    """Sorts by an underlying numeric value (None sorts last) instead of text."""

    def __init__(self, text, value):
        super().__init__(text)
        self.value = value

    def __lt__(self, other):
        a, b = self.value, getattr(other, "value", None)
        if a is None:
            return False
        if b is None:
            return True
        return a < b


def _format_length(seconds):
    if seconds is None:
        return ""
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def _format_num(value):
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


class SongListWidget(QWidget):
    """Shared song table: search bar + Song Name/Artist/Length/BPM/Offset columns,
    click-to-sort (numeric columns sort numerically), checkbox per row."""

    checkedChanged = Signal()

    def __init__(self, parent=None, disable_no_id=False):
        super().__init__(parent)
        self._disable_no_id = disable_no_id
        self._maps: list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title or artist…")
        self.search.textChanged.connect(self._apply_filter)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemChanged.connect(self._on_item_changed)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMouseTracking(True)
        self._hover_delegate = _RowHoverDelegate(self.table)
        self.table.setItemDelegate(self._hover_delegate)
        self.table.viewport().installEventFilter(self)

        layout.addWidget(self.table)

    def set_songs(self, maps) -> None:
        checked = self.checked_sources()
        self._maps = list(maps)

        self.table.setSortingEnabled(False)
        self.table.itemChanged.disconnect(self._on_item_changed)
        self.table.setRowCount(0)
        for m in self._maps:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name = m.title
            addable = m.unique_id is not None
            if self._disable_no_id and not addable:
                name += "   (no ID — can't add)"

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, m)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            name_item.setCheckState(Qt.CheckState.Checked if str(m.source) in checked
                                     else Qt.CheckState.Unchecked)
            if self._disable_no_id and not addable:
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 0, name_item)

            self.table.setItem(row, 1, QTableWidgetItem(m.artist))
            self.table.setItem(row, 2, NumericTableWidgetItem(_format_length(m.duration), m.duration))
            self.table.setItem(row, 3, NumericTableWidgetItem(_format_num(m.tempo), m.tempo))
            self.table.setItem(row, 4, NumericTableWidgetItem(_format_num(m.offset), m.offset))
            for col in (1, 2, 3, 4):
                self.table.item(row, col).setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setSortingEnabled(True)
        self._apply_filter()

    def eventFilter(self, obj, event) -> bool:
        if obj is self.table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                row = self.table.indexAt(event.pos()).row()
                if row != self._hover_delegate.hover_row:
                    self._hover_delegate.hover_row = row
                    self.table.viewport().update()
            elif event.type() == QEvent.Type.Leave:
                if self._hover_delegate.hover_row != -1:
                    self._hover_delegate.hover_row = -1
                    self.table.viewport().update()
        return super().eventFilter(obj, event)

    def _apply_filter(self) -> None:
        q = self.search.text().strip().lower()
        for row in range(self.table.rowCount()):
            m = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            visible = not q or q in m.title.lower() or q in m.artist.lower()
            self.table.setRowHidden(row, not visible)

    def _on_item_changed(self, item) -> None:
        if item.column() == 0:
            self.table.viewport().update()
            self.checkedChanged.emit()

    def checked_sources(self) -> set[str]:
        out = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            m = item.data(Qt.ItemDataRole.UserRole)
            if m and item.checkState() == Qt.CheckState.Checked:
                out.add(str(m.source))
        return out

    def checked_maps(self) -> list:
        sources = self.checked_sources()
        return [m for m in self._maps if str(m.source) in sources]

    def toggle_all(self) -> None:
        items = [self.table.item(r, 0) for r in range(self.table.rowCount())
                 if not self.table.isRowHidden(r)]
        any_unchecked = any(it.checkState() != Qt.CheckState.Checked for it in items)
        state = Qt.CheckState.Checked if any_unchecked else Qt.CheckState.Unchecked
        for it in items:
            it.setCheckState(state)
