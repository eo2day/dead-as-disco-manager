import json
import os
import subprocess
from pathlib import Path

if os.name == "nt":
    CONFIG_DIR = Path(os.environ["APPDATA"]) / "DiscoManager"
else:
    CONFIG_DIR = Path.home() / ".config" / "disco-manager"

CONFIG_FILE = CONFIG_DIR / "settings.json"

STEAM_APP_ID = "3404260"


def launch_game_url() -> str:
    return f"steam://rungameid/{STEAM_APP_ID}"


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


def find_game_exe() -> Path | None:
    """Locate Pagoda.exe in common Steam library locations (Windows)."""
    if os.name != "nt":
        return None
    roots = []
    for drive in "CDEFGH":
        roots.append(Path(f"{drive}:/SteamLibrary/steamapps/common"))
        roots.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common"))
    for root in roots:
        if not root.exists():
            continue
        for name in ("Dead as Disco", "Dead as Disco Demo"):
            game_dir = root / name
            if game_dir.exists():
                for exe in game_dir.rglob("Pagoda.exe"):
                    return exe
    return None


def is_game_running() -> bool:
    """True if the Dead as Disco process appears to be running (Windows)."""
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq PagodaSteam-Win64-Shipping.exe"],
            capture_output=True, text=True)
        return "PagodaSteam-Win64-Shipping.exe" in out.stdout
    except Exception:
        return False


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