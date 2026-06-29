import json
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
        reload_btn = QPushButton("⟳"); home = QPushButton("⌂")
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
        self.view.loadFinished.connect(self._sync_installed_markers)
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
        self._sync_installed_markers()
        self.imported.emit(msg)

    def refresh_installed_markers(self):
        self._sync_installed_markers()

    def _installed_song_payload(self) -> list[dict]:
        path = config.get_imported_songs_path()
        if not path:
            return []
        payload = []
        for song in importer.list_installed(path):
            payload.append({
                "title": song.title,
                "artist": song.artist,
                "tempo": song.tempo,
            })
        return payload

    def _sync_installed_markers(self, *_args):
        payload = json.dumps(self._installed_song_payload())
        script = f"""
(() => {{
  const installedSongs = {payload};

  const normalize = (value) => (value || "")
    .toString()
    .normalize("NFKD")
    .replace(/[\\u0300-\\u036f]/g, "")
    .replace(/[^a-z0-9]+/gi, " ")
    .trim()
    .toLowerCase();

  const titleArtistKeys = new Set();
  const titleArtistTempoKeys = new Set();

  for (const song of installedSongs) {{
    const title = normalize(song.title);
    const artist = normalize(song.artist);
    if (!title || !artist) continue;
    titleArtistKeys.add(`${{title}}|${{artist}}`);
    if (Number.isFinite(song.tempo)) {{
      titleArtistTempoKeys.add(`${{title}}|${{artist}}|${{Math.round(song.tempo)}}`);
    }}
  }}

  const extractSongMeta = (button) => {{
    const card = button.closest(".p-6.relative")
      || button.closest("div[class*='p-6']")
      || button.parentElement;
    if (!card) return null;

    const title = normalize(card.querySelector("h3")?.textContent);
    const artist = normalize(card.querySelector("p")?.textContent);
    const bpmText = card.querySelector(".bpm-text")?.textContent || "";
    const bpmMatch = bpmText.match(/(\\d+)/);
    const tempo = bpmMatch ? Number.parseInt(bpmMatch[1], 10) : null;

    if (!title || !artist) return null;
    return {{ title, artist, tempo }};
  }};

  const isInstalled = (meta) => {{
    if (!meta) return false;
    const baseKey = `${{meta.title}}|${{meta.artist}}`;
    if (meta.tempo !== null && titleArtistTempoKeys.has(`${{baseKey}}|${{meta.tempo}}`)) {{
      return true;
    }}
    return titleArtistKeys.has(baseKey);
  }};

  const markInstalled = (button) => {{
    if (button.dataset.dadInstalled === "1") return;
    button.dataset.dadInstalled = "1";
    button.dataset.dadOriginalHtml = button.innerHTML;
    button.dataset.dadOriginalTitle = button.getAttribute("title") || "";
    button.style.setProperty("background", "#16a34a", "important");
    button.style.setProperty("border", "1px solid #15803d", "important");
    button.style.setProperty("box-shadow", "0 0 0 1px rgba(255,255,255,0.08) inset", "important");
    button.style.setProperty("color", "#ffffff", "important");
    button.style.setProperty("pointer-events", "none", "important");
    button.style.setProperty("opacity", "1", "important");
    button.innerHTML = '<span class="whitespace-nowrap">Installed</span>';
    button.setAttribute("title", "Already installed");
    button.setAttribute("aria-label", "Installed");
    const tooltip = button.querySelector(".download-tooltip");
    if (tooltip) tooltip.remove();
  }};

  const unmarkInstalled = (button) => {{
    if (button.dataset.dadInstalled !== "1") return;
    button.dataset.dadInstalled = "0";
    if (button.dataset.dadOriginalHtml) {{
      button.innerHTML = button.dataset.dadOriginalHtml;
    }}
    if (button.dataset.dadOriginalTitle) {{
      button.setAttribute("title", button.dataset.dadOriginalTitle);
    }} else {{
      button.removeAttribute("title");
    }}
    button.style.removeProperty("background");
    button.style.removeProperty("border");
    button.style.removeProperty("box-shadow");
    button.style.removeProperty("color");
    button.style.removeProperty("pointer-events");
    button.style.removeProperty("opacity");
    button.removeAttribute("aria-label");
  }};

  const applyMarkers = () => {{
    for (const button of document.querySelectorAll("button.download-zip-button")) {{
      if (isInstalled(extractSongMeta(button))) {{
        markInstalled(button);
      }} else {{
        unmarkInstalled(button);
      }}
    }}
  }};

  window.__dadApplyInstalledMarkers = applyMarkers;
  if (!window.__dadInstalledObserver) {{
    const observer = new MutationObserver(() => {{
      window.requestAnimationFrame(() => window.__dadApplyInstalledMarkers?.());
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});
    window.__dadInstalledObserver = observer;
  }}

  applyMarkers();
}})();
"""
        self.page.runJavaScript(script)
