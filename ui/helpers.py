SORT_OPTIONS = ["Artist", "Title", "BPM", "Duration"]


def song_label(m) -> str:
    meta = []
    if m.tempo:
        meta.append(f"{m.tempo} BPM")
    if m.duration:
        s = int(round(m.duration))
        meta.append(f"{s // 60}:{s % 60:02d}")
    base = f"{m.artist} — {m.title}"
    return base + ("   ·  " + "  ·  ".join(meta) if meta else "")


def filter_sort(maps, query, sort_key, descending):
    q = (query or "").strip().lower()
    res = [m for m in maps if (q in m.artist.lower() or q in m.title.lower())] if q else list(maps)
    if sort_key == "Title":
        res.sort(key=lambda m: (m.title.lower(), m.artist.lower()), reverse=descending)
    elif sort_key in ("BPM", "Duration"):
        attr = "tempo" if sort_key == "BPM" else "duration"
        have = [m for m in res if getattr(m, attr) is not None]
        missing = [m for m in res if getattr(m, attr) is None]
        have.sort(key=lambda m: getattr(m, attr), reverse=descending)
        res = have + missing
    else:  # Artist
        res.sort(key=lambda m: (m.artist.lower(), m.title.lower()), reverse=descending)
    return res
