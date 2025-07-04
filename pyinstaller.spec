# code: language=python
# main.spec
# This file tells PyInstaller how to bundle your application
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.building.api import EXE,PYZ
from PyInstaller.building.build_main import Analysis
import sys
import os

block_cipher = None

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
        ('./app/web_static', 'app/web_static'),
        ('./app/web_templates', 'app/web_templates')
    ],
    hiddenimports=[
        'readchar',
        'numpy',
        'numpy.core.multiarray'
    ],  # Include any imports that PyInstaller might miss
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
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