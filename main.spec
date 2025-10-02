# -*- mode: python ; coding: utf-8 -*-

# 添加数据文件，确保配置文件和记录文件夹被包含
import os

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('records', 'records')
    ],
    hiddenimports=[
        'collections.abc',
        'configparser',
        'json',
        'os',
        'tkinter',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.simpledialog',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'logging',
        'time',
        'appdirs'
    ],
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
    name='main',
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
