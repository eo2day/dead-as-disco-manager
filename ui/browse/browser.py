import tempfile
from pathlib import Path

from PySide6.QtCore import QUrl, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineDownloadRequest,
)

from disco import config, importer

DISCOMAPS_URL = "https://discomaps.com"


class BrowseTab(QWidget):
    """Embedded DiscoMaps browser that auto-imports downloaded map zips."""

    imported = Signal(str)

    def __init__(self, storage_dir: Path, parent=None):
        super().__init__(parent)
        self._download_dir = Path(tempfile.mkdtemp(prefix="discomaps_dl_"))
        self._loaded_once = False
        self._popout = None

        layout = QVBoxLayout(self)

        nav = QHBoxLayout()
        back = QPushButton("◀"); fwd = QPushButton("▶")
        reload_btn = QPushButton("⟳"); home = QPushButton("Home")
        popout = QPushButton("Open in separate window")
        self.status = QLabel("")
        for b in (back, fwd, reload_btn, home):
            b.setMaximumWidth(60); nav.addWidget(b)
        nav.addWidget(popout)
        nav.addWidget(self.status, 1)
        layout.addLayout(nav)

        self.profile = QWebEngineProfile("disco-manager", self)
        self.profile.setPersistentStoragePath(str(storage_dir / "web"))
        self.profile.setCachePath(str(storage_dir / "web-cache"))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(self._on_download)

        self.view = QWebEngineView(self)
        self.page = QWebEnginePage(self.profile, self)
        self.view.setPage(self.page)
        self.view.setMinimumSize(800, 500)
        layout.addWidget(self.view, 1)

        back.clicked.connect(self.view.back)
        fwd.clicked.connect(self.view.forward)
        reload_btn.clicked.connect(self.view.reload)
        home.clicked.connect(lambda: self.view.setUrl(QUrl(DISCOMAPS_URL)))
        popout.clicked.connect(self._open_popout)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded_once:
            self._loaded_once = True

            def load():
                self.updateGeometry()
                self.layout().activate()
                self.view.setUrl(QUrl(DISCOMAPS_URL))
                QTimer.singleShot(300, self._reflow)

            QTimer.singleShot(0, load)
        else:
            QTimer.singleShot(0, self._reflow)

    def _reflow(self):
        s = self.view.size()
        self.view.resize(s.width(), s.height() - 1)
        self.view.resize(s)
        self.view.update()

    def _open_popout(self):
        w = QWebEngineView()
        w.setWindowTitle("DiscoMaps")
        w.setPage(QWebEnginePage(self.profile, w))
        w.resize(1100, 800)
        w.setUrl(QUrl(DISCOMAPS_URL))
        w.show()
        self._popout = w

    def _on_download(self, download: QWebEngineDownloadRequest):
        download.setDownloadDirectory(str(self._download_dir))
        download.accept()
        name = download.downloadFileName()
        if name.lower().endswith(".zip"):
            self.status.setText(f"Downloading {name}…")
            download.isFinishedChanged.connect(lambda: self._finish(download))

    def _finish(self, download: QWebEngineDownloadRequest):
        if download.state() != QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            return
        zip_path = Path(download.downloadDirectory()) / download.downloadFileName()
        target = config.get_imported_songs_path()
        if not target:
            msg = "Set your ImportedSongs folder first (Home page)."
            self.status.setText(msg); self.imported.emit(msg); return
        try:
            installed = importer.import_zip(zip_path, target)
        except importer.ImportError_ as e:
            msg = f"Import failed: {e}"
            self.status.setText(msg); self.imported.emit(msg); return
        msg = "Installed " + ", ".join(installed) + " — restart the game to see them."
        self.status.setText(msg)
        self.imported.emit(msg)
