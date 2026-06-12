"""Read and edit Dead as Disco (.bjpl) playlist files.

Each song = an object-path string + a trailer record whose 4-byte value is the
song's uniqueId (from the song's Meta.json).
"""
import re
import struct
import os
from pathlib import Path

_DEFAULT_PREFIX = ("/Engine/Transient.GameEngine_2147482574:"
                   "GI_PagodaGameInstance_C_2147482511."
                   "PagodaSongCatalogSubsystem_2147482231.")


def _rstr(raw, p):
    n = struct.unpack_from("<i", raw, p)[0]; p += 4
    if n == 0:
        return "", p
    if n > 0:
        return raw[p:p + n - 1].decode("latin-1"), p + n
    return raw[p:p + (-n) * 2 - 2].decode("utf-16-le"), p + (-n) * 2


def _wstr(s):
    try:
        b = s.encode("latin-1")
        return struct.pack("<i", len(b) + 1) + b + b"\x00"
    except UnicodeEncodeError:
        b = s.encode("utf-16-le")
        return struct.pack("<i", -(len(s) + 1)) + b + b"\x00\x00"


def parse(raw: bytes) -> dict:
    sp = raw.find(b"StrProperty\x00")
    e = sp + len(b"StrProperty\x00")
    name_valsize_pos = e + 4
    name, name_value_end = _rstr(raw, e + 9)

    op = raw.find(b"ObjectProperty\x00")
    a = op + len(b"ObjectProperty\x00") + 4
    songs_size_pos = a
    a += 4 + 1
    count = struct.unpack_from("<i", raw, a)[0]; a += 4
    paths = []
    for _ in range(count):
        s, a = _rstr(raw, a); paths.append(s)
    none_pos = raw.find(b"\x05\x00\x00\x00None\x00", a)
    tpos = none_pos + 9
    tcount = struct.unpack_from("<i", raw, tpos + 4)[0]
    trailer = []; z = tpos + 8
    for _ in range(tcount):
        trailer.append((raw[z:z + 4], struct.unpack_from("<i", raw, z + 4)[0])); z += 8

    return {"raw": raw, "name": name, "paths": paths, "trailer": trailer,
            "name_valsize_pos": name_valsize_pos, "name_value_end": name_value_end,
            "songs_size_pos": songs_size_pos}


def build(state: dict, name=None, songs=None) -> bytes:
    """songs: list of (object_path:str, unique_id:int)."""
    raw = state["raw"]
    name = state["name"] if name is None else name
    if songs is None:
        songs = list(zip(state["paths"],
                         [struct.unpack("<I", h)[0] for h, _ in state["trailer"]]))

    out = bytearray(raw[:state["name_valsize_pos"]])
    namebytes = _wstr(name)
    out += struct.pack("<i", len(namebytes)) + b"\x00" + namebytes
    out += raw[state["name_value_end"]:state["songs_size_pos"]]

    entries = b"".join(_wstr(p) for p, _ in songs)
    out += struct.pack("<i", 4 + len(entries)) + b"\x00" + struct.pack("<i", len(songs))
    out += entries
    out += struct.pack("<i", 5) + b"None\x00"
    out += struct.pack("<i", 0) + struct.pack("<i", len(songs))
    for i, (_, uid) in enumerate(songs):
        out += struct.pack("<I", uid & 0xffffffff) + struct.pack("<i", i)
    return bytes(out)


def catalog_prefix(existing_playlists) -> str:
    for pl in existing_playlists:
        try:
            for pth in parse(Path(pl).read_bytes())["paths"]:
                m = re.match(r"(.*PagodaSongCatalogSubsystem_\d+\.)", pth)
                if m:
                    return m.group(1)
        except Exception:
            continue
    return _DEFAULT_PREFIX


def song_ref(prefix: str, artist: str, title: str) -> str:
    return f"{prefix}{artist} - {title}"


def is_importable_ref(path: str) -> bool:
    """True for imported-song references the manager can safely write."""
    return "SongCatalogSubsystem_" in path


def create_from_template(template_path, name, songs, out_dir):
    out_dir = Path(out_dir)
    state = parse(Path(template_path).read_bytes())
    data = build(state, name=name, songs=songs)
    # never overwrite an existing file
    for _ in range(100):
        new_path = out_dir / f"Playlist_{os.urandom(16).hex().upper()}.bjpl"
        if not new_path.exists():
            break
    else:
        raise RuntimeError("Couldn't find a free filename.")
    new_path.write_bytes(data)
    return new_path