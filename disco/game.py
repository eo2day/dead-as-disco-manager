import os
import shutil
import subprocess
import time
from pathlib import Path

from disco import config, platform


def launch_game_url() -> str:
    return f"steam://rungameid/{config.get_steam_app_id()}"


def supports_direct_game_exe() -> bool:
    return platform.WINDOWS


def game_exe_label() -> str:
    return "Game executable (Pagoda.exe):" if supports_direct_game_exe() else "Game launch target:"


def game_exe_dialog_title() -> str:
    return "Select Pagoda.exe" if supports_direct_game_exe() else "Select game launch target"


def game_exe_filter() -> str:
    return "Executable (*.exe)" if platform.WINDOWS else "All files (*)"


def game_exe_help_text() -> str:
    if supports_direct_game_exe():
        return "Select or auto-detect Pagoda.exe."
    return "This platform restarts through Steam App ID, so a direct game executable is optional."


def find_game_exe() -> Path | None:
    """Locate a direct game executable when the current platform uses one."""
    if not platform.WINDOWS:
        return None
    game_dir = platform.find_game_install_dir()
    if game_dir:
        for exe in game_dir.rglob(platform.WINDOWS_GAME_EXE):
            return exe
    return None


def is_game_running() -> bool:
    """True if the Dead as Disco process appears to be running."""
    try:
        if platform.WINDOWS:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq PagodaSteam-Win64-Shipping.exe",
                 "/FO", "CSV", "/NH"],
                capture_output=True, text=True)
            return "PagodaSteam-Win64-Shipping.exe" in out.stdout
        out = subprocess.run(
            ["pgrep", "-f", "PagodaSteam-Win64-Shipping\\.exe|Pagoda\\.exe"],
            capture_output=True, text=True
        )
        return out.returncode == 0
    except Exception:
        return False


def _terminate_game_processes() -> None:
    if platform.WINDOWS:
        for name in platform.GAME_PROCESS_NAMES:
            subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
        return
    subprocess.run(
        ["pkill", "-f", "PagodaSteam-Win64-Shipping\\.exe|Pagoda\\.exe"],
        capture_output=True
    )


def _launch_via_steam() -> None:
    url = launch_game_url()
    steam_bin = shutil.which("steam") or shutil.which("steam-native")
    if steam_bin:
        subprocess.Popen([steam_bin, url])
        return
    opener = shutil.which("xdg-open")
    if opener:
        subprocess.Popen([opener, url])
        return
    raise RuntimeError("Couldn't find Steam or xdg-open to relaunch the game.")


def restart_game(exe: Path | None = None) -> None:
    """Kill the game if needed and relaunch it using the current platform's flow."""
    _terminate_game_processes()
    time.sleep(1.0)
    if platform.WINDOWS:
        if not exe:
            raise RuntimeError("No Pagoda.exe path is configured.")
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        return
    _launch_via_steam()


def open_in_file_manager(path: Path) -> None:
    path = Path(path)
    target = path if path.is_dir() else path.parent
    if platform.WINDOWS:
        os.startfile(str(target))
        return

    for opener in ("xdg-open", "open"):
        binary = shutil.which(opener)
        if binary:
            subprocess.Popen([binary, str(target)])
            return
    raise RuntimeError("Couldn't find a file manager opener for this platform.")
