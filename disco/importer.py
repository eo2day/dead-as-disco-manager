import json
import struct
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MapFolder:
    source: Path
    title: str
    artist: str
    tempo: int | None = None
    unique_id: int | None = None
    duration: float | None = None   # seconds, read from the .ogg
    offset: float | None = None     # beatOffset, from Meta.json

    @property
    def folder_name(self) -> str:
        return self.source.name


class ImportError_(Exception):
    pass


def _load_json(meta_path: Path) -> dict | None:
    raw = meta_path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            data = json.loads(raw.decode(enc))
            return data if isinstance(data, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return None


def _read_meta(meta_path: Path) -> tuple[str, str]:
    data = _load_json(meta_path)
    if data is None:
        return ("Unknown title", "Unknown artist")
    lower = {k.lower(): v for k, v in data.items()}

    def first(*keys):
        for k in keys:
            if k in lower and lower[k] not in (None, "", []):
                return lower[k]
        return None

    title = first("songname", "title", "name", "song") or "Unknown title"
    artist_val = first("performedby", "artist", "author", "mapper")
    if isinstance(artist_val, list):
        artist = ", ".join(str(a) for a in artist_val) if artist_val else "Unknown artist"
    elif artist_val:
        artist = str(artist_val)
    else:
        artist = "Unknown artist"
    return (str(title), artist)


def _read_tempo(meta_path: Path) -> int | None:
    data = _load_json(meta_path)
    if data is None:
        return None
    t = data.get("tempo")
    return int(t) if isinstance(t, (int, float)) else None


def _read_uid(meta_path: Path) -> int | None:
    data = _load_json(meta_path)
    if data is None:
        return None
    u = data.get("uniqueId")
    return int(u) if isinstance(u, (int, float)) else None


def _read_offset(meta_path: Path) -> float | None:
    data = _load_json(meta_path)
    if data is None:
        return None
    o = data.get("beatOffset")
    return float(o) if isinstance(o, (int, float)) else None


def _read_ogg_duration(ogg_path: Path) -> float | None:
    """Estimate an Ogg Vorbis file's duration without external libraries.

    Reads the sample rate from the Vorbis identification header (near the
    start) and the final granule position (sample count) from the last Ogg
    page near the end of the file.
    """
    try:
        with open(ogg_path, "rb") as f:
            head = f.read(8192)
            i = head.find(b"\x01vorbis")
            if i < 0 or i + 16 > len(head):
                return None
            sample_rate = struct.unpack_from("<I", head, i + 12)[0]
            if sample_rate <= 0:
                return None
            f.seek(0, 2)
            size = f.tell()
            tail_len = min(65536, size)
            f.seek(size - tail_len)
            tail = f.read(tail_len)
            j = tail.rfind(b"OggS")
            if j < 0 or j + 14 > len(tail):
                return None
            granule = struct.unpack_from("<q", tail, j + 6)[0]
            if granule <= 0:
                return None
            return granule / sample_rate
    except Exception:
        return None


def _safe_name(name: str) -> str:
    bad = '<>:"/\\|?*'
    cleaned = "".join("_" if c in bad else c for c in name).strip().strip(".")
    return cleaned or "Untitled map"


def _scan_folder(folder: Path) -> MapFolder | None:
    ogg = next((f for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() == ".ogg"), None)
    meta = next((f for f in folder.iterdir()
                 if f.is_file() and f.suffix.lower() == ".json"), None)
    if ogg and meta:
        title, artist = _read_meta(meta)
        return MapFolder(source=folder, title=title, artist=artist,
                         tempo=_read_tempo(meta), unique_id=_read_uid(meta),
                         duration=_read_ogg_duration(ogg), offset=_read_offset(meta))
    return None


def _find_map_folders(root: Path) -> list[MapFolder]:
    found = []
    for folder in [root, *(p for p in root.rglob("*") if p.is_dir())]:
        m = _scan_folder(folder)
        if m:
            found.append(m)
    return found


def import_zip(zip_path: Path, imported_songs: Path) -> list[str]:
    zip_path = Path(zip_path); imported_songs = Path(imported_songs)
    if not zipfile.is_zipfile(zip_path):
        raise ImportError_(f"Not a valid zip file: {zip_path.name}")
    imported_songs.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                target = (tmp_path / member).resolve()
                if not str(target).startswith(str(tmp_path.resolve())):
                    raise ImportError_(f"Unsafe path in zip: {member}")
            zf.extractall(tmp_path)
        maps = _find_map_folders(tmp_path)
        if not maps:
            raise ImportError_("No maps found in this zip (expected an .ogg + .json pair).")
        installed = []
        for m in maps:
            name = _safe_name(f"{m.artist} - {m.title}") if m.source == tmp_path \
                else _safe_name(m.folder_name)
            dest = imported_songs / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(m.source, dest)
            installed.append(name)
    return installed


def list_installed(imported_songs: Path) -> list[MapFolder]:
    imported_songs = Path(imported_songs)
    if not imported_songs.exists():
        return []
    result = []
    for folder in sorted(p for p in imported_songs.iterdir() if p.is_dir()):
        m = _scan_folder(folder)
        if m:
            result.append(m)
    return result