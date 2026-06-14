from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QGroupBox, QMessageBox,
)

from disco import config, game
from disco.playlists import saved_root


class HomePage(QWidget):
    """Home / settings page: file paths, Steam App ID, theme, user guide."""

    pathsChanged = Signal()
    themeChanged = Signal(str)
    guideRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.addStretch()

        paths_box = QGroupBox("File paths")
        form = QFormLayout(paths_box)

        self.songs_edit = QLineEdit()
        self.songs_edit.textChanged.connect(self._update_playlists_path)
        songs_row = QHBoxLayout()
        songs_browse = QPushButton("Browse…")
        songs_browse.clicked.connect(self._browse_songs)
        songs_auto = QPushButton("Auto-detect")
        songs_auto.clicked.connect(self._autodetect_songs)
        songs_row.addWidget(self.songs_edit, 1)
        songs_row.addWidget(songs_browse)
        songs_row.addWidget(songs_auto)
        form.addRow("Imported songs folder:", songs_row)

        self.playlists_edit = QLineEdit()
        self.playlists_edit.setReadOnly(True)
        form.addRow("Playlists folder:", self.playlists_edit)

        self.exe_edit = QLineEdit()
        exe_row = QHBoxLayout()
        exe_browse = QPushButton("Browse…")
        exe_browse.clicked.connect(self._browse_exe)
        exe_auto = QPushButton("Auto-detect")
        exe_auto.clicked.connect(self._autodetect_exe)
        exe_row.addWidget(self.exe_edit, 1)
        exe_row.addWidget(exe_browse)
        exe_row.addWidget(exe_auto)
        form.addRow("Game executable (Pagoda.exe):", exe_row)

        layout.addWidget(paths_box)

        other_box = QGroupBox("Other settings")
        other_form = QFormLayout(other_box)

        self.steam_edit = QLineEdit()
        other_form.addRow("Steam App ID:", self.steam_edit)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        other_form.addRow("Theme:", self.theme_combo)

        layout.addWidget(other_box)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        guide_btn = QPushButton("User Guide")
        guide_btn.clicked.connect(self.guideRequested.emit)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        btn_row.addWidget(guide_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        self._load()

    def _load(self) -> None:
        songs = config.get_imported_songs_path()
        self.songs_edit.setText(str(songs) if songs else "")

        exe = config.get_game_exe_path() or game.find_game_exe()
        self.exe_edit.setText(str(exe) if exe else "")

        self.steam_edit.setText(config.get_steam_app_id())

        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText("Light" if config.get_theme() == "light" else "Dark")
        self.theme_combo.blockSignals(False)

        self._update_playlists_path()

    def _update_playlists_path(self) -> None:
        songs = self.songs_edit.text().strip()
        if not songs:
            self.playlists_edit.setText("")
            return
        root = saved_root(Path(songs))
        derived = (root / "Playlists") if root else Path(songs)
        self.playlists_edit.setText(str(derived))

    def _browse_songs(self) -> None:
        start = self.songs_edit.text() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Select your ImportedSongs folder", start)
        if chosen:
            self.songs_edit.setText(chosen)

    def _autodetect_songs(self) -> None:
        detected = config.autodetect_imported_songs()
        if detected:
            self.songs_edit.setText(str(detected))
        else:
            QMessageBox.warning(self, "Not found", "Couldn't auto-detect the ImportedSongs folder.")

    def _browse_exe(self) -> None:
        start = self.exe_edit.text() or str(Path.home())
        chosen, _ = QFileDialog.getOpenFileName(
            self, "Select Pagoda.exe", start, "Executable (*.exe)")
        if chosen:
            self.exe_edit.setText(chosen)

    def _autodetect_exe(self) -> None:
        detected = game.find_game_exe()
        if detected:
            self.exe_edit.setText(str(detected))
        else:
            QMessageBox.warning(self, "Not found", "Couldn't auto-detect Pagoda.exe.")

    def _on_theme_changed(self, text: str) -> None:
        name = "light" if text == "Light" else "dark"
        config.set_theme(name)
        self.themeChanged.emit(name)

    def _save(self) -> None:
        songs = self.songs_edit.text().strip()
        if songs:
            config.set_imported_songs_path(Path(songs))

        exe = self.exe_edit.text().strip()
        if exe:
            config.set_game_exe_path(Path(exe))

        steam_id = self.steam_edit.text().strip()
        if steam_id:
            config.set_steam_app_id(steam_id)

        self.pathsChanged.emit()
        QMessageBox.information(self, "Saved", "Settings saved.")
