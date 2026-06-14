# Dead as Disco — Music Manager

> [!IMPORTANT]
> **Unofficial, AI-assisted community tool** — not affiliated with the
> developers of Dead as Disco or with DiscoMaps. Built largely with AI
> assistance to simplify my own workflow. Use at your own risk, and keep
> backups of your playlists and song files.

A desktop manager for the rhythm game **Dead as Disco**. Browse and download
custom songs, manage your installed library, and build in-game playlists —
all from one app.

---

## Features

- **Browse DiscoMaps** in an embedded browser and auto-import downloads
- **Import** map `.zip` files manually
- **Manage installed songs**: search, sort (artist / title / BPM / duration),
  and bulk-remove with checkboxes
- **Playlists**: create, edit, reorder, rename, and delete playlists of your
  imported songs
- **Restart the game** from the app to apply changes
- Simple sidebar navigation between **Home**, **Browse**, and **Library**

---

## Requirements

- Windows (the game and its file paths are Windows-based)
- Python 3.10+ (only needed to run from source — not for the packaged app)

## Install & run

**From the packaged release:** download the app zip from the
[Releases](../../releases) page, unzip it, and run `DiscoManager.exe`.

**From source:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If PowerShell blocks venv activation, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

---

# User Guide

> [!WARNING]
> Always do playlist work with the **game closed**. Dead as Disco rewrites its
> playlist files when it saves, so edits made while the game is open will be
> lost.

## Getting started

The left sidebar switches between three sections: **Home**, **Browse**, and
**Library**.

On launch, the app opens on the **Home** page and automatically finds your
game's song folder, shown under **Imported songs folder**.

![Home page](docs/screenshots/01-home-tab.png)

If the folder wasn't detected, click **Browse…** or **Auto-detect** next to
**Imported songs folder** and point it at:
`%LOCALAPPDATA%\Pagoda\Saved\ImportedSongs`

The Home page is also where you set the **game executable** (for restarting
the game), your **Steam App ID**, and the app **theme** (Dark/Light).

## Browsing and downloading songs

1. Open the **Browse** section in the sidebar.
2. Log in to your DiscoMaps account (only needed once — the app remembers you).
3. Find a map and download it as normal.
4. The app detects the download, extracts it, and installs it automatically.

![Browse tab](docs/screenshots/02-browse-tab.png)

Restart the game to see newly installed songs.

## Managing your installed songs

The **Library → Installed** tab lists every song with its **BPM** and **length**.

![Installed songs tab](docs/screenshots/03-installed-tab.png)

- **Search** by title or artist.
- **Sort** by artist, title, BPM, or duration, with a **Desc** toggle.
- **Import .zip…** installs a map file you downloaded manually.
- To remove songs, **tick the checkboxes** (or use **Check all / none**),
  then click **Remove checked**.

![Removing songs with checkboxes](docs/screenshots/04-remove-songs.png)

## Restarting the game

Click **Restart game** (Library → Installed tab) to close Dead as Disco and
relaunch it. Use this after making changes so they take effect.

## Playlists

### One-time setup: the Template

The manager builds new playlists from a blueprint:

1. In the **game**, create a new playlist named exactly **`Template`** and add one song
2. Fully exit the game.
3. In the manager, open **Library → Playlists** and click **Rescan**.

The Template is protected — it can't be edited or deleted from the app.

![Playlists tab](docs/screenshots/05-playlists-tab.png)

### Creating a playlist

1. Make sure the game is **closed**.
2. On the **Library → Playlists** tab, click **New playlist…**
3. Enter a name.
4. In the song picker, **tick the songs** you want (search and sort work
   here too), then click **OK**.
5. Restart the game to see your new playlist.

![Song picker dialog](docs/screenshots/06-song-picker.png)

### Editing a playlist

Select a playlist, then use the buttons under the song list:

- **Add songs…** — add more songs from your library
- **Remove** — remove the selected song(s)
- **↑ / ↓** — reorder songs
- **Rename…** — change the playlist's name
- **Save** — write your changes (then restart the game)

> [!NOTE]
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

---

## Building from source

```powershell
pip install pyinstaller
pyinstaller DiscoManager.spec
```

The runnable app is the **`dist/DiscoManager/`** folder (use the folder build,
not one-file — the embedded browser needs it). Zip and share that folder.

## Notes

- Settings and the embedded browser's login/cache are stored in
  `%APPDATA%\DiscoManager`.

---

> [!IMPORTANT]
> This is a fan-made tool, not affiliated with or endorsed by the creators of
> Dead as Disco or DiscoMaps. All custom songs and maps belong to their
> respective creators. Developed with AI assistance.