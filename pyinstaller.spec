# code: language=python
# main.spec
# This file tells PyInstaller how to bundle your application
from PyInstaller.utils.hooks import copy_metadata, collect_data_files
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis, COLLECT, BUNDLE
import sys
import os
import site


site_packages_path = None
block_cipher = None

for site_path in site.getsitepackages():
  if 'site-packages' in site_path:
    site_packages_path = site_path
    break

if site_packages_path is None:
  raise RuntimeError("The site-packages directory could not be found. Please setup the python envrionment correctly and try again...")

a = Analysis(
    ['cibmangotree_gui.py'],  # GUI entry point
    pathex=['.'],    # Ensure all paths are correctly included
    binaries=[],
    datas=[
        # version file, if defined
        *(
            [('./VERSION', '.')]
            if os.path.exists('VERSION') else []
        ),

        # inquirer depends on readchar as a hidden dependency that requires package metadata
        *copy_metadata('readchar'),

        # static assets for web servers
        (os.path.join(site_packages_path, 'shiny/www'), 'shiny/www'),
        (os.path.join(site_packages_path, 'shinywidgets/static'), 'shinywidgets/static'),
        ('./app/web_static', 'app/web_static'),
        ('./app/web_templates', 'app/web_templates'),

        # NiceGUI static files (required for GUI mode)
        (os.path.join(site_packages_path, 'nicegui'), 'nicegui')
        # Note: pywebview data files are handled by custom hook in ./hooks/
    ],
    hiddenimports=[
        'readchar',
        'numpy',
        'numpy.core.multiarray',
        'shiny',
        'shiny.ui',
        'shiny.server',
        'htmltools',
        'starlette',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'asyncio',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'polars',
        'plotly',
        'linkify_it',
        'markdown_it',
        'mdit_py_plugins',
        'mdurl',
        'uc_micro',
        'pythonjsonlogger',
        'pythonjsonlogger.jsonlogger',
        # NiceGUI and pywebview (required for GUI mode)
        'nicegui',
        'nicegui.elements',
        'nicegui.events',
        'nicegui.ui',
        'fastapi',
        'sse_starlette',
        'pywebview',
        'pywebview.platforms',
    ],  # Include any imports that PyInstaller might miss
    hookspath=['./hooks'],  # Use custom hooks to override broken pywebview hook
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    # For onedir build: EXE only contains scripts
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,  # This makes it onedir, not onefile
        name='CIBMangoTree',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,
        upx=True,
        console=False,  # No console window for GUI app
        entitlements_file="./mango.entitlements",
        codesign_identity=os.getenv('APPLE_APP_CERT_ID'),
    )

    # Collect all files for the bundle (onedir structure)
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=True,
        upx=True,
        name='CIBMangoTree'
    )

    # Create macOS app bundle from the collected files
    app = BUNDLE(
        coll,
        name='CIBMangoTree.app',
        icon=None,  # Add icon path when available (e.g., 'icon.icns')
        bundle_identifier='org.civictechdc.cibmangotree',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.9.0',
            'CFBundleName': 'CIB Mango Tree',  # Display name (can have spaces)
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='CIBMangoTree',  # The name of the executable
        debug=False,
        strip=False,
        upx=True,
        console=False,  # No console window for GUI app
        icon=None,  # Add icon path when available (e.g., 'icon.ico' for Windows)
    )
