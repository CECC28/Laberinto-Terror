# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/Colibecas/OneDrive/Documentos/FIME/Semestre 5/Parcial 1/Interacción Humano-Computadora/PROYEC-TITO/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['skills'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'PIL', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Laberinto_del_Terror',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Laberinto_del_Terror',
)
