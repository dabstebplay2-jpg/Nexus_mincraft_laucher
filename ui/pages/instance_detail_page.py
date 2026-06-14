from pathlib import Path
import shutil
import os
import webbrowser

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTabWidget,
    QScrollArea,
    QMessageBox,
)


class InstanceDetailPage(QWidget):
    back_clicked = Signal()
    play_clicked = Signal(dict)

    def __init__(self):
        super().__init__()

        self.instance = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("ScrollArea")

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(36, 32, 36, 32)
        self.content_layout.setSpacing(18)

        self.scroll.setWidget(self.content)

        root.addWidget(self.scroll)

    def set_instance(self, instance):
        self.instance = instance or {}
        self.refresh()

    def clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)

            widget = item.widget()
            layout = item.layout()

            if widget:
                widget.deleteLater()

            if layout:
                self.clear_layout(layout)

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
        self.clear()

        if not self.instance:
            empty = QLabel("Сборка не выбрана")
            empty.setObjectName("PageTitle")
            self.content_layout.addWidget(empty)
            return

        self.content_layout.addWidget(self.create_hero())
        self.content_layout.addWidget(self.create_tabs())
        self.content_layout.addStretch()

    def create_hero(self):
        hero = QFrame()
        hero.setObjectName("InstanceDetailHero")
        hero.setMinimumHeight(210)

        layout = QVBoxLayout(hero)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        top = QHBoxLayout()

        back_button = QPushButton("← Назад")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self.back_clicked.emit)

        play_button = QPushButton("▶ Играть")
        play_button.setObjectName("PrimaryButton")
        play_button.clicked.connect(lambda: self.play_clicked.emit(self.instance))

        folder_button = QPushButton("Папка")
        folder_button.setObjectName("SecondaryButton")
        folder_button.clicked.connect(self.open_folder)

        top.addWidget(back_button)
        top.addStretch()
        top.addWidget(folder_button)
        top.addWidget(play_button)

        name = QLabel(self.instance.get("name", "Без названия"))
        name.setObjectName("PageTitle")

        meta = QLabel(
            f'Minecraft {self.instance.get("minecraft_version", "unknown")} • '
            f'{self.instance.get("loader", "vanilla").capitalize()} • '
            f'RAM: {self.get_ram_text()}'
        )
        meta.setObjectName("PageDescription")
        meta.setWordWrap(True)

        path = QLabel(str(self.get_instance_path()))
        path.setObjectName("InstanceMeta")
        path.setWordWrap(True)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)

        metrics.addWidget(self.metric_card("Моды", str(self.count_mods())))
        metrics.addWidget(self.metric_card("Миры", str(self.count_worlds())))
        metrics.addWidget(self.metric_card("Размер", self.get_size_text()))
        metrics.addStretch()

        layout.addLayout(top)
        layout.addWidget(name)
        layout.addWidget(meta)
        layout.addWidget(path)
        layout.addLayout(metrics)

        return hero

    def metric_card(self, title, value):
        card = QFrame()
        card.setObjectName("SettingsStatCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("HeroStatTitle")

        value_label = QLabel(value)
        value_label.setObjectName("HeroStatValue")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def create_tabs(self):
        tabs = QTabWidget()
        tabs.setObjectName("InstanceDetailTabs")

        tabs.addTab(self.create_overview_tab(), "Обзор")
        tabs.addTab(self.create_mods_tab(), "Моды")
        tabs.addTab(self.create_worlds_tab(), "Миры")
        tabs.addTab(self.create_logs_tab(), "Логи")
        tabs.addTab(self.create_settings_tab(), "Настройки")

        return tabs

    def make_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        return page, layout

    def create_overview_tab(self):
        page, layout = self.make_tab()

        layout.addWidget(self.info_row("Название", self.instance.get("name", "—")))
        layout.addWidget(self.info_row("Версия Minecraft", self.instance.get("minecraft_version", "—")))
        layout.addWidget(self.info_row("Загрузчик", self.instance.get("loader", "vanilla")))
        layout.addWidget(self.info_row("RAM", self.get_ram_text()))
        layout.addWidget(self.info_row("Папка сборки", str(self.get_instance_path())))
        layout.addWidget(self.info_row("Папка Minecraft", str(self.get_minecraft_dir())))

        layout.addStretch()
        return page

    def create_mods_tab(self):
        page, layout = self.make_tab()

        mods_dir = self.get_mods_dir()
        mods_dir.mkdir(parents=True, exist_ok=True)

        mods = sorted(mods_dir.glob("*.jar"))

        if not mods:
            layout.addWidget(self.empty_label("Моды пока не установлены. Открой вкладку «Моды» и установи их через Modrinth."))
            layout.addStretch()
            return page

        for mod in mods:
            layout.addWidget(self.file_row(mod, allow_delete=True))

        layout.addStretch()
        return page

    def create_worlds_tab(self):
        page, layout = self.make_tab()

        saves_dir = self.get_minecraft_dir() / "saves"
        saves_dir.mkdir(parents=True, exist_ok=True)

        worlds = [item for item in saves_dir.iterdir() if item.is_dir()]

        if not worlds:
            layout.addWidget(self.empty_label("Миров пока нет. После создания мира в Minecraft он появится здесь."))
            layout.addStretch()
            return page

        for world in sorted(worlds):
            layout.addWidget(self.file_row(world, allow_delete=False))

        layout.addStretch()
        return page

    def create_logs_tab(self):
        page, layout = self.make_tab()

        logs_dir = self.get_minecraft_dir() / "logs"
        latest = logs_dir / "latest.log"

        if latest.exists():
            text = latest.read_text(encoding="utf-8", errors="ignore")[-12000:]
            label = QLabel(text)
            label.setObjectName("LogViewer")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setWordWrap(True)
            layout.addWidget(label)
        else:
            layout.addWidget(self.empty_label("Лог Minecraft пока не найден."))

        layout.addStretch()
        return page

    def create_settings_tab(self):
        page, layout = self.make_tab()

        layout.addWidget(self.info_row("ID", self.instance.get("id", "—")))
        layout.addWidget(self.info_row("Создана", self.instance.get("created_at", "—")))
        layout.addWidget(self.info_row("Последний запуск", str(self.instance.get("last_played_at", "—"))))
        layout.addWidget(self.info_row("Путь", str(self.get_instance_path())))

        layout.addStretch()
        return page

    def info_row(self, title, value):
        row = QFrame()
        row.setObjectName("DetailInfoRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("HeroStatTitle")
        title_label.setMinimumWidth(180)

        value_label = QLabel(str(value))
        value_label.setObjectName("PanelText")
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(title_label)
        layout.addWidget(value_label, 1)

        return row

    def file_row(self, path, allow_delete=False):
        row = QFrame()
        row.setObjectName("DetailInfoRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        name = QLabel(path.name)
        name.setObjectName("InstanceTitle")

        meta = QLabel(self.path_size_text(path))
        meta.setObjectName("InstanceMeta")

        open_button = QPushButton("Открыть")
        open_button.setObjectName("SecondaryButton")
        open_button.clicked.connect(lambda: self.open_path(path))

        layout.addWidget(name, 1)
        layout.addWidget(meta)
        layout.addWidget(open_button)

        if allow_delete:
            delete_button = QPushButton("Удалить")
            delete_button.setObjectName("DangerButton")
            delete_button.clicked.connect(lambda: self.delete_path(path))
            layout.addWidget(delete_button)

        return row

    def empty_label(self, text):
        label = QLabel(text)
        label.setObjectName("PanelText")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumHeight(140)
        return label

    def get_instance_path(self):
        return Path(self.instance.get("path") or self.instance.get("instance_dir") or "")

    def get_minecraft_dir(self):
        if self.instance.get("minecraft_dir"):
            return Path(self.instance["minecraft_dir"])

        return self.get_instance_path() / ".minecraft"

    def get_mods_dir(self):
        return self.get_minecraft_dir() / "mods"

    def get_ram_text(self):
        ram = self.instance.get("ram_mb") or self.instance.get("ram") or 4096

        try:
            ram = int(ram)
            if ram >= 1024:
                gb = ram / 1024
                if abs(gb - round(gb)) < 0.05:
                    return f"{int(round(gb))} GB"
                return f"{gb:.1f} GB"
        except Exception:
            pass

        return str(ram)

    def count_mods(self):
        mods_dir = self.get_mods_dir()

        if not mods_dir.exists():
            return 0

        return len(list(mods_dir.glob("*.jar")))

    def count_worlds(self):
        saves_dir = self.get_minecraft_dir() / "saves"

        if not saves_dir.exists():
            return 0

        return len([item for item in saves_dir.iterdir() if item.is_dir()])

    def get_size_text(self):
        path = self.get_instance_path()

        if not path.exists():
            return "0 MB"

        total = 0

        for file in path.rglob("*"):
            try:
                if file.is_file():
                    total += file.stat().st_size
            except Exception:
                pass

        mb = total / (1024 * 1024)

        if mb >= 1024:
            return f"{mb / 1024:.1f} GB"

        return f"{mb:.0f} MB"

    def path_size_text(self, path):
        try:
            if path.is_file():
                size = path.stat().st_size / (1024 * 1024)
                return f"{size:.1f} MB"

            if path.is_dir():
                count = sum(1 for _ in path.rglob("*"))
                return f"{count} файлов"
        except Exception:
            pass

        return ""

    def open_folder(self):
        self.open_path(self.get_instance_path())

    def open_path(self, path):
        path = Path(path)

        if not path.exists():
            QMessageBox.warning(self, "Не найдено", f"Путь не найден:\n{path}")
            return

        try:
            os.startfile(str(path))
        except Exception:
            webbrowser.open(path.as_uri())

    def delete_path(self, path):
        result = QMessageBox.question(
            self,
            "Удалить файл?",
            f"Удалить:\n{path.name}?"
        )

        if result != QMessageBox.Yes:
            return

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

            self.refresh()
        except Exception as error:
            QMessageBox.critical(self, "Ошибка удаления", str(error))
