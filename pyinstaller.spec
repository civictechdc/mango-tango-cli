# code: language=python
# main.spec
# This file tells PyInstaller how to bundle your application
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.building.api import EXE,PYZ
from PyInstaller.building.build_main import Analysis
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
    ['mangotango.py'],  # Entry point
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
        ('./app/web_templates', 'app/web_templates')
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
    ],  # Include any imports that PyInstaller might miss
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='mangotango',  # The name of the executable
        debug=False,
        strip=True,
        upx=True,  # You can set this to False if you don’t want UPX compression
        console=True,  # Set to False if you don't want a console window
        entitlements_file="./mango.entitlements",
        codesign_identity=os.getenv('APPLE_APP_CERT_ID'),
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='mangotango',  # The name of the executable
        debug=False,
        strip=False,
        upx=True,  # You can set this to False if you don’t want UPX compression
        console=True  # Set to False if you don't want a console window
    )
