## Development note

This project was developed with substantial help from an AI assistant
(Anthropic's Claude), including reverse-engineering the game's playlist
format and writing most of the code. It has been tested by the author but,
as with any software, use it at your own risk and keep backups of your
playlists and song files.



# Dead as Disco — Music Manager

A desktop manager for the rhythm game **Dead as Disco**. Browse and download
custom songs, manage your installed library, and build in-game playlists —
all from one app.

## Features

- **Browse DiscoMaps** in an embedded browser and auto-import downloads
- **Import** map `.zip` files manually
- **Manage installed songs**: search, sort (artist / title / BPM / duration),
  and bulk-remove with checkboxes
- **Playlists**: create, edit, reorder, rename, and delete playlists of your
  imported songs
- **Restart the game** from the app to apply changes

## Requirements

- Windows (the game and its file paths are Windows-based)
- Python 3.10+

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If PowerShell blocks venv activation, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## How playlists work (important)

The game stores playlists as `.bjpl` files and **rewrites them whenever it
saves**. So:

- Do all playlist creation/editing in the manager **with the game closed**,
  then use **Restart game** to launch and apply changes.
- Playlist creation copies a blueprint playlist named **`Template`**. Create
  one playlist called exactly `Template` in-game once; the manager uses it as
  the basis for new playlists and protects it from edits/deletion.
- The manager only manages **imported** songs in playlists. Playlists
  containing built-in game songs are left to be edited in-game.

## Building an executable

```powershell
pip install pyinstaller
pyinstaller DiscoManager.spec
```

The runnable app is the **`dist/DiscoManager/`** folder (use the folder build,
not one-file — the embedded browser needs it). Zip and share that folder.

## Notes

- Settings and the embedded browser's login/cache are stored in
  `%APPDATA%\DiscoManager`.
- This is an unofficial, community tool and is not affiliated with the game's
  developers or with DiscoMaps.