import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox,
)

from disco import config, importer, game
from ui.song_list import SongListWidget


class InstalledTab(QWidget):
    """Installed songs: search/sort/check, import, remove, restart game."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_installed: list = []

        root = QVBoxLayout(self)

        b = QHBoxLayout()
        imp = QPushButton("Import .zip…"); imp.clicked.connect(self.import_zip)
        ref = QPushButton("Refresh"); ref.clicked.connect(self.refresh)
        chk = QPushButton("Check all / none"); chk.clicked.connect(self.toggle_all_checks)
        rm = QPushButton("Remove checked"); rm.clicked.connect(self.remove_song)
        restart = QPushButton("Restart game"); restart.clicked.connect(self.restart_game)
        fix = QPushButton("Fix songs for 0.1.1"); fix.clicked.connect(self.repair_meta)
        b.addWidget(imp); b.addWidget(ref); b.addWidget(chk); b.addWidget(rm)
        b.addWidget(fix)
        b.addStretch(); b.addWidget(restart)
        root.addLayout(b)

        self.song_list = SongListWidget()
        root.addWidget(self.song_list)

        self.refresh()

    def current_path(self):
        return config.get_imported_songs_path()

    def refresh(self):
        path = self.current_path()
        self._all_installed = importer.list_installed(path) if path else []
        self.song_list.set_songs(self._all_installed)

    def toggle_all_checks(self):
        self.song_list.toggle_all()

    def remove_song(self):
        maps = self.song_list.checked_maps()
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
        self.refresh()

    def import_zip(self):
        path = self.current_path()
        if not path:
            QMessageBox.warning(self, "No folder", "Set your ImportedSongs folder on the Home page first.")
            return
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
        self.refresh()

    def repair_meta(self):
        path = self.current_path()
        if not path:
            QMessageBox.warning(self, "No folder", "Set your ImportedSongs folder on the Home page first.")
            return
        if game.is_game_running():
            QMessageBox.warning(
                self, "Game is running",
                "Dead as Disco is open. Close the game first, then try again.")
            return
        fixed, skipped, errors = importer.repair_installed(str(path))
        msg = f"Fixed {fixed} song(s), skipped {skipped}."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(f"  {name}: {err}" for name, err in errors)
        QMessageBox.information(self, "Repair complete", msg)

    def restart_game(self):
        exe = config.get_game_exe_path() or game.find_game_exe()
        if game.supports_direct_game_exe() and not exe:
            QMessageBox.warning(self, "Game not found",
                                "Couldn't find Pagoda.exe. Set it on the Home page or launch the game from Steam.")
            return
        try:
            game.restart_game(exe)
        except RuntimeError as e:
            QMessageBox.critical(self, "Restart failed", str(e))
            return
        detail = exe.name if exe else "the Steam game entry"
        QMessageBox.information(self, "Restarting", f"Relaunched {detail}.")
