from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.icon_utils import icon


EXPANDED_WIDTH = 200
COMPACT_WIDTH = 64


class SidebarButton(QPushButton):
    def __init__(self, icon_name, title, index):
        super().__init__(title)
        self.icon_name = icon_name
        self.full_text = title
        self.index = index
        self.setObjectName("SidebarNavButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(42)
        self.setIcon(icon(icon_name))
        self.setIconSize(QSize(18, 18))
        self.setToolTip(title)


class ClickableLogo(QWidget):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class Sidebar(QWidget):
    page_changed = Signal(int)
    collapsed_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.compact = False
        self.buttons = []
        self.disabled_pages = set()
        self.setFixedWidth(EXPANDED_WIDTH)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 14, 12, 16)
        self.root_layout.setSpacing(6)

        self.logo_card = ClickableLogo()
        self.logo_card.setObjectName("SidebarLogoCard")
        self.logo_card.clicked.connect(self._on_logo_clicked)
        logo = QHBoxLayout(self.logo_card)
        logo.setContentsMargins(5, 4, 5, 4)
        logo.setSpacing(5)
        self.logo_mark = QLabel()
        self.logo_mark.setFixedSize(42, 42)
        self.logo_mark.setPixmap(icon("nexus").pixmap(QSize(40, 40)))
        logo.addWidget(self.logo_mark)
        names = QVBoxLayout()
        names.setSpacing(0)
        self.logo_title = QLabel("NEXUS")
        self.logo_title.setObjectName("NexusLogoTitle")
        self.logo_subtitle = QLabel("LAUNCHER")
        self.logo_subtitle.setObjectName("NexusLogoSubtitle")
        names.addWidget(self.logo_title)
        names.addWidget(self.logo_subtitle)
        logo.addLayout(names, 1)
        self.collapse_button = QPushButton()
        self.collapse_button.setObjectName("SidebarCollapseButton")
        self.collapse_button.setIcon(icon("chevron-left"))
        self.collapse_button.setIconSize(QSize(14, 14))
        self.collapse_button.setFixedSize(24, 24)
        self.collapse_button.setToolTip("Свернуть меню")
        self.collapse_button.setCursor(Qt.PointingHandCursor)
        self.collapse_button.clicked.connect(lambda: self._change_compact(True))
        logo.addWidget(self.collapse_button)
        self.root_layout.addWidget(self.logo_card)
        self.root_layout.addSpacing(22)

        for icon_name, title, index in (
            ("home", "Главная", 0),
            ("instances", "Сборки", 1),
            ("mods", "Каталог", 2),
        ):
            self.root_layout.addWidget(self._nav(icon_name, title, index))
        self.root_layout.addStretch()
        self.root_layout.addWidget(self._nav("settings", "Настройки", 6))

    def _nav(self, icon_name, title, index):
        button = SidebarButton(icon_name, title, index)
        button.clicked.connect(lambda checked=False, i=index: self.page_changed.emit(i))
        self.buttons.append(button)
        return button

    def _change_compact(self, compact):
        self.set_compact(compact)
        self.collapsed_changed.emit(compact)

    def _on_logo_clicked(self):
        if self.compact:
            self._change_compact(False)

    def set_compact(self, compact: bool):
        compact = bool(compact)
        if self.compact == compact:
            return
        self.compact = compact
        self.setProperty("compact", compact)
        width = COMPACT_WIDTH if compact else EXPANDED_WIDTH
        self.setFixedWidth(width)
        self.root_layout.setContentsMargins(4 if compact else 12, 14, 4 if compact else 12, 16)
        for button in self.buttons:
            button.setText("" if compact else button.full_text)
            button.setProperty("compact", compact)
            button.setFixedWidth(48 if compact else 176)
            button.style().unpolish(button)
            button.style().polish(button)
        self.logo_title.setVisible(not compact)
        self.logo_subtitle.setVisible(not compact)
        self.collapse_button.setVisible(not compact)
        self.logo_mark.setToolTip("Развернуть меню" if compact else "")
        self.logo_mark.setCursor(Qt.PointingHandCursor if compact else Qt.ArrowCursor)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_collapsed(self, collapsed: bool):
        self.set_compact(collapsed)

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
            button.setEnabled(button.index not in self.disabled_pages)

    def refresh_theme(self, theme=None):
        for button in self.buttons:
            button.setIcon(icon(button.icon_name))
        self.logo_mark.setPixmap(icon("nexus").pixmap(QSize(40, 40)))
