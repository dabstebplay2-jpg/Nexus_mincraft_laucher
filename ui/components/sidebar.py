from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
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
        self.setObjectName("SidebarNavButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setCheckable(True)
        self.setProperty("active", False)

        qicon = get_icon(icon_name)

        if qicon:
            self.setIcon(qicon)
            self.setIconSize(QSize(19, 19))


class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        self.compact = False
        self._nav_labels = []
        self._logo_text_widgets = []
        self._profile_text_widgets = []

        self.buttons = []
        self.disabled_pages = set()

        self.root_layout = QVBoxLayout(self)
        root = self.root_layout
        root.setContentsMargins(14, 16, 14, 16)
        root.setSpacing(14)

        root.addWidget(self.create_logo())
        root.addSpacing(8)

        nav_title = QLabel("НАВИГАЦИЯ")
        nav_title.setObjectName("SidebarSectionTitle")
        root.addWidget(nav_title)

        for icon_name, text, index in [
            ("home", "Главная", 0),
            ("instances", "Сборки", 1),
            ("mods", "Моды", 2),
            ("library", "Библиотека", 3),
            ("downloads", "Загрузки", 4),
        ]:
            root.addWidget(self.create_nav_button(icon_name, text, index))

        root.addSpacing(12)

        system_title = QLabel("СИСТЕМА")
        system_title.setObjectName("SidebarSectionTitle")
        root.addWidget(system_title)

        for icon_name, text, index in [
            ("accounts", "Аккаунты", 5),
            ("settings", "Настройки", 6),
            ("logs", "Логи", 7),
        ]:
            root.addWidget(self.create_nav_button(icon_name, text, index))

        root.addStretch()
        root.addWidget(self.create_profile_card())

    def create_logo(self):
        card = QFrame()
        card.setObjectName("SidebarLogoCard")
        card.setMinimumHeight(96)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        mark = QLabel("×")
        mark.setObjectName("NexusMark")
        mark.setAlignment(Qt.AlignCenter)
        mark.setFixedSize(52, 52)

        qicon = get_icon("nexus")
        if qicon:
            mark.setPixmap(qicon.pixmap(QSize(52, 52)))

        text = QVBoxLayout()
        text.setSpacing(0)

        title = QLabel("NEXUS")
        title.setObjectName("NexusLogoTitle")

        subtitle = QLabel("LAUNCHER")
        subtitle.setObjectName("NexusLogoSubtitle")
        self._logo_text_widgets.extend([title, subtitle])

        text.addWidget(title)
        text.addWidget(subtitle)

        layout.addWidget(mark)
        layout.addLayout(text)
        layout.addStretch()

        return card

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
        self.setFixedWidth(74 if compact else 260)
        self.root_layout.setContentsMargins(8 if compact else 14, 12 if compact else 16, 8 if compact else 14, 12 if compact else 16)
        self.root_layout.setSpacing(10 if compact else 14)

        for button in self.buttons:
            button.setText("" if compact else getattr(button, "full_text", button.text()))
            button.setMinimumHeight(46 if compact else 48)
            button.setIconSize(QSize(22, 22) if compact else QSize(19, 19))
            button.setToolTip(getattr(button, "full_text", ""))

        for widget in self._logo_text_widgets + self._profile_text_widgets:
            widget.setVisible(not compact)

    def set_active(self, index):
        for button in self.buttons:
            active = button.index == index

            button.setChecked(active)
            button.setProperty("active", active)

            button.style().unpolish(button)
            button.style().polish(button)

    def set_disabled_pages(self, pages):
        self.disabled_pages = set(pages or [])

        for button in self.buttons:
            disabled = button.index in self.disabled_pages
            button.setProperty("disabledPage", disabled)

            button.style().unpolish(button)
            button.style().polish(button)

    def create_profile_card(self):
        card = QFrame()
        card.setObjectName("SidebarProfileCard")
        card.setMinimumHeight(78)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        avatar = QLabel("▣")
        avatar.setObjectName("SidebarAvatar")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(46, 46)

        qicon = get_icon("creeper")
        if qicon:
            avatar.setPixmap(qicon.pixmap(QSize(46, 46)))

        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel("NexusPlayer")
        name.setObjectName("SidebarProfileName")

        status = QLabel("● Offline")
        status.setObjectName("SidebarProfileStatus")
        self._profile_text_widgets.extend([name, status])

        info.addWidget(name)
        info.addWidget(status)

        arrow = QLabel("⌄")
        arrow.setObjectName("SidebarProfileArrow")
        arrow.setAlignment(Qt.AlignCenter)

        layout.addWidget(avatar)
        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(arrow)

        return card


