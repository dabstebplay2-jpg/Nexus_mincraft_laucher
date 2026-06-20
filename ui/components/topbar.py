from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
)

try:
    from ui.icon_utils import icon
except Exception:
    icon = None


class Topbar(QWidget):
    search_submitted = Signal(str)
    play_clicked = Signal()
    sidebar_toggle_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("Topbar")
        self.setFixedHeight(60)
        self.compact = False

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 8, 16, 8)
        root.setSpacing(10)

        title_block = QVBoxLayout()
        title_block.setSpacing(1)

        self.title_label = QLabel("Главная")
        self.title_label.setObjectName("TopbarTitle")

        self.subtitle_label = QLabel("Центр управления Nexus Launcher")
        self.subtitle_label.setObjectName("TopbarSubtitle")

        title_block.addWidget(self.title_label)
        title_block.addWidget(self.subtitle_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("TopbarSearch")
        self.search_input.setPlaceholderText("Поиск по сборкам и каталогу")
        self.search_input.setMinimumWidth(180)
        self.search_input.setMaximumWidth(330)

        try:
            self.search_input.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        except Exception:
            try:
                self.search_input.addAction(icon("search"), QLineEdit.LeadingPosition)
            except Exception:
                pass

        self.search_input.returnPressed.connect(self.submit_search)

        self.sidebar_button = QPushButton("☰")
        self.sidebar_button.setObjectName("TopbarMenuButton")
        self.sidebar_button.setCursor(Qt.PointingHandCursor)
        self.sidebar_button.setToolTip("Свернуть / развернуть меню")
        self.sidebar_button.setFixedWidth(42)
        self.sidebar_button.clicked.connect(self.sidebar_toggle_clicked.emit)

        self.play_button = QPushButton("Играть")
        self.play_button.setObjectName("TopbarPlayButton")
        self.play_button.setCursor(Qt.PointingHandCursor)
        try:
            if icon:
                self.play_button.setIcon(icon("play"))
        except Exception:
            pass
        self.play_button.setIconSize(QSize(18, 18))
        self.play_button.clicked.connect(self.play_clicked.emit)

        root.addLayout(title_block)
        root.addStretch()
        root.addWidget(self.sidebar_button)
        root.addWidget(self.search_input)
        root.addWidget(self.play_button)

    def refresh_theme(self, theme: str | None = None):
        try:
            from ui.icon_utils import icon as load_icon
            play_icon = load_icon("play")
            if play_icon:
                self.play_button.setIcon(play_icon)
                self.play_button.setIconSize(QSize(18, 18))
        except Exception:
            pass

    def submit_search(self):
        self.search_submitted.emit(self.search_input.text())

    def set_page(self, title, subtitle):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def set_compact(self, compact: bool):
        compact = bool(compact)
        if self.compact == compact:
            return

        self.compact = compact
        self.setFixedHeight(54 if compact else 60)
        self.subtitle_label.setVisible(not compact)
        self.search_input.setMinimumWidth(120 if compact else 180)
        self.search_input.setMaximumWidth(220 if compact else 330)
        self.sidebar_button.setFixedWidth(38 if compact else 42)
        self.play_button.setText("▶" if compact else "Играть")

    def set_sidebar_collapsed(self, collapsed: bool):
        self.sidebar_button.setText("☰" if collapsed else "‹")
        self.sidebar_button.setToolTip("Развернуть меню" if collapsed else "Свернуть меню")
