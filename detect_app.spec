# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['detect_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('haarcascades/haarcascade_frontalface_alt.xml', 'haarcascades/'),
        ('haarcascades/haarcascade_lefteye_2splits.xml', 'haarcascades/'),
        ('haarcascades/haarcascade_righteye_2splits.xml', 'haarcascades/'),
        ('static/assets/alarm.wav', 'static/assets/'),
        ('model/main_cnn.h5', 'model/')
    ],
    hiddenimports=[],
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
    name='detect_app',
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
)
