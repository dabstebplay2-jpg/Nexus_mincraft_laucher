from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.download_manager import DownloadManager


class DownloadsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.manager = DownloadManager()
        self.manager.seed_demo_if_empty()

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(36, 32, 36, 24)
        self.root.setSpacing(18)

        self.build_ui()
        self.refresh()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1500)

    def build_ui(self):
        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("Загрузки")
        title.setObjectName("PageTitle")

        subtitle = QLabel("Центр загрузок Nexus: Minecraft, моды, Java, скины и история операций.")
        subtitle.setObjectName("PageDescription")
        subtitle.setWordWrap(True)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.clicked.connect(self.refresh)

        clear_completed_btn = QPushButton("Очистить завершённые")
        clear_completed_btn.setObjectName("SecondaryButton")
        clear_completed_btn.clicked.connect(self.clear_completed)

        clear_all_btn = QPushButton("Очистить всё")
        clear_all_btn.setObjectName("DangerButton")
        clear_all_btn.clicked.connect(self.clear_all)

        header.addLayout(title_box, 1)
        header.addWidget(refresh_btn)
        header.addWidget(clear_completed_btn)
        header.addWidget(clear_all_btn)

        self.root.addLayout(header)

        stats = QHBoxLayout()
        stats.setSpacing(14)

        self.active_stat = self.stat_card("Активные", "0", "идут сейчас")
        self.done_stat = self.stat_card("Завершённые", "0", "готовые")
        self.failed_stat = self.stat_card("Ошибки", "0", "с ошибками")
        self.total_stat = self.stat_card("Всего", "0", "в истории")

        stats.addWidget(self.active_stat)
        stats.addWidget(self.done_stat)
        stats.addWidget(self.failed_stat)
        stats.addWidget(self.total_stat)

        self.root.addLayout(stats)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("ScrollArea")
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(14)

        self.scroll.setWidget(self.container)
        self.root.addWidget(self.scroll, 1)

    def stat_card(self, title, value, desc):
        card = QFrame()
        card.setObjectName("DownloadSummaryCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("HeroStatTitle")

        value_label = QLabel(value)
        value_label.setObjectName("DownloadBigNumber")

        desc_label = QLabel(desc)
        desc_label.setObjectName("InstanceMeta")

        card.value_label = value_label

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)

        return card

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget:
                widget.deleteLater()

            if child_layout:
                self.clear_layout(child_layout)

    def refresh(self):
        tasks = self.manager.list_tasks()

        active = [task for task in tasks if task.get("state") == "active"]
        done = [task for task in tasks if task.get("state") == "completed"]
        failed = [task for task in tasks if task.get("state") == "failed"]

        self.active_stat.value_label.setText(str(len(active)))
        self.done_stat.value_label.setText(str(len(done)))
        self.failed_stat.value_label.setText(str(len(failed)))
        self.total_stat.value_label.setText(str(len(tasks)))

        self.clear_layout(self.list_layout)

        if not tasks:
            self.list_layout.addWidget(self.empty_card())
            self.list_layout.addStretch()
            return

        if active:
            self.list_layout.addWidget(self.section_title("Активные загрузки"))
            for task in active:
                self.list_layout.addWidget(self.task_card(task))

        history = [task for task in tasks if task.get("state") != "active"]

        if history:
            self.list_layout.addWidget(self.section_title("История"))
            for task in history:
                self.list_layout.addWidget(self.task_card(task))

        self.list_layout.addStretch()

    def section_title(self, text):
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def empty_card(self):
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 40, 28, 40)
        layout.setSpacing(10)

        title = QLabel("Загрузок пока нет")
        title.setObjectName("SectionTitle")
        title.setAlignment(Qt.AlignCenter)

        desc = QLabel("Когда ты будешь запускать Minecraft или устанавливать моды, задачи появятся здесь.")
        desc.setObjectName("PageDescription")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)

        return card

    def task_card(self, task):
        active = task.get("state") == "active"

        card = QFrame()
        card.setObjectName("DownloadTaskCardActive" if active else "DownloadTaskCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(14)

        icon = QLabel(self.manager.icon(task.get("kind")))
        icon.setObjectName("DownloadIcon")
        icon.setFixedSize(52, 52)
        icon.setAlignment(Qt.AlignCenter)

        info = QVBoxLayout()
        info.setSpacing(4)

        title = QLabel(task.get("title", "Загрузка"))
        title.setObjectName("CardTitle")

        subtitle = QLabel(task.get("subtitle") or task.get("status") or "")
        subtitle.setObjectName("PageDescription")
        subtitle.setWordWrap(True)

        status = QLabel(self.status_text(task))
        status.setObjectName("DownloadStatus")

        info.addWidget(title)
        info.addWidget(subtitle)
        info.addWidget(status)

        badge = QLabel(self.state_text(task))
        badge.setObjectName("SmallBadge")

        top.addWidget(icon)
        top.addLayout(info, 1)
        top.addWidget(badge)

        progress = QProgressBar()
        progress.setObjectName("DownloadProgress")
        progress.setRange(0, 100)
        progress.setValue(int(task.get("progress") or 0))
        progress.setTextVisible(False)
        progress.setFixedHeight(8)

        meta = QLabel("Создано: " + self.manager.time_text(task.get("created_at")))
        meta.setObjectName("InstanceMeta")

        layout.addLayout(top)
        layout.addWidget(progress)
        layout.addWidget(meta)

        error = task.get("error")
        if error:
            error_label = QLabel(str(error))
            error_label.setObjectName("DownloadError")
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

        return card

    def status_text(self, task):
        progress = int(task.get("progress") or 0)
        status = task.get("status") or "Ожидание"
        return f"{status} • {progress}%"

    def state_text(self, task):
        state = task.get("state")

        if state == "active":
            return "ACTIVE"
        if state == "completed":
            return "DONE"
        if state == "failed":
            return "ERROR"

        return "TASK"

    def clear_completed(self):
        count = self.manager.clear_completed()
        self.refresh()
        QMessageBox.information(self, "Готово", f"Удалено завершённых задач: {count}")

    def clear_all(self):
        result = QMessageBox.question(
            self,
            "Очистить всё?",
            "Удалить всю историю загрузок?"
        )

        if result != QMessageBox.Yes:
            return

        count = self.manager.clear_all()
        self.refresh()
        QMessageBox.information(self, "Готово", f"Удалено задач: {count}")

    def refresh_page(self):
        self.refresh()
