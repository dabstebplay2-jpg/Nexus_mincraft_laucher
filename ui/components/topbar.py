import logging
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QRect, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.icon_utils import icon

logger = logging.getLogger(__name__)


class ProfileAvatar(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(30, 30)
        self.skin_path = None

    def set_skin(self, skin_path, _username):
        self.skin_path = skin_path
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#304236"))
        painter.drawRoundedRect(self.rect(), 8, 8)
        if self.skin_path and Path(self.skin_path).is_file():
            pixmap = QPixmap(str(self.skin_path))
            if not pixmap.isNull() and pixmap.width() >= 64 and pixmap.height() >= 32:
                scale = max(1, pixmap.width() // 64)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
                painter.drawPixmap(QRect(3, 3, 24, 24), pixmap,
                                   QRect(8 * scale, 8 * scale, 8 * scale, 8 * scale))
                return
        painter.drawPixmap(5, 5, icon("accounts").pixmap(QSize(20, 20)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class Topbar(QWidget):
    """Global actions that should remain available on every page."""

    downloads_clicked = Signal()
    account_clicked = Signal()
    theme_clicked = Signal()

    THEME_LABELS = {
        "dark": "Тёмная", "amoled": "AMOLED", "forest": "Лес",
        "ocean": "Океан", "purple": "Эндер", "sunset": "Закат",
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("Topbar")
        self.setFixedHeight(68)
        self.current_theme = "dark"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(10)

        self.title_label = QLabel("Главная")
        self.title_label.setObjectName("TopbarTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.downloads_button = QPushButton("Загрузки")
        self.downloads_button.setObjectName("TopbarDownloadsButton")
        self.downloads_button.setIcon(icon("downloads"))
        self.downloads_button.setIconSize(QSize(17, 17))
        self.downloads_button.setCursor(Qt.PointingHandCursor)
        self.downloads_button.clicked.connect(self.downloads_clicked.emit)
        layout.addWidget(self.downloads_button)

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("TopbarThemeButton")
        self.theme_button.setIcon(icon("settings"))
        self.theme_button.setIconSize(QSize(17, 17))
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.clicked.connect(self.theme_clicked.emit)
        self.theme_button.setFixedSize(36, 36)
        layout.addWidget(self.theme_button)

        self.account_button = QPushButton("NexusPlayer")
        self.account_button.setObjectName("TopbarAccountButton")
        self.account_button.setCursor(Qt.PointingHandCursor)
        self.account_button.clicked.connect(self.account_clicked.emit)
        self.avatar = ProfileAvatar()
        self.avatar.setObjectName("TopbarAvatar")
        self.avatar.setCursor(Qt.PointingHandCursor)
        self.avatar.clicked.connect(self.account_clicked.emit)
        layout.addWidget(self.avatar)
        layout.addWidget(self.account_button)
        self.set_theme("dark")
        self.update_profile()

    def set_page(self, title, subtitle=""):
        self.title_label.setText(title)
        self.title_label.setToolTip(subtitle)

    def set_compact(self, compact: bool):
        self.account_button.setVisible(not compact)

    def set_theme(self, theme: str | None):
        self.current_theme = str(theme or "dark").lower()
        label = self.THEME_LABELS.get(self.current_theme, "Тёмная")
        self.theme_button.setToolTip(f"Тема: {label}. Переключить")

    def set_download_count(self, count: int):
        count = max(0, int(count))
        self.downloads_button.setText(f"Загрузки · {count}" if count else "Загрузки")

    def update_profile(self):
        from auth.account_manager import AccountManager
        from core.skin_manager import SkinManager

        account = None
        skin_path = None
        try:
            account = AccountManager().get_active_account()
            if account:
                skin = SkinManager().get_account_skin(account)
                if skin:
                    skin_path = skin.get("path")
        except (OSError, ValueError, RuntimeError):
            logger.warning("Could not read account profile for topbar", exc_info=True)
        username = (account or {}).get("display_name") or (account or {}).get("username") or "NexusPlayer"
        self.account_button.setText(username)
        self.account_button.setToolTip("Аккаунты и скины")
        self.avatar.set_skin(skin_path, username)
