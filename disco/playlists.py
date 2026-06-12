import re
import struct
from dataclasses import dataclass
from pathlib import Path

_SONG_RE = re.compile(r"SongCatalogSubsystem_\d+\.(.*)")


@dataclass
class Playlist:
    path: Path
    name: str
    songs: list[str]
    refs: list[str]


def _rstr(raw, p):
    n = struct.unpack_from("<i", raw, p)[0]; p += 4
    if n == 0:
        return "", p
    if n > 0:
        return raw[p:p + n - 1].decode("latin-1"), p + n
    return raw[p:p + (-n) * 2 - 2].decode("utf-16-le"), p + (-n) * 2


def read_playlist(path: Path) -> Playlist:
    path = Path(path)
    raw = path.read_bytes()
    sp = raw.find(b"StrProperty\x00")
    e = sp + len(b"StrProperty\x00")
    name, _ = _rstr(raw, e + 9)

    op = raw.find(b"ObjectProperty\x00")
    a = op + len(b"ObjectProperty\x00") + 4 + 4 + 1
    count = struct.unpack_from("<i", raw, a)[0]; a += 4
    refs = []
    for _ in range(count):
        s, a = _rstr(raw, a); refs.append(s)
    songs = []
    for r in refs:
        m = _SONG_RE.search(r)
        songs.append(m.group(1) if m else r)
    return Playlist(path=path, name=name or path.stem, songs=songs, refs=refs)


def saved_root(imported_songs: Path) -> Path | None:
    p = Path(imported_songs)
    if p.name.lower() == "importedsongs":
        return p.parent
    return p.parent if p.parent.exists() else None


def find_playlists(imported_songs: Path) -> list[Playlist]:
    root = saved_root(imported_songs)
    if not root or not root.exists():
        return []
    out = []
    for f in sorted(root.rglob("*.bjpl")):
        try:
            out.append(read_playlist(f))
        except Exception:
            continue
    return out