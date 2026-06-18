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

    def __init__(self):
        super().__init__()

        self.setObjectName("Topbar")
        self.setFixedHeight(86)
        self.compact = False

        root = QHBoxLayout(self)
        root.setContentsMargins(26, 14, 28, 14)
        root.setSpacing(16)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        self.title_label = QLabel("Главная")
        self.title_label.setObjectName("TopbarTitle")

        self.subtitle_label = QLabel("Центр управления Nexus Launcher")
        self.subtitle_label.setObjectName("TopbarSubtitle")

        title_block.addWidget(self.title_label)
        title_block.addWidget(self.subtitle_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("TopbarSearch")
        self.search_input.setPlaceholderText("Поиск сборок, модов, настроек...")
        self.search_input.setMinimumWidth(240)
        self.search_input.setMaximumWidth(420)

        try:
            self.search_input.addAction(icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        except Exception:
            try:
                self.search_input.addAction(icon("search"), QLineEdit.LeadingPosition)
            except Exception:
                pass

        self.search_input.returnPressed.connect(self.submit_search)

        self.status_button = QPushButton("READY")
        self.status_button.setObjectName("TopbarStatusButton")
        self.status_button.setCursor(Qt.PointingHandCursor)
        try:
            if icon:
                self.status_button.setIcon(icon("rocket"))
            else:
                self.status_button.setText("🚀")
        except Exception:
            pass
        self.status_button.setIconSize(QSize(16, 16))

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
        root.addWidget(self.search_input, 1)
        root.addWidget(self.status_button)
        root.addWidget(self.play_button)

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
        self.setFixedHeight(62 if compact else 86)
        self.title_label.setVisible(not compact)
        self.subtitle_label.setVisible(False if compact else True)
        self.status_button.setVisible(not compact)
        self.search_input.setMinimumWidth(120 if compact else 240)
        self.search_input.setMaximumWidth(260 if compact else 420)
        self.play_button.setText("▶" if compact else "Играть")

