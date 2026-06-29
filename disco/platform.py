import os
from pathlib import Path


WINDOWS = os.name == "nt"
GAME_DIR_NAMES = ("Dead as Disco", "Dead as Disco Demo")
WINDOWS_GAME_EXE = "Pagoda.exe"
GAME_PROCESS_NAMES = ("PagodaSteam-Win64-Shipping.exe", "Pagoda.exe")


def config_dir() -> Path:
    if WINDOWS:
        return Path(os.environ["APPDATA"]) / "DiscoManager"
    return Path.home() / ".config" / "disco-manager"


def autodetect_imported_songs() -> Path | None:
    """Locate the game's ImportedSongs folder on the current platform."""
    candidates: list[Path] = []
    if WINDOWS:
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidates.append(Path(local) / "Pagoda" / "Saved" / "ImportedSongs")
    else:
        home = Path.home()
        for steam in (home / ".steam/steam", home / ".local/share/Steam"):
            compat = steam / "steamapps/compatdata"
            if not compat.exists():
                continue
            for appdir in compat.glob(
                "*/pfx/drive_c/users/*/AppData/Local/Pagoda/Saved/ImportedSongs"
            ):
                candidates.append(appdir)

    for path in candidates:
        if path.exists() or path.parent.exists():
            return path
    return None


def steam_library_roots() -> list[Path]:
    roots: list[Path] = []
    if WINDOWS:
        for drive in "CDEFGH":
            roots.append(Path(f"{drive}:/SteamLibrary/steamapps/common"))
            roots.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common"))
        return roots

    home = Path.home()
    for root in (
        home / ".local/share/Steam/steamapps/common",
        home / ".steam/steam/steamapps/common",
    ):
        roots.append(root)

    media_root = Path("/run/media") / home.name
    if media_root.exists():
        for child in media_root.iterdir():
            roots.append(child / "SteamLibrary/steamapps/common")

    return roots


def find_game_install_dir() -> Path | None:
    for root in steam_library_roots():
        if not root.exists():
            continue
        for name in GAME_DIR_NAMES:
            game_dir = root / name
            if game_dir.exists():
                return game_dir
    return None


def imported_songs_site_path(path: Path) -> str:
    """Convert a host ImportedSongs path into the format DiscoMaps expects."""
    path = Path(path).expanduser().resolve()
    raw = path.as_posix()

    marker = "/drive_c/"
    if marker in raw:
        suffix = raw.split(marker, 1)[1]
        return f"C:/{suffix}"

    if WINDOWS:
        return str(path).replace("\\", "/")

    return raw
