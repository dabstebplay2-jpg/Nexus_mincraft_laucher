from __future__ import annotations

import os
import sys
from pathlib import Path

# PyInstaller safety net:
# if local packages are also bundled as data, make sys._MEIPASS importable.
bundle_dir = getattr(sys, "_MEIPASS", None)
if bundle_dir and bundle_dir not in sys.path:
    sys.path.insert(0, bundle_dir)

# Windows does not search sibling package folders for dependent DLLs. Keep the
# directory handles alive for the entire process before importing QtWidgets.
_dll_directories = []
if bundle_dir and os.name == "nt" and hasattr(os, "add_dll_directory"):
    for package in ("shiboken6", "PySide6"):
        directory = Path(bundle_dir) / package
        if directory.is_dir():
            _dll_directories.append(os.add_dll_directory(str(directory)))

if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
    if app_dir and app_dir not in sys.path:
        sys.path.insert(0, app_dir)
