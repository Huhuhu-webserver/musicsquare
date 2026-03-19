# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

added_files = [
    ('index.html', '.'),
    ('local.html', '.'),
    ('style.css', '.'),
    ('pikachu.gif', '.'),
    ('wss.py', '.'),
    ('docs/logo.png', 'docs'),
]

binaries = []
import pythonnet
pythonnet_path = os.path.dirname(pythonnet.__file__)
for root, dirs, files in os.walk(pythonnet_path):
    for file in files:
        if file.endswith('.dll'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(root, pythonnet_path)
            binaries.append((full_path, os.path.join('pythonnet', rel_path)))

# 收集pywin32相关文件
try:
    # 收集win32com相关文件
    win32com_binaries, win32com_datas, win32com_hiddenimports = collect_all('win32com')
    binaries.extend(win32com_binaries)
    added_files.extend(win32com_datas)
    
    # 收集pywintypes相关文件
    pywintypes_binaries, pywintypes_datas, pywintypes_hiddenimports = collect_all('pywintypes')
    binaries.extend(pywintypes_binaries)
    added_files.extend(pywintypes_datas)
    
    # 收集pythoncom相关文件
    pythoncom_binaries, pythoncom_datas, pythoncom_hiddenimports = collect_all('pythoncom')
    binaries.extend(pythoncom_binaries)
    added_files.extend(pythoncom_datas)
except ImportError:
    pass

hidden_imports = [
    'webview',
    'pythonnet',
    'clr',
    'base58',
    'requests',
    'Cryptodome',
    'Cryptodome.Cipher',
    'Cryptodome.Cipher.DES',
    'Cryptodome.Util.Padding',
] + win32com_hiddenimports + pywintypes_hiddenimports + pythoncom_hiddenimports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pkg_resources', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter'],  # 排除pkg_resources以避免PyiFrozenImporter错误
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
    name='pikachu_music-v1.1.9',
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
    icon='docs/logo.ico',
)