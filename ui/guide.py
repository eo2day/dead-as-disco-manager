from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox

from disco import game, platform


GUIDE_MARKDOWN = f"""
# User Guide

> **Always do playlist work with the game closed.** Dead as Disco rewrites its
> playlist files when it saves, so edits made while the game is open will be lost.

## Getting started

On launch, the app auto-detects your game's song folder. You can confirm or
change it on the **Home** page, which also shows where your playlists live.

If the folder wasn't detected, go to **Home**, click **Browse…** next to
"Imported songs folder", and select:
`{"%LOCALAPPDATA%\\\\Pagoda\\\\Saved\\\\ImportedSongs" if platform.WINDOWS else "~/.local/share/Steam/steamapps/compatdata/<appid>/pfx/drive_c/users/<user>/AppData/Local/Pagoda/Saved/ImportedSongs"}`

## Browsing and downloading songs

1. Open the **Browse** section.
2. Log in to your DiscoMaps account (only needed once — the app remembers you).
3. Find a map and download it as normal.
4. The app detects the download, extracts it, and installs it automatically.

Restart the game to see newly installed songs.

## Managing your installed songs

The **Library → Installed** tab lists every song with its **Length**, **BPM**,
and **Offset**.

- **Search** by title or artist using the search box.
- Click any column header to **sort** — Length, BPM, and Offset sort numerically.
- **Import .zip…** installs a map file you downloaded manually.
- To remove songs, **tick the checkboxes** (or use **Check all / none**),
  then click **Remove checked**.

## Restarting the game

Click **Restart game** (Library → Installed) to close Dead as Disco and relaunch it. {"On Linux/Proton this uses your Steam App ID rather than launching Pagoda.exe directly." if not game.supports_direct_game_exe() else ""}
Use this after making changes so they take effect.

## Playlists

### One-time setup: the Template

The manager builds new playlists from a blueprint:

1. In the **game**, create a new playlist named exactly **Template** and add one song.
2. Fully exit the game.
3. In the manager, open **Library → Playlists** and click **Rescan**.

The Template is protected — it can't be edited or deleted from the app.

### Creating a playlist

1. Make sure the game is **closed**.
2. On **Library → Playlists**, click **New playlist…**
3. Enter a name.
4. In the song picker, **tick the songs** you want (search and sort work here too),
   then click **OK**.
5. Restart the game to see your new playlist.

### Editing a playlist

Select a playlist, then use the buttons under the song list:

- **Add songs…** — add more songs from your library
- **Remove** — remove the selected song(s)
- **↑ / ↓** — reorder songs
- **Rename…** — change the playlist's name
- **Save** — write your changes (then restart the game)

> The manager only edits playlists made of **imported** songs. Playlists that
> contain built-in game songs must be edited in-game.

### Deleting a playlist

Select it and click **Delete playlist**. (The Template can't be deleted here.)

## Tips & troubleshooting

- **Changes don't show in-game?** Restart the game — it only reads playlists
  and songs at startup.
- **"Game is running" warning?** Close Dead as Disco before creating or
  saving playlists, or your changes will be overwritten.
- **A song you added doesn't appear in-game?** It may be a built-in game song
  (only imported songs can be added via the manager).
- **Backups:** the manager saves a `.bjpl.bak` copy the first time it edits a
  playlist, so your original is preserved.
"""


def show_guide_dialog(parent=None) -> None:
    dlg = QDialog(parent)
    dlg.setWindowTitle("User Guide")
    dlg.resize(700, 600)

    layout = QVBoxLayout(dlg)
    browser = QTextBrowser()
    browser.setMarkdown(GUIDE_MARKDOWN)
    layout.addWidget(browser)

    bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    bb.rejected.connect(dlg.reject)
    bb.button(QDialogButtonBox.StandardButton.Close).clicked.connect(dlg.accept)
    layout.addWidget(bb)

    dlg.exec()
