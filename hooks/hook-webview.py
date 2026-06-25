# PyInstaller hook for pywebview.
#
# pywebview's own hook collects the `webview` package as loose SOURCE
# (module_collection_mode='py'), which is not reliably importable in a one-file
# build -> the app fails with "No module named 'webview'" and falls back to the
# classic UI. Forcing 'pyz' puts the modules into the archive as importable
# bytecode. We also pull the Windows edgechromium (WebView2) backend + its
# clr/.NET interop and pywebview's runtime deps.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files


def _keep(name):
    # Drop backends for platforms we don't ship (their imports also error out).
    return not any(p in name for p in ('android', 'cocoa', 'gtk', 'qt'))


hiddenimports = [m for m in collect_submodules('webview') if _keep(m)]
hiddenimports += [
    'webview',
    'webview.platforms.edgechromium',
    'webview.platforms.winforms',
    'clr', 'clr_loader', 'clr_loader.netfx', 'clr_loader.util',
    'proxy_tools', 'bottle', 'typing_extensions',
]

datas = collect_data_files('webview')

# The key fix: importable bytecode in the PYZ, not loose source files.
module_collection_mode = {'webview': 'pyz'}
