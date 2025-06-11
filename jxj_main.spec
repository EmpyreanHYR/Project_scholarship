# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['jxj_main.py'],
    pathex=[],
    binaries=[],
    datas=[('template.xlsx', '.'), ('logo.ico', '.')],
    hiddenimports=['pandas', 'json', 'sys', 'shutil', 'PIL', 'openpyxl', 'openpyxl.cell._writer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='jxj_main',
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
    icon=['logo.ico'],
)
