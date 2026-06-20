from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)

try:
    from ui.icon_utils import icon
except Exception:
    icon = None


def get_icon(name):
    if not icon:
        return None
    try:
        return icon(name)
    except Exception:
        return None


class SidebarButton(QPushButton):
    def __init__(self, icon_name, text, index):
        super().__init__(text)
        self.index = index
        self.icon_name = icon_name
        self.setObjectName("SidebarNavButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setCheckable(True)
        self.setProperty("active", False)
        self.apply_icon()

    def apply_icon(self):
        qicon = get_icon(self.icon_name)
        if qicon:
            self.setIcon(qicon)
            self.setIconSize(QSize(18, 18))


class ClickableProfileCard(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class Sidebar(QWidget):
    page_changed = Signal(int)
    profile_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self.compact = False
        self._nav_labels = []
        self._logo_text_widgets = []
        self._profile_text_widgets = []
        self._section_titles = []

        self.buttons = []
        self.disabled_pages = set()

        self.root_layout = QVBoxLayout(self)
        root = self.root_layout
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        root.addWidget(self.create_logo())
        root.addSpacing(4)

        nav_title = QLabel("ОСНОВНОЕ")
        nav_title.setObjectName("SidebarSectionTitle")
        self._section_titles.append(nav_title)
        root.addWidget(nav_title)

        for icon_name, text, index in [
            ("home", "Главная", 0),
            ("instances", "Сборки", 1),
            ("mods", "Каталог", 2),
            ("library", "Библиотека", 3),
            ("downloads", "Загрузки", 4),
        ]:
            root.addWidget(self.create_nav_button(icon_name, text, index))

        root.addSpacing(8)

        system_title = QLabel("СИСТЕМА")
        system_title.setObjectName("SidebarSectionTitle")
        self._section_titles.append(system_title)
        root.addWidget(system_title)

        for icon_name, text, index in [
            ("settings", "Настройки", 6),
            ("logs", "Логи", 7),
        ]:
            root.addWidget(self.create_nav_button(icon_name, text, index))

        root.addStretch()
        root.addWidget(self.create_profile_card())

    def create_logo(self):
        card = QFrame()
        card.setObjectName("SidebarLogoCard")
        card.setMinimumHeight(74)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        mark = QLabel("×")
        mark.setObjectName("NexusMark")
        mark.setAlignment(Qt.AlignCenter)
        mark.setFixedSize(48, 48)
        self.logo_mark = mark

        self.apply_logo_icon()

        text = QVBoxLayout()
        text.setSpacing(0)

        title = QLabel("NEXUS")
        title.setObjectName("NexusLogoTitle")
        title.setMinimumWidth(100)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        subtitle = QLabel("Launcher")
        subtitle.setObjectName("NexusLogoSubtitle")
        subtitle.setMinimumWidth(100)
        subtitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._logo_text_widgets.extend([title, subtitle])

        text.addWidget(title)
        text.addWidget(subtitle)

        layout.addWidget(mark)
        layout.addLayout(text, 1)
        return card

    def apply_logo_icon(self):
        if not hasattr(self, "logo_mark") or self.logo_mark is None:
            return

        qicon = get_icon("nexus")
        if qicon:
            self.logo_mark.setPixmap(qicon.pixmap(QSize(48, 48)))

    def create_nav_button(self, icon_name, text, index):
        button = SidebarButton(icon_name, text, index)
        button.full_text = text
        button.clicked.connect(lambda checked=False, i=index: self.page_changed.emit(i))
        self.buttons.append(button)
        return button

    def set_compact(self, compact: bool):
        compact = bool(compact)
        if self.compact == compact:
            return

        self.compact = compact
        self.setProperty("compact", compact)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setFixedWidth(76 if compact else 220)
        self.root_layout.setContentsMargins(8 if compact else 12, 10, 8 if compact else 12, 10)
        self.root_layout.setSpacing(8)

        for button in self.buttons:
            button.setText("" if compact else getattr(button, "full_text", button.text()))
            button.setMinimumHeight(40 if compact else 44)
            button.setIconSize(QSize(20, 20) if compact else QSize(18, 18))
            button.setToolTip(getattr(button, "full_text", ""))

        for widget in self._logo_text_widgets + self._profile_text_widgets + self._section_titles:
            widget.setVisible(not compact)

    def set_active(self, index):
        for button in self.buttons:
            active = button.index == index
            button.setChecked(active)
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)

        if hasattr(self, "profile_card") and self.profile_card:
            active_profile = index == 5
            self.profile_card.setProperty("active", active_profile)
            self.profile_card.style().unpolish(self.profile_card)
            self.profile_card.style().polish(self.profile_card)

    def set_disabled_pages(self, pages):
        self.disabled_pages = set(pages or [])
        for button in self.buttons:
            disabled = button.index in self.disabled_pages
            button.setProperty("disabledPage", disabled)
            button.style().unpolish(button)
            button.style().polish(button)

    def create_profile_card(self):
        card = ClickableProfileCard()
        card.setObjectName("SidebarProfileCard")
        card.setCursor(Qt.PointingHandCursor)
        card.clicked.connect(self.profile_clicked.emit)
        self.profile_card = card
        card.setMinimumHeight(60)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(10)

        avatar = QLabel("▣")
        avatar.setObjectName("SidebarAvatar")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(38, 38)

        qicon = get_icon("creeper")
        if qicon:
            avatar.setPixmap(qicon.pixmap(QSize(38, 38)))

        info = QVBoxLayout()
        info.setSpacing(1)

        name = QLabel("NexusPlayer")
        name.setObjectName("SidebarProfileName")
        self.profile_name_label = name

        status = QLabel("Offline")
        status.setObjectName("SidebarProfileStatus")
        self.profile_status_label = status
        self._profile_text_widgets.extend([name, status])

        info.addWidget(name)
        info.addWidget(status)

        arrow = QLabel("⌄")
        arrow.setObjectName("SidebarProfileArrow")
        arrow.setAlignment(Qt.AlignCenter)
        self._profile_text_widgets.append(arrow)

        layout.addWidget(avatar)
        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(arrow)

        card.setToolTip("Профиль, аккаунты и скины")
        return card

    def refresh_theme(self, theme: str | None = None):
        for button in self.buttons:
            button.apply_icon()
            if self.compact:
                button.setIconSize(QSize(20, 20))
            else:
                button.setIconSize(QSize(18, 18))

        self.apply_logo_icon()

        avatar = self.findChild(QLabel, "SidebarAvatar")
        if avatar is None and hasattr(self, "profile_card"):
            avatar = self.profile_card.findChild(QLabel, "SidebarAvatar")

        creeper_icon = get_icon("creeper")
        if creeper_icon and avatar is not None:
            avatar.setPixmap(creeper_icon.pixmap(QSize(38, 38)))

        self.update_profile()

    def update_profile(self):
        username = "NexusPlayer"
        status = "Offline"

        try:
            from auth.account_manager import AccountManager

            account = AccountManager().get_active_account()
            if account:
                username = (
                    account.get("display_name")
                    or account.get("username")
                    or username
                )
                provider = str(account.get("provider") or account.get("type") or "").lower()
                if provider in {"microsoft", "ely", "elyby"}:
                    status = provider.capitalize()
                elif account.get("token"):
                    status = "Online"
        except Exception:
            pass

        if hasattr(self, "profile_name_label") and self.profile_name_label:
            self.profile_name_label.setText(username)
        if hasattr(self, "profile_status_label") and self.profile_status_label:
            self.profile_status_label.setText(status)
