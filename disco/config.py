import json
import os
from pathlib import Path

if os.name == "nt":
    CONFIG_DIR = Path(os.environ["APPDATA"]) / "DiscoManager"
else:
    CONFIG_DIR = Path.home() / ".config" / "disco-manager"

CONFIG_FILE = CONFIG_DIR / "settings.json"

STEAM_APP_ID = "3404260"


def autodetect_imported_songs() -> Path | None:
    """Locate the game's ImportedSongs folder (engine name 'Pagoda')."""
    candidates: list[Path] = []
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidates.append(Path(local) / "Pagoda" / "Saved" / "ImportedSongs")
    else:
        home = Path.home()
        for steam in (home / ".steam/steam", home / ".local/share/Steam"):
            compat = steam / "steamapps/compatdata"
            if compat.exists():
                for appdir in compat.glob(
                    "*/pfx/drive_c/users/steamuser/"
                    "AppData/Local/Pagoda/Saved/ImportedSongs"
                ):
                    candidates.append(appdir)
    for path in candidates:
        if path.exists() or path.parent.exists():
            return path
    return None


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_imported_songs_path() -> Path | None:
    settings = load_settings()
    if "imported_songs_path" in settings:
        return Path(settings["imported_songs_path"])
    return None


def set_imported_songs_path(path: Path) -> None:
    settings = load_settings()
    settings["imported_songs_path"] = str(path)
    save_settings(settings)