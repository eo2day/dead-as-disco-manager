# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for pkg in ("PySide6",):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas + [("icon.png", ".")],
    hiddenimports=hiddenimports + [
        "disco.config", "disco.importer", "disco.playlists",
        "disco.bjpl", "disco.browser",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="DiscoManager",
    console=False,          # no terminal window
    disable_windowed_traceback=False,
    icon="icon.ico",
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    name="DiscoManager",
)