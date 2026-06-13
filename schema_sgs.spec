# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Le Schéma SGS.

Build locally with:
    pyinstaller schema_sgs.spec

The GitHub Actions workflow (.github/workflows/build-exe.yml) uses this
spec file to produce LeSchemaSGS.exe on Windows.
"""

import customtkinter
from pathlib import Path

block_cipher = None

# Bundle customtkinter's theme/asset files (required for it to run when frozen)
ctk_path = Path(customtkinter.__file__).parent

datas = [
    (str(ctk_path), "customtkinter"),
    ("assets", "assets"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PIL._tkinter_finder",
        "matplotlib.backends.backend_tkagg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LeSchemaSGS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
