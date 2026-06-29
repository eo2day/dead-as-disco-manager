import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget

from disco import config
from ui import theme
from ui.browse.browser import BrowseTab
from ui.guide import show_guide_dialog
from ui.home import HomePage
from ui.library.library_page import LibraryPage
from ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dead as Disco — Music Manager")
        icon_path = Path(__file__).parent.parent / "icon.png"
        if hasattr(sys, "_MEIPASS"):                 # running from PyInstaller bundle
            icon_path = Path(sys._MEIPASS) / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1000, 700)

        self._resolve_path_on_start()

        sidebar = Sidebar()
        self.stack = QStackedWidget()

        self.home_page = HomePage()
        self.home_page.pathsChanged.connect(self._on_paths_changed)
        self.home_page.themeChanged.connect(self._on_theme_changed)
        self.home_page.guideRequested.connect(lambda: show_guide_dialog(self))

        self.browse = BrowseTab(config.CONFIG_DIR, self)
        self.library = LibraryPage()
        self.browse.imported.connect(lambda _m: self.library.installed_tab.refresh())
        self.browse.imported.connect(lambda _m: self.browse.refresh_installed_markers())

        self.stack.addWidget(self.home_page)  # index 0 — Home
        self.stack.addWidget(self.browse)     # index 1 — Browse
        self.stack.addWidget(self.library)    # index 2 — Library
        sidebar.pageChanged.connect(self.stack.setCurrentIndex)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addWidget(self.stack)
        self.setCentralWidget(central)

    def _resolve_path_on_start(self):
        saved = config.get_imported_songs_path()
        if saved and saved.parent.exists():
            return
        detected = config.autodetect_imported_songs()
        if detected:
            config.set_imported_songs_path(detected)

    def _on_paths_changed(self):
        self.library.installed_tab.refresh()
        self.library.playlists_tab.refresh_playlists()
        self.browse.refresh_installed_markers()

    def _on_theme_changed(self, name):
        app = QApplication.instance()
        if app:
            theme.apply_theme(app, name)
