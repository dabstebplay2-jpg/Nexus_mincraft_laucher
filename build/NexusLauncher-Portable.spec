# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_root = Path.cwd().resolve()

datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "README.md"), "."),
]

binaries = []

LOCAL_PACKAGES = ["app", "auth", "core", "mods", "storage", "ui", "tools"]

def collect_local_modules(package_name: str):
    package_dir = project_root / package_name
    modules = []

    if not package_dir.exists():
        return modules

    for path in package_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        rel = path.relative_to(project_root).with_suffix("")
        parts = list(rel.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]

        if parts:
            modules.append(".".join(parts))

    return modules

hiddenimports = [
    "requests",
    "urllib3",
    "certifi",
    "charset_normalizer",
    "idna",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
]

for local_package in LOCAL_PACKAGES:
    package_dir = project_root / local_package
    if package_dir.exists():
        datas.append((str(package_dir), local_package))
    hiddenimports += collect_local_modules(local_package)

for package in ["minecraft_launcher_lib", "keyring", "pypresence"]:
    collected = collect_all(package)
    datas += collected[0]
    binaries += collected[1]
    hiddenimports += collected[2]

qt_heavy_excludes = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtHelp",
    "PySide6.QtHttpServer",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickTest",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.scripts",
    "tkinter",
    "unittest",
    "pytest",
]

runtime_hook = project_root / "tools" / "pyi_runtime_hook.py"

if not runtime_hook.exists():
    raise FileNotFoundError(f"PyInstaller runtime hook missing: {runtime_hook}")

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(runtime_hook)],
    excludes=qt_heavy_excludes,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NexusLauncher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "nexus.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="NexusLauncher",
)
