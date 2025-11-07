# Custom hook for pywebview to fix broken upstream hook
# The upstream hook has a bug where it tries to use 'datas' variable before defining it

from PyInstaller.utils.hooks import collect_data_files

# Properly initialize datas variable before using it
datas = []
datas += collect_data_files("webview", subdir="js")

# Collect all webview data files
hiddenimports = [
    "webview",
    "webview.platforms",
]
