import json
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QTimer, QUrl, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtWebEngineCore import (
    QWebEngineDownloadRequest,
    QWebEnginePage,
    QWebEngineProfile,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from disco import config, game, importer

DISCOMAPS_URL = "https://discomaps.com"


class BrowserPage(QWebEnginePage):
    actionRequested = Signal(str, str)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme() == "dad":
            parsed = urlparse(url.toString())
            action = (parsed.netloc or parsed.path.lstrip("/")).strip()
            payload = parse_qs(parsed.query).get("path", [""])[0]
            self.actionRequested.emit(action, payload)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


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
        back = QPushButton("◀")
        fwd = QPushButton("▶")
        reload_btn = QPushButton("⟳")
        home = QPushButton("⌂")
        popout = QPushButton("Open in separate window")
        self.status = QLabel("")
        for b in (back, fwd, reload_btn, home):
            b.setMaximumWidth(60)
            nav.addWidget(b)
        nav.addWidget(popout)
        nav.addWidget(self.status, 1)
        layout.addLayout(nav)

        tools = QHBoxLayout()
        self.refresh_markers_btn = QPushButton("Refresh markers")
        self.refresh_markers_btn.clicked.connect(self._refresh_markers_clicked)
        self.hide_installed_btn = QPushButton("Hide installed")
        self.hide_installed_btn.setCheckable(True)
        self.hide_installed_btn.toggled.connect(self._hide_installed_toggled)
        self.low_motion_checkbox = QCheckBox("Low-Motion mode")
        self.low_motion_checkbox.toggled.connect(self._low_motion_toggled)
        self.legend = QLabel(
            'Legend: '
            '<span style="color:#16a34a;font-weight:600;">Installed</span> '
            '· <span style="color:#d97706;font-weight:600;">Update?</span> '
            '· <span style="color:#cbd5e1;">Not installed</span>'
        )
        self.legend.setTextFormat(Qt.RichText)
        tools.addWidget(self.refresh_markers_btn)
        tools.addWidget(self.hide_installed_btn)
        tools.addWidget(self.low_motion_checkbox)
        tools.addWidget(self.legend, 1)
        layout.addLayout(tools)

        self.profile = QWebEngineProfile("disco-manager", self)
        self.profile.setPersistentStoragePath(str(storage_dir / "web"))
        self.profile.setCachePath(str(storage_dir / "web-cache"))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(self._on_download)

        self.view = QWebEngineView(self)
        self.page = BrowserPage(self.profile, self)
        self.page.actionRequested.connect(self._on_page_action)
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
        popup_page = BrowserPage(self.profile, w)
        popup_page.actionRequested.connect(self._on_page_action)
        w.setPage(popup_page)
        w.resize(1100, 800)
        w.setUrl(QUrl(DISCOMAPS_URL))
        w.show()
        self._popout = w

    def _refresh_markers_clicked(self):
        self.status.setText("Refreshing installed markers…")
        self._sync_installed_markers()

    def _hide_installed_toggled(self, checked: bool):
        self.hide_installed_btn.setText("Show all songs" if checked else "Hide installed")
        self._sync_installed_markers()

    def _low_motion_toggled(self, _checked: bool):
        self._sync_installed_markers()

    def _on_page_action(self, action: str, payload: str):
        if action != "open-folder" or not payload:
            return
        try:
            game.open_in_file_manager(Path(payload))
            self.status.setText(f"Opened {Path(payload).name}")
        except RuntimeError as exc:
            self.status.setText(str(exc))

    def _on_download(self, download: QWebEngineDownloadRequest):
        download.setDownloadDirectory(str(self._download_dir))
        download.accept()
        name = download.downloadFileName()
        if name.lower().endswith(".zip"):
            self.status.setText(f"Downloading {name}…")
            download.isFinishedChanged.connect(lambda: self._finish(download))

    def _consume_pending_download_meta(self, callback):
        self.page.runJavaScript(
            "window.__dadConsumeLastDownloadMeta ? window.__dadConsumeLastDownloadMeta() : null;",
            callback,
        )

    def _finish(self, download: QWebEngineDownloadRequest):
        if download.state() != QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            return
        self._consume_pending_download_meta(lambda meta: self._finish_with_meta(download, meta))

    def _finish_with_meta(self, download: QWebEngineDownloadRequest, download_meta):
        zip_path = Path(download.downloadDirectory()) / download.downloadFileName()
        target = config.get_imported_songs_path()
        if not target:
            msg = "Set your ImportedSongs folder first (Home page)."
            self.status.setText(msg)
            self.imported.emit(msg)
            return
        try:
            installed = importer.import_zip(zip_path, target, download_meta)
        except importer.ImportError_ as e:
            msg = f"Import failed: {e}"
            self.status.setText(msg)
            self.imported.emit(msg)
            return
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
                "duration": song.duration,
                "site_id": song.site_map_id,
                "path": str(song.source),
            })
        return payload

    def _sync_installed_markers(self, *_args):
        payload = json.dumps(self._installed_song_payload())
        hide_installed = "true" if self.hide_installed_btn.isChecked() else "false"
        low_motion = "true" if self.low_motion_checkbox.isChecked() else "false"
        import_path = json.dumps(config.get_discomaps_imported_songs_path())
        script = """
(() => {
  const installedSongs = __PAYLOAD__;
  const hideInstalled = __HIDE_INSTALLED__;
  const lowMotion = __LOW_MOTION__;
  const configuredImportPath = __IMPORT_PATH__;

  const applyLowMotionMode = () => {
    const styleId = "dad-low-motion-style";
    let style = document.getElementById(styleId);
    if (lowMotion) {
      if (!style) {
        style = document.createElement("style");
        style.id = styleId;
        document.head.appendChild(style);
      }
      style.textContent = `
        html, body {
          background: #000000 !important;
        }
        #particle-canvas {
          display: none !important;
          visibility: hidden !important;
          opacity: 0 !important;
        }
      `;
      const particleCanvas = document.getElementById("particle-canvas");
      if (particleCanvas instanceof HTMLCanvasElement) {
        const ctx = particleCanvas.getContext("2d");
        ctx?.clearRect(0, 0, particleCanvas.width, particleCanvas.height);
      }
    } else if (style) {
      style.remove();
    }
  };

  const normalize = (value) => (value || "")
    .toString()
    .normalize("NFKD")
    .replace(/[\\u0300-\\u036f]/g, "")
    .replace(/[^a-z0-9]+/gi, " ")
    .trim()
    .toLowerCase();

  const parseDuration = (value) => {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    const parts = (value || "").toString().trim().split(":").map((part) => Number.parseInt(part, 10));
    if (!parts.length || parts.some((part) => Number.isNaN(part))) return null;
    let total = 0;
    for (const part of parts) total = total * 60 + part;
    return total;
  };

  const roundTempo = (value) => (typeof value === "number" && Number.isFinite(value) ? Math.round(value) : null);
  const installedById = new Map();
  const installedByKey = new Map();

  for (const song of installedSongs) {
    const normTitle = normalize(song.title);
    const normArtist = normalize(song.artist);
    if (!normTitle || !normArtist) continue;
    const normKey = `${normTitle}|${normArtist}`;
    const entry = {
      ...song,
      normTitle,
      normArtist,
      normKey,
      tempo: roundTempo(song.tempo),
      duration: parseDuration(song.duration),
    };
    if (entry.site_id) {
      installedById.set(entry.site_id, entry);
    }
    const bucket = installedByKey.get(normKey) || [];
    bucket.push(entry);
    installedByKey.set(normKey, bucket);
  }

  const extractSongMeta = (button) => {
    const card = button.closest(".p-6.relative")
      || button.closest("div[class*='p-6']")
      || button.parentElement;
    if (!card) return null;

    const rawTitle = (card.querySelector("h3")?.textContent || "").trim();
    const rawArtist = (card.querySelector("p")?.textContent || "").trim();
    const title = normalize(rawTitle);
    const artist = normalize(rawArtist);
    const bpmText = card.querySelector(".bpm-text")?.textContent || "";
    const bpmMatch = bpmText.match(/(\\d+)/);
    const tempo = bpmMatch ? Number.parseInt(bpmMatch[1], 10) : null;
    const durationText = (card.querySelector(".length-text")?.textContent || "").trim();
    const duration = parseDuration(durationText);
    const siteId = button.dataset.id || card.querySelector("[data-id]")?.dataset.id || null;

    if (!title || !artist) return null;
    return { card, button, rawTitle, rawArtist, title, artist, tempo, duration, siteId };
  };

  const classifySong = (entry) => {
    if (!entry) return { state: "none" };

    if (entry.siteId && installedById.has(entry.siteId)) {
      const exact = installedById.get(entry.siteId);
      const tempoMismatch = entry.tempo !== null && exact.tempo !== null && entry.tempo !== exact.tempo;
      const durationMismatch = entry.duration !== null && exact.duration !== null
        && Math.abs(entry.duration - exact.duration) > 1;
      if (!tempoMismatch && !durationMismatch) {
        return { state: "installed", song: exact };
      }
      return { state: "update", song: exact };
    }

    const similar = installedByKey.get(`${entry.title}|${entry.artist}`) || [];
    if (similar.length) {
      return { state: "update", song: similar[0] };
    }

    return { state: "none" };
  };

  const storeOriginalButton = (button) => {
    if (!button.dataset.dadOriginalHtml) {
      button.dataset.dadOriginalHtml = button.innerHTML;
      button.dataset.dadOriginalTitle = button.getAttribute("title") || "";
    }
  };

  const clearOpenButton = (button) => {
    button.parentElement?.querySelector(".dad-open-folder-button")?.remove();
  };

  const resetButton = (button) => {
    if (
      button.dataset.dadState === "none"
      && !button.parentElement?.querySelector(".dad-open-folder-button")
      && !button.hasAttribute("data-dad-open-folder")
    ) {
      return;
    }
    clearOpenButton(button);
    button.dataset.dadState = "none";
    button.removeAttribute("data-dad-open-folder");
    if (button.dataset.dadOriginalHtml) {
      button.innerHTML = button.dataset.dadOriginalHtml;
    }
    if (button.dataset.dadOriginalTitle) {
      button.setAttribute("title", button.dataset.dadOriginalTitle);
    } else {
      button.removeAttribute("title");
    }
    button.style.removeProperty("background");
    button.style.removeProperty("border");
    button.style.removeProperty("box-shadow");
    button.style.removeProperty("color");
    button.style.removeProperty("pointer-events");
    button.style.removeProperty("opacity");
    button.style.removeProperty("flex");
    button.removeAttribute("aria-label");
  };

  const ensureOpenButton = (button, song) => {
    let openButton = button.parentElement?.querySelector(".dad-open-folder-button");
    if (!openButton) {
      openButton = document.createElement("button");
      openButton.type = "button";
      openButton.className = "dad-open-folder-button h-12 text-white font-bold py-3 px-2 rounded-lg flex items-center justify-center text-sm";
      button.parentElement?.insertBefore(openButton, button);
    }
    openButton.dataset.dadOpenFolder = song.path || "";
    openButton.textContent = "Open folder";
    openButton.style.setProperty("background", "#166534", "important");
    openButton.style.setProperty("border", "1px solid #15803d", "important");
    openButton.style.setProperty("color", "#ffffff", "important");
    openButton.style.setProperty("flex", "1 1 0", "important");
    return openButton;
  };

  const markInstalled = (entry, song) => {
    const button = entry.button;
    const targetPath = song.path || "";
    if (
      button.dataset.dadState === "installed"
      && button.getAttribute("data-dad-open-folder") === targetPath
      && button.textContent?.trim() === "Installed"
    ) {
      return;
    }
    storeOriginalButton(button);
    clearOpenButton(button);
    button.dataset.dadState = "installed";
    button.dataset.dadOpenFolder = targetPath;
    button.style.setProperty("background", "#16a34a", "important");
    button.style.setProperty("border", "1px solid #15803d", "important");
    button.style.setProperty("box-shadow", "0 0 0 1px rgba(255,255,255,0.08) inset", "important");
    button.style.setProperty("color", "#ffffff", "important");
    button.style.setProperty("pointer-events", "auto", "important");
    button.style.setProperty("opacity", "1", "important");
    button.innerHTML = '<span class="whitespace-nowrap">Installed</span>';
    button.setAttribute("title", "Open local song folder");
    button.setAttribute("aria-label", "Installed");
  };

  const markUpdate = (entry, song) => {
    const button = entry.button;
    const targetPath = song.path || "";
    const existingOpenButton = button.parentElement?.querySelector(".dad-open-folder-button");
    if (
      button.dataset.dadState === "update"
      && button.textContent?.trim() === "Update?"
      && existingOpenButton?.getAttribute("data-dad-open-folder") === targetPath
    ) {
      return;
    }
    storeOriginalButton(button);
    const openButton = ensureOpenButton(button, song);
    button.dataset.dadState = "update";
    button.removeAttribute("data-dad-open-folder");
    button.style.setProperty("background", "#d97706", "important");
    button.style.setProperty("border", "1px solid #b45309", "important");
    button.style.setProperty("box-shadow", "0 0 0 1px rgba(255,255,255,0.08) inset", "important");
    button.style.setProperty("color", "#ffffff", "important");
    button.style.setProperty("pointer-events", "auto", "important");
    button.style.setProperty("opacity", "1", "important");
    button.style.setProperty("flex", "1 1 0", "important");
    button.innerHTML = '<span class="whitespace-nowrap">Update?</span>';
    button.setAttribute("title", "Download this version");
    button.setAttribute("aria-label", "Update");
    openButton.setAttribute("title", "Open local song folder");
  };

  const maybeSeedImportPath = () => {
    if (!configuredImportPath || typeof window.dmGetImportPath !== "function") return;
    let currentPath = "";
    try {
      currentPath = window.dmGetImportPath() || "";
    } catch (_error) {
      currentPath = "";
    }
    if (currentPath) return;

    if (typeof window.dmOpenImportPathModal === "function") {
      window.dmOpenImportPathModal();
    }

    const apply = () => {
      const input = document.getElementById("import-path-input");
      const save = document.getElementById("import-path-save");
      if (!input || !save) return;
      input.value = configuredImportPath;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      save.click();
    };

    window.requestAnimationFrame(() => window.requestAnimationFrame(apply));
  };

  const applyMarkers = () => {
    for (const button of document.querySelectorAll("button.download-zip-button")) {
      const entry = extractSongMeta(button);
      const state = classifySong(entry);
      if (!entry) continue;
      if (state.state === "installed") {
        markInstalled(entry, state.song);
      } else if (state.state === "update") {
        markUpdate(entry, state.song);
      } else {
        resetButton(button);
      }
      const shouldHide = hideInstalled && (state.state === "installed" || state.state === "update");
      entry.card.style.display = shouldHide ? "none" : "";
    }
  };

  if (!window.__dadFolderHandlerInstalled) {
    document.addEventListener("click", (event) => {
      const openTrigger = event.target.closest("[data-dad-open-folder]");
      if (openTrigger) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        const path = openTrigger.getAttribute("data-dad-open-folder") || "";
        if (path) {
          window.location.href = `dad://open-folder?path=${encodeURIComponent(path)}`;
        }
        return;
      }

      const downloadButton = event.target.closest("button.download-zip-button[data-id]");
      if (!downloadButton) return;
      const meta = extractSongMeta(downloadButton);
      if (!meta) return;
      window.__dadLastDownloadMeta = {
        site_id: meta.siteId,
        title: meta.rawTitle,
        artist: meta.rawArtist,
        tempo: meta.tempo,
        duration: meta.duration,
      };
    }, true);
    window.__dadFolderHandlerInstalled = true;
  }

  window.__dadConsumeLastDownloadMeta = () => {
    const value = window.__dadLastDownloadMeta || null;
    window.__dadLastDownloadMeta = null;
    return value;
  };
  window.__dadApplyInstalledMarkers = applyMarkers;

  if (!window.__dadInstalledObserver) {
    const observer = new MutationObserver(() => {
      window.requestAnimationFrame(() => window.__dadApplyInstalledMarkers?.());
    });
    observer.observe(document.body, { childList: true, subtree: true });
    window.__dadInstalledObserver = observer;
  }

  maybeSeedImportPath();
  applyLowMotionMode();
  applyMarkers();
})();
"""
        script = (
            script.replace("__PAYLOAD__", payload)
            .replace("__HIDE_INSTALLED__", hide_installed)
            .replace("__LOW_MOTION__", low_motion)
            .replace("__IMPORT_PATH__", import_path)
        )
        self.page.runJavaScript(script)
