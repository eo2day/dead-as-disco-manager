
# Dead as Disco Music Manager — developed with AI assistance (Anthropic Claude).

import os
if os.name == "nt":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--use-gl=angle --use-angle=d3d11"

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from disco import config
from ui import theme
from ui.main_window import MainWindow


if __name__ == "__main__":
    if os.name == "nt":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DiscoManager")
        except Exception:
            pass
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    theme.apply_theme(app, config.get_theme())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
