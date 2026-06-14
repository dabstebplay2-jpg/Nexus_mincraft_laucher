from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
)

from ui.icon_utils import icon


class Topbar(QWidget):
    search_submitted = Signal(str)
    play_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("Topbar")
        self.setFixedHeight(86)

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
        self.search_input.setMinimumWidth(360)

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
        self.status_button.setIcon(icon("rocket"))
        self.status_button.setIconSize(QSize(16, 16))

        self.play_button = QPushButton("Играть")
        self.play_button.setObjectName("TopbarPlayButton")
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setIcon(icon("play"))
        self.play_button.setIconSize(QSize(18, 18))
        self.play_button.clicked.connect(self.play_clicked.emit)

        root.addLayout(title_block)
        root.addStretch()
        root.addWidget(self.search_input)
        root.addWidget(self.status_button)
        root.addWidget(self.play_button)

    def submit_search(self):
        self.search_submitted.emit(self.search_input.text())

    def set_page(self, title, subtitle):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
