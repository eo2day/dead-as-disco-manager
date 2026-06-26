import json
from pathlib import Path

from disco import platform

CONFIG_DIR = platform.config_dir()

CONFIG_FILE = CONFIG_DIR / "settings.json"

STEAM_APP_ID = "3404260"


def autodetect_imported_songs() -> Path | None:
    """Locate the game's ImportedSongs folder (engine name 'Pagoda')."""
    return platform.autodetect_imported_songs()


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


def get_theme() -> str:
    settings = load_settings()
    return settings.get("theme", "dark")


def set_theme(name: str) -> None:
    settings = load_settings()
    settings["theme"] = name
    save_settings(settings)


def get_steam_app_id() -> str:
    settings = load_settings()
    return settings.get("steam_app_id", STEAM_APP_ID)


def set_steam_app_id(app_id: str) -> None:
    settings = load_settings()
    settings["steam_app_id"] = app_id
    save_settings(settings)


def get_game_exe_path() -> Path | None:
    settings = load_settings()
    if "game_exe_path" in settings:
        path = Path(settings["game_exe_path"])
        if path.exists():
            return path
    return None


def set_game_exe_path(path: Path) -> None:
    settings = load_settings()
    settings["game_exe_path"] = str(path)
    save_settings(settings)
