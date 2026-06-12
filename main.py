
# Dead as Disco Music Manager — developed with AI assistance (Anthropic Claude).

import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--use-gl=angle --use-angle=d3d11"

import re
import sys
import time
import struct
import shutil
import subprocess
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QSplitter, QDialog, QDialogButtonBox, QInputDialog,
    QLineEdit, QComboBox, QCheckBox,
)

from disco import config, importer, playlists, bjpl
from disco.browser import BrowseTab

SORT_OPTIONS = ["Artist", "Title", "BPM", "Duration"]


def song_label(m) -> str:
    meta = []
    if m.tempo:
        meta.append(f"{m.tempo} BPM")
    if m.duration:
        s = int(round(m.duration))
        meta.append(f"{s // 60}:{s % 60:02d}")
    base = f"{m.artist} — {m.title}"
    return base + ("   ·  " + "  ·  ".join(meta) if meta else "")


def filter_sort(maps, query, sort_key, descending):
    q = (query or "").strip().lower()
    res = [m for m in maps if (q in m.artist.lower() or q in m.title.lower())] if q else list(maps)
    if sort_key == "Title":
        res.sort(key=lambda m: (m.title.lower(), m.artist.lower()), reverse=descending)
    elif sort_key in ("BPM", "Duration"):
        attr = "tempo" if sort_key == "BPM" else "duration"
        have = [m for m in res if getattr(m, attr) is not None]
        missing = [m for m in res if getattr(m, attr) is None]
        have.sort(key=lambda m: getattr(m, attr), reverse=descending)
        res = have + missing
    else:  # Artist
        res.sort(key=lambda m: (m.artist.lower(), m.title.lower()), reverse=descending)
    return res


class MainWindow(QMainWindow):
    TEMPLATE_NAME = "Template"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dead as Disco — Music Manager")
        icon_path = Path(__file__).parent / "icon.png"
        if hasattr(sys, "_MEIPASS"):                 # running from PyInstaller bundle
            icon_path = Path(sys._MEIPASS) / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1000, 700)

        self._playlists: list[playlists.Playlist] = []
        self._current_pl_row = -1
        self._editing_name = ""
        self._editing_songs: list[tuple[str, str, int]] = []
        self._all_installed: list = []
        self._checked: set[str] = set()

        tabs = QTabWidget()
        self.browse = BrowseTab(config.CONFIG_DIR, self)
        self.browse.imported.connect(lambda _m: self.refresh_list())
        tabs.addTab(self.browse, "Browse DiscoMaps")
        tabs.addTab(self._build_installed_tab(), "Installed")
        tabs.addTab(self._build_playlists_tab(), "Playlists")

        self.setCentralWidget(tabs)
        self.resolve_path_on_start()

    # ---------- installed tab ----------
    def _build_installed_tab(self):
        w = QWidget(); root = QVBoxLayout(w)
        self.path_label = QLabel(); root.addWidget(self.path_label)

        b = QHBoxLayout()
        imp = QPushButton("Import .zip…"); imp.clicked.connect(self.import_zip)
        ref = QPushButton("Refresh"); ref.clicked.connect(self.refresh_list)
        chk = QPushButton("Check all / none"); chk.clicked.connect(self.toggle_all_checks)
        rm = QPushButton("Remove checked"); rm.clicked.connect(self.remove_song)
        restart = QPushButton("Restart game"); restart.clicked.connect(self.restart_game)
        ch = QPushButton("Change folder…"); ch.clicked.connect(self.choose_folder)
        b.addWidget(imp); b.addWidget(ref); b.addWidget(chk); b.addWidget(rm)
        b.addStretch(); b.addWidget(restart); b.addWidget(ch)
        root.addLayout(b)

        fr = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search title or artist…")
        self.search.textChanged.connect(self.render_installed)
        self.sort = QComboBox(); self.sort.addItems(SORT_OPTIONS)
        self.sort.currentIndexChanged.connect(self.render_installed)
        self.desc = QCheckBox("Desc"); self.desc.toggled.connect(self.render_installed)
        fr.addWidget(self.search, 1)
        fr.addWidget(QLabel("Sort:")); fr.addWidget(self.sort); fr.addWidget(self.desc)
        root.addLayout(fr)

        root.addWidget(QLabel("Installed songs:"))
        self.song_list = QListWidget()
        self.song_list.itemChanged.connect(self._on_song_check)
        root.addWidget(self.song_list)
        return w

    # ---------- playlists tab ----------
    def _build_playlists_tab(self):
        w = QWidget(); root = QVBoxLayout(w)
        top = QHBoxLayout()
        newpl = QPushButton("New playlist…"); newpl.clicked.connect(self.new_playlist)
        rescan = QPushButton("Rescan"); rescan.clicked.connect(self.refresh_playlists)
        delpl = QPushButton("Delete playlist"); delpl.clicked.connect(self.delete_playlist)
        top.addWidget(newpl); top.addWidget(rescan); top.addWidget(delpl); top.addStretch()
        root.addLayout(top)

        split = QSplitter()
        self.playlist_list = QListWidget()
        self.playlist_list.currentRowChanged.connect(self._select_playlist)
        split.addWidget(self.playlist_list)

        right = QWidget(); rl = QVBoxLayout(right)
        self.playlist_songs = QListWidget()
        rl.addWidget(self.playlist_songs)
        eb = QHBoxLayout()
        for label, slot in [("Add songs…", self.add_songs), ("Remove", self.remove_songs),
                            ("↑", self.move_up), ("↓", self.move_down),
                            ("Rename…", self.rename_playlist), ("Save", self.save_playlist)]:
            btn = QPushButton(label); btn.clicked.connect(slot); eb.addWidget(btn)
        rl.addLayout(eb)
        split.addWidget(right)
        split.setSizes([300, 600])
        root.addWidget(split)
        return w

    # ---------- helpers ----------
    def _find_template(self):
        for pl in self._playlists:
            if pl.name.strip().lower() == self.TEMPLATE_NAME.lower():
                return pl
        return None

    def _warn_if_running(self) -> bool:
        if config.is_game_running():
            QMessageBox.warning(
                self, "Game is running",
                "Dead as Disco is open. It rewrites playlist files when it saves, "
                "so changes you make now will be lost.\n\nClose the game first, then try again.")
            return True
        return False

    # ---------- playlist data ----------
    def refresh_playlists(self):
        self.playlist_list.clear(); self.playlist_songs.clear()
        self._editing_songs = []; self._current_pl_row = -1
        path = config.get_imported_songs_path()
        if not path:
            return
        self._playlists = playlists.find_playlists(path)
        if not self._playlists:
            self.playlist_list.addItem("(no playlists found)")
            return
        for pl in self._playlists:
            self.playlist_list.addItem(f"{pl.name}  ({len(pl.songs)} songs)")

    def _select_playlist(self, row):
        self._current_pl_row = row
        self._editing_songs = []
        if not (0 <= row < len(self._playlists)):
            self.playlist_songs.clear(); return
        st = bjpl.parse(self._playlists[row].path.read_bytes())
        self._editing_name = st["name"]
        ids = [struct.unpack("<I", h)[0] for h, _ in st["trailer"]]
        for pth, uid in zip(st["paths"], ids):
            disp = re.sub(r".*SongCatalogSubsystem_\d+\.", "", pth) \
                if "SongCatalogSubsystem_" in pth else pth
            self._editing_songs.append((disp, pth, uid))
        self._render_songs()

    def _render_songs(self):
        self.playlist_songs.clear()
        for disp, _p, _u in self._editing_songs:
            self.playlist_songs.addItem(disp)

    def _pick_songs_dialog(self, title):
        """Checkbox song picker with search + sort; returns chosen MapFolders."""
        installed = importer.list_installed(config.get_imported_songs_path())
        dlg = QDialog(self); dlg.setWindowTitle(title); dlg.resize(580, 640)
        lay = QVBoxLayout(dlg)

        fr = QHBoxLayout()
        search = QLineEdit(); search.setPlaceholderText("Search title or artist…")
        sort = QComboBox(); sort.addItems(SORT_OPTIONS)
        desc = QCheckBox("Desc")
        fr.addWidget(search, 1); fr.addWidget(QLabel("Sort:")); fr.addWidget(sort); fr.addWidget(desc)
        lay.addLayout(fr)

        lst = QListWidget(); lay.addWidget(lst, 1)
        checked: set[str] = set()

        def render():
            lst.blockSignals(True)
            lst.clear()
            for m in filter_sort(installed, search.text(), sort.currentText(), desc.isChecked()):
                it = QListWidgetItem(song_label(m))
                it.setData(Qt.ItemDataRole.UserRole, m)
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                it.setCheckState(Qt.CheckState.Checked if str(m.source) in checked
                                 else Qt.CheckState.Unchecked)
                if m.unique_id is None:
                    it.setText(it.text() + "   (no ID — can't add)")
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                lst.addItem(it)
            lst.blockSignals(False)

        def on_change(it):
            m = it.data(Qt.ItemDataRole.UserRole)
            if not m:
                return
            k = str(m.source)
            if it.checkState() == Qt.CheckState.Checked:
                checked.add(k)
            else:
                checked.discard(k)

        lst.itemChanged.connect(on_change)
        search.textChanged.connect(render)
        sort.currentIndexChanged.connect(render)
        desc.toggled.connect(render)
        render()

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if not dlg.exec():
            return None
        return [m for m in installed if str(m.source) in checked and m.unique_id is not None]

    def new_playlist(self):
        tmpl = self._find_template()
        if not tmpl:
            QMessageBox.warning(
                self, "No Template playlist",
                "Create a playlist named exactly \"Template\" in-game first "
                "(it can have any songs — they're ignored), exit, then Rescan.\n\n"
                "The manager uses that playlist as the blueprint for new ones.")
            return
        if self._warn_if_running():
            return
        name, ok = QInputDialog.getText(self, "New playlist", "Playlist name:")
        if not (ok and name.strip()):
            return
        if name.strip().lower() == self.TEMPLATE_NAME.lower():
            QMessageBox.warning(self, "Reserved name",
                                "\"Template\" is reserved as the blueprint. Pick another name.")
            return
        picked = self._pick_songs_dialog("Choose songs for the new playlist")
        if picked is None:
            return
        prefix = bjpl.catalog_prefix([p.path for p in self._playlists])
        songs = [(bjpl.song_ref(prefix, m.artist, m.title), m.unique_id) for m in picked]
        try:
            bjpl.create_from_template(tmpl.path, name.strip(), songs, tmpl.path.parent)
        except Exception as e:
            QMessageBox.critical(self, "Create failed", str(e)); return
        QMessageBox.information(self, "Created",
                                f"Created “{name.strip()}”. Restart the game to see it.")
        self.refresh_playlists()

    def add_songs(self):
        if not (0 <= self._current_pl_row < len(self._playlists)):
            QMessageBox.warning(self, "No playlist", "Select a playlist first."); return
        picked = self._pick_songs_dialog("Add songs to this playlist")
        if not picked:
            return
        prefix = bjpl.catalog_prefix([p.path for p in self._playlists])
        for m in picked:
            self._editing_songs.append(
                (f"{m.artist} — {m.title}", bjpl.song_ref(prefix, m.artist, m.title), m.unique_id))
        self._render_songs()

    def remove_songs(self):
        rows = sorted((self.playlist_songs.row(it)
                       for it in self.playlist_songs.selectedItems()), reverse=True)
        if not rows:
            r = self.playlist_songs.currentRow()
            if r >= 0:
                rows = [r]
        for i in rows:
            del self._editing_songs[i]
        self._render_songs()

    def move_up(self):
        i = self.playlist_songs.currentRow()
        if i > 0:
            self._editing_songs[i-1], self._editing_songs[i] = \
                self._editing_songs[i], self._editing_songs[i-1]
            self._render_songs(); self.playlist_songs.setCurrentRow(i-1)

    def move_down(self):
        i = self.playlist_songs.currentRow()
        if 0 <= i < len(self._editing_songs) - 1:
            self._editing_songs[i+1], self._editing_songs[i] = \
                self._editing_songs[i], self._editing_songs[i+1]
            self._render_songs(); self.playlist_songs.setCurrentRow(i+1)

    def rename_playlist(self):
        if not (0 <= self._current_pl_row < len(self._playlists)):
            return
        new, ok = QInputDialog.getText(self, "Rename playlist", "Name:", text=self._editing_name)
        if ok and new.strip():
            self._editing_name = new.strip()
            QMessageBox.information(self, "Renamed", "Click Save to write the change.")

    def save_playlist(self):
        if not (0 <= self._current_pl_row < len(self._playlists)):
            return
        pl = self._playlists[self._current_pl_row]
        if pl.name.strip().lower() == self.TEMPLATE_NAME.lower():
            QMessageBox.warning(
                self, "Protected",
                "The \"Template\" playlist is the blueprint and can't be edited here. "
                "Use New playlist… to make a copy with your songs instead.")
            return
        if any(not bjpl.is_importable_ref(p) for _d, p, _u in self._editing_songs):
            QMessageBox.warning(
                self, "Can't save this playlist",
                "This playlist contains built-in game songs, which the manager "
                "can't rewrite safely. Edit it in-game instead.")
            return
        if self._warn_if_running():
            return
        st = bjpl.parse(pl.path.read_bytes())
        songs = [(p, uid) for _d, p, uid in self._editing_songs]
        try:
            data = bjpl.build(st, name=self._editing_name, songs=songs)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e)); return
        bak = pl.path.with_suffix(".bjpl.bak")
        if not bak.exists():
            shutil.copy2(pl.path, bak)
        pl.path.write_bytes(data)
        QMessageBox.information(self, "Saved",
                                "Playlist saved. Restart the game to see the changes.")
        self.refresh_playlists()

    def delete_playlist(self):
        if not (0 <= self._current_pl_row < len(self._playlists)):
            QMessageBox.warning(self, "No playlist", "Select a playlist first."); return
        pl = self._playlists[self._current_pl_row]
        if pl.name.strip().lower() == self.TEMPLATE_NAME.lower():
            QMessageBox.warning(
                self, "Protected",
                "The \"Template\" playlist is the blueprint for new playlists "
                "and can't be deleted here. Remove it in-game if you really mean to.")
            return
        confirm = QMessageBox.question(
            self, "Delete playlist",
            f"Delete the playlist “{pl.name}”?\n\nThis removes its .bjpl file.")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            pl.path.unlink()
        except OSError as e:
            QMessageBox.critical(self, "Couldn't delete", str(e)); return
        self.refresh_playlists()

    # ---------- path handling ----------
    def resolve_path_on_start(self):
        saved = config.get_imported_songs_path()
        if saved and saved.parent.exists():
            self.set_path(saved); return
        detected = config.autodetect_imported_songs()
        if detected:
            self.set_path(detected)
        else:
            self.path_label.setText("Couldn't auto-detect ImportedSongs. Use “Change folder…”.")

    def choose_folder(self):
        detected = config.autodetect_imported_songs()
        start = str(detected.parent if detected else Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Select your ImportedSongs folder", start)
        if chosen:
            self.set_path(Path(chosen))

    def set_path(self, path):
        config.set_imported_songs_path(path)
        self.path_label.setText(f"ImportedSongs: {path}")
        self.refresh_list(); self.refresh_playlists()

    def current_path(self):
        return config.get_imported_songs_path()

    # ---------- installed songs ----------
    def refresh_list(self):
        path = self.current_path()
        self._all_installed = importer.list_installed(path) if path else []
        self._checked.clear()
        self.render_installed()

    def render_installed(self):
        self.song_list.blockSignals(True)
        self.song_list.clear()
        if not self._all_installed:
            self.song_list.addItem("(no songs installed yet)")
            self.song_list.blockSignals(False)
            return
        maps = filter_sort(self._all_installed, self.search.text(),
                           self.sort.currentText(), self.desc.isChecked())
        for m in maps:
            it = QListWidgetItem(song_label(m))
            it.setData(Qt.ItemDataRole.UserRole, m)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if str(m.source) in self._checked
                             else Qt.CheckState.Unchecked)
            self.song_list.addItem(it)
        self.song_list.blockSignals(False)

    def _on_song_check(self, item):
        m = item.data(Qt.ItemDataRole.UserRole)
        if not m:
            return
        k = str(m.source)
        if item.checkState() == Qt.CheckState.Checked:
            self._checked.add(k)
        else:
            self._checked.discard(k)

    def toggle_all_checks(self):
        visible = [self.song_list.item(i) for i in range(self.song_list.count())
                   if self.song_list.item(i).data(Qt.ItemDataRole.UserRole)]
        any_unchecked = any(it.checkState() != Qt.CheckState.Checked for it in visible)
        state = Qt.CheckState.Checked if any_unchecked else Qt.CheckState.Unchecked
        for it in visible:
            it.setCheckState(state)

    def remove_song(self):
        maps = [m for m in self._all_installed if str(m.source) in self._checked]
        if not maps:
            QMessageBox.warning(self, "Nothing checked", "Tick the songs you want to remove.")
            return
        detail = f'"{maps[0].artist} — {maps[0].title}"' if len(maps) == 1 else f"{len(maps)} songs"
        confirm = QMessageBox.question(
            self, "Remove songs",
            f"Delete {detail} from ImportedSongs?\n\nThis deletes the folders from disk.")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        failed = []
        for m in maps:
            try:
                shutil.rmtree(m.source)
            except OSError as e:
                failed.append(f"{m.title}: {e}")
        if failed:
            QMessageBox.critical(self, "Some removals failed", "\n".join(failed))
        self.refresh_list()

    def import_zip(self):
        path = self.current_path()
        if not path:
            QMessageBox.warning(self, "No folder", "Set your ImportedSongs folder first."); return
        zf, _ = QFileDialog.getOpenFileName(self, "Choose a downloaded map zip",
                                            str(Path.home() / "Downloads"), "Zip archives (*.zip)")
        if not zf:
            return
        try:
            installed = importer.import_zip(Path(zf), path)
        except importer.ImportError_ as e:
            QMessageBox.critical(self, "Import failed", str(e)); return
        QMessageBox.information(self, "Imported", "Installed:\n" + "\n".join(installed) +
                               "\n\nRestart the game to see them.")
        self.refresh_list()

    def restart_game(self):
        exe = config.find_game_exe()
        if not exe:
            QMessageBox.warning(self, "Game not found",
                                "Couldn't find Pagoda.exe. Launch the game from Steam.")
            return
        if os.name == "nt":
            for name in ("PagodaSteam-Win64-Shipping.exe", "Pagoda.exe"):
                subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
        time.sleep(1.0)
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        QMessageBox.information(self, "Restarting", f"Relaunched {exe.name}.")


if __name__ == "__main__":
    if os.name == "nt":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DiscoManager")
        except Exception:
            pass
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())