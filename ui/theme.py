DARK_QSS = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-size: 10pt;
}
QMainWindow, QDialog {
    background-color: #2b2b2b;
}
QLineEdit, QComboBox, QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 4px 8px;
}
QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    padding: 2px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #7c5cff;
}
QHeaderView::section {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 0px;
    padding: 6px;
}
QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #484848;
}
QPushButton:pressed {
    background-color: #555;
}
QPushButton:checked {
    background-color: #7c5cff;
    color: #ffffff;
    border: 1px solid #7c5cff;
}
QGroupBox {
    background-color: #323232;
    border: 1px solid #444;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QTabWidget::pane {
    border: 1px solid #444;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border-radius: 6px;
    padding: 6px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #7c5cff;
    color: #ffffff;
}
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #555;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #7c5cff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #555;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #7c5cff;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f2f2f2;
    color: #202020;
    font-size: 10pt;
}
QMainWindow, QDialog {
    background-color: #f2f2f2;
}
QLineEdit, QComboBox, QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #bbb;
    border-radius: 6px;
    padding: 4px 8px;
}
QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    padding: 2px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #6d4fe0;
}
QHeaderView::section {
    background-color: #e6e6e6;
    color: #202020;
    border: 1px solid #bbb;
    border-radius: 0px;
    padding: 6px;
}
QPushButton {
    background-color: #e6e6e6;
    color: #202020;
    border: 1px solid #aaa;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #dcdcdc;
}
QPushButton:pressed {
    background-color: #cfcfcf;
}
QPushButton:checked {
    background-color: #6d4fe0;
    color: #ffffff;
    border: 1px solid #6d4fe0;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QTabWidget::pane {
    border: 1px solid #bbb;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #e6e6e6;
    color: #202020;
    border-radius: 6px;
    padding: 6px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #6d4fe0;
    color: #ffffff;
}
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #ccc;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #6d4fe0;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #ccc;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #6d4fe0;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""


def apply_theme(app, name: str) -> None:
    app.setStyleSheet(LIGHT_QSS if name == "light" else DARK_QSS)
