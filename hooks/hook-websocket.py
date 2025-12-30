# PyInstaller hook for websocket-client
# This ensures all websocket modules are properly bundled

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules of websocket
hiddenimports = collect_submodules('websocket')

# Collect any data files
datas = collect_data_files('websocket')

# Explicitly add critical submodules that might be missed
hiddenimports += [
    'websocket',
    'websocket._abnf',
    'websocket._app',
    'websocket._core',
    'websocket._cookiejar',
    'websocket._exceptions',
    'websocket._handshake',
    'websocket._http',
    'websocket._logging',
    'websocket._socket',
    'websocket._ssl_compat',
    'websocket._url',
    'websocket._utils',
]
