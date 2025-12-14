# -*- mode: python ; coding: utf-8 -*-
# Simplified PyInstaller spec for MyRacingData Telemetry

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all data for problematic packages
datas = []
binaries = []
hiddenimports = []

# Collect pystray
tmp_ret = collect_all('pystray')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect PIL
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Add more hidden imports
hiddenimports += [
    'websocket',
    'websocket._abnf',
    'websocket._app',
    'websocket._core',
    'websocket._exceptions',
    'websocket._handshake',
    'websocket._http',
    'websocket._logging',
    'websocket._socket',
    'websocket._ssl_compat',
    'websocket._url',
    'websocket._utils',
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyRacingData-Telemetry',
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
    icon='build/icon.ico' if os.path.exists('build/icon.ico') else None,
)
