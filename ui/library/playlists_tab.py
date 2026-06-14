import re
import shutil
import struct

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QSplitter,
    QDialog, QDialogButtonBox, QInputDialog, QMessageBox,
)

from disco import config, importer, playlists, bjpl, game
from ui.song_list import SongListWidget


class PlaylistsTab(QWidget):
    """Playlists: Template-based create, add/remove/reorder/rename/save/delete."""

    TEMPLATE_NAME = "Template"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._playlists: list[playlists.Playlist] = []
        self._current_pl_row = -1
        self._editing_name = ""
        self._editing_songs: list[tuple[str, str, int]] = []

        root = QVBoxLayout(self)
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

        self.refresh_playlists()

    # ---------- helpers ----------
    def _find_template(self):
        for pl in self._playlists:
            if pl.name.strip().lower() == self.TEMPLATE_NAME.lower():
                return pl
        return None

    def _warn_if_running(self) -> bool:
        if game.is_game_running():
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
        """Checkbox song picker; returns chosen MapFolders."""
        installed = importer.list_installed(config.get_imported_songs_path())
        dlg = QDialog(self); dlg.setWindowTitle(title); dlg.resize(580, 640)
        lay = QVBoxLayout(dlg)

        song_list = SongListWidget(disable_no_id=True)
        song_list.set_songs(installed)
        lay.addWidget(song_list, 1)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if not dlg.exec():
            return None
        return song_list.checked_maps()

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
