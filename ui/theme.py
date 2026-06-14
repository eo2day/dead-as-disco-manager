DARK_QSS = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QMainWindow, QDialog {
    background-color: #2b2b2b;
}
QLineEdit, QComboBox, QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #444;
}
QHeaderView::section {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #444;
    padding: 4px;
}
QPushButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 4px 10px;
}
QPushButton:hover {
    background-color: #484848;
}
QPushButton:pressed {
    background-color: #555;
}
QPushButton:checked {
    background-color: #5a5a5a;
    border: 1px solid #888;
}
QTabWidget::pane {
    border: 1px solid #444;
}
QTabBar::tab {
    background-color: #3a3a3a;
    color: #e0e0e0;
    padding: 6px 12px;
}
QTabBar::tab:selected {
    background-color: #4a4a4a;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f2f2f2;
    color: #202020;
}
QMainWindow, QDialog {
    background-color: #f2f2f2;
}
QLineEdit, QComboBox, QListWidget, QTableWidget, QTextBrowser, QTreeWidget {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #bbb;
}
QHeaderView::section {
    background-color: #e6e6e6;
    color: #202020;
    border: 1px solid #bbb;
    padding: 4px;
}
QPushButton {
    background-color: #e6e6e6;
    color: #202020;
    border: 1px solid #aaa;
    padding: 4px 10px;
}
QPushButton:hover {
    background-color: #dcdcdc;
}
QPushButton:pressed {
    background-color: #cfcfcf;
}
QPushButton:checked {
    background-color: #cfcfcf;
    border: 1px solid #888;
}
QTabWidget::pane {
    border: 1px solid #bbb;
}
QTabBar::tab {
    background-color: #e6e6e6;
    color: #202020;
    padding: 6px 12px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
}
"""


def apply_theme(app, name: str) -> None:
    app.setStyleSheet(LIGHT_QSS if name == "light" else DARK_QSS)
