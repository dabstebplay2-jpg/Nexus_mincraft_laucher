from pathlib import Path
from PySide6.QtGui import QIcon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets"
ICON_DIR = ASSET_DIR / "icons"


def icon(name: str) -> QIcon:
    """Load launcher icon by name.

    Priority:
    1. assets/icons/<name>.png
    2. assets/icons/<name>.ico
    3. assets/icons/<name>.svg

    This makes project avatar replacement easy:
    just replace assets/icons/nexus.png and assets/nexus.ico.
    """
    for ext in ("png", "ico", "svg"):
        path = ICON_DIR / f"{name}.{ext}"
        if path.exists():
            return QIcon(str(path))

    fallback = ASSET_DIR / f"{name}.ico"
    if fallback.exists():
        return QIcon(str(fallback))

    return QIcon()
