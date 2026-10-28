# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import glob

# Include sign.ps1 only if it exists (optional)
datas = [('logo.ico', '.')]
if os.path.exists('sign.ps1'):
    datas.append(('sign.ps1', '.'))

# Tcl/Tk data directories for tkinter. PyInstaller normally auto-collects these,
# but its discovery probe fails on some systems (and inside restricted shells),
# which silently produces an EXE that dies with "Can't find a usable init.tcl".
# Adding them explicitly makes the build self-sufficient.
_tcl_root = os.path.join(sys.base_prefix, 'tcl')
for _pattern, _dest in (('tcl8.*', '_tcl_data'), ('tk8.*', '_tk_data')):
    for _dir in sorted(glob.glob(os.path.join(_tcl_root, _pattern))):
        if os.path.isdir(_dir):
            datas.append((_dir, _dest))
            break

a = Analysis(
    ['k4li_protect.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinter.colorchooser',
        'tkinter.font',
        'tkinter.scrolledtext',
        '_tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'cv2', 'PyQt5', 'wx',
    ],
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
    name='K4LI_EXE_PROTECT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir='.',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)
