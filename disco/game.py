import os
import subprocess
import time
from pathlib import Path

from disco import config


def launch_game_url() -> str:
    return f"steam://rungameid/{config.get_steam_app_id()}"


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
            ["tasklist", "/FI", "IMAGENAME eq PagodaSteam-Win64-Shipping.exe",
             "/FO", "CSV", "/NH"],
            capture_output=True, text=True)
        return "PagodaSteam-Win64-Shipping.exe" in out.stdout
    except Exception:
        return False


def restart_game(exe: Path) -> None:
    """Kill both game processes and relaunch from the given Pagoda.exe path."""
    if os.name == "nt":
        for name in ("PagodaSteam-Win64-Shipping.exe", "Pagoda.exe"):
            subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
    time.sleep(1.0)
    subprocess.Popen([str(exe)], cwd=str(exe.parent))
