# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

hiddenimports = [
    "openpyxl", "openpyxl.cell._writer", "docx", "pypdf", "olefile",
    "deep_translator", "dotenv", "openai", "httpx", "httpcore",
    "PySide6.QtCore", "PySide6.QtWidgets", "PySide6.QtGui",
]

# Collect PySide6 data and binaries, then filter
datas = collect_data_files("PySide6", include_py_files=True)
binaries = collect_dynamic_libs("PySide6")

# Include QR code image
datas += [("src/file_toolbox/wechat_qr.jpg", "file_toolbox")]

BAD = [
    "api-ms-win",
    "qt6qml", "qt6quick", "qt63d", "qt6charts",
    "qt6datavisualization", "qt6designer", "qt6graph",
    "qt6help", "qt6httpserver", "qt6location", "qt6lottie",
    "qt6multimedia", "qt6networkauth", "qt6nfc",
    "qt6pdf", "qt6printsupport", "qt6remoteobjects",
    "qt6scxml", "qt6sensors", "qt6serial", "qt6spatialaudio",
    "qt6sql", "qt6statemachine", "qt6svg", "qt6test",
    "qt6texttospeech", "qt6uitools", "qt6web", "qt6websockets",
    "qt6bluetooth", "qt6positioning",
    "qml" + chr(92),  # qml\ 
    ".qmlc", "qsb.exe",
    chr(92) + "concurrent" + chr(92),
    chr(92) + "generic" + chr(92),
    chr(92) + "multimedia" + chr(92),
    chr(92) + "network" + chr(92),
    chr(92) + "position" + chr(92),
    chr(92) + "qmltooling" + chr(92),
    chr(92) + "renderplugins" + chr(92),
    chr(92) + "scxmldata" + chr(92),
    chr(92) + "sensorgestures" + chr(92),
    chr(92) + "sqldrivers" + chr(92),
    chr(92) + "texttospeech" + chr(92),
    chr(92) + "tls" + chr(92),
    chr(92) + "webview" + chr(92),
    chr(92) + "gamepad" + chr(92),
]

def keep(path):
    name = path.lower()
    for pattern in BAD:
        if pattern in name:
            return False
    return True

datas = [(s, d) for (s, d) in datas if keep(s)]
binaries = [(s, d) for (s, d) in binaries if keep(s)]

a = Analysis(
    ["src/file_toolbox/main.py"],
    pathex=["src"],
    binaries=binaries, datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="FileTranslator", debug=False, icon="app.ico",
    bootloader_ignore_signals=False, strip=False,
    upx=True, console=False,
    disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
_exclusions = [
    "api-ms-win",
    "ucrtbase.dll",
    
    "qt6qml", "qt6quick", "qt63d", "qt6charts",
    "qt6datavisualization", "qt6designer", "qt6graph",
    "qt6help", "qt6httpserver", "qt6location", "qt6lottie",
    "qt6multimedia", "qt6networkauth", "qt6nfc",
    "qt6pdf", "qt6printsupport", "qt6remoteobjects",
    "qt6scxml", "qt6sensors", "qt6serial", "qt6spatialaudio",
    "qt6sql", "qt6statemachine", "qt6svg", "qt6test",
    "qt6texttospeech", "qt6uitools", "qt6web", "qt6websockets",
    "qt6bluetooth", "qt6positioning",
    "qml" + chr(92), ".qmlc", "qsb.exe",
    chr(92) + "concurrent" + chr(92),
    chr(92) + "generic" + chr(92),
    chr(92) + "multimedia" + chr(92),
    chr(92) + "network" + chr(92),
    chr(92) + "position" + chr(92),
    chr(92) + "qmltooling" + chr(92),
    chr(92) + "renderplugins" + chr(92),
    chr(92) + "scxmldata" + chr(92),
    chr(92) + "sensorgestures" + chr(92),
    chr(92) + "sqldrivers" + chr(92),
    chr(92) + "texttospeech" + chr(92),
    chr(92) + "tls" + chr(92),
    chr(92) + "webview" + chr(92),
    chr(92) + "gamepad" + chr(92),
]

def _keep(name):
    low = name.lower()
    for pat in _exclusions:
        if pat in low:
            return False
    return True

_filtered_bins = [(d, s, t) for (d, s, t) in a.binaries if _keep(d.lower()) and _keep(s.lower())]
_filtered_datas = [(s, d, t) for (s, d, t) in a.datas if _keep(s.lower()) and _keep(d.lower())]
coll = COLLECT(
    exe, _filtered_bins, _filtered_datas,
    strip=False, upx=True, upx_exclude=[], name="FileTranslator",
)
