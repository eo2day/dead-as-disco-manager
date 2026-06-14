from PySide6.QtWidgets import QTabWidget

from ui.library.installed_tab import InstalledTab
from ui.library.playlists_tab import PlaylistsTab


class LibraryPage(QTabWidget):
    """Library section: Installed and Playlists sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installed_tab = InstalledTab()
        self.playlists_tab = PlaylistsTab()
        self.addTab(self.installed_tab, "Installed")
        self.addTab(self.playlists_tab, "Playlists")
