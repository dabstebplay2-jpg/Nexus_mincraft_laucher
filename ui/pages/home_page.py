"""Launch focused home page. Game operations remain in InstancesPage."""

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from core.instance_manager import get_instance_manager
from storage.json_store import load_json
from ui.icon_utils import icon

logger = logging.getLogger(__name__)


def _mod_count(instance):
    path = Path(instance.get("path") or "")
    index = load_json(path / "mods_index.json", {"mods": []})
    mods = index.get("mods", []) if isinstance(index, dict) else []
    if mods:
        return len(mods)
    mods_dir = Path(instance.get("minecraft_dir") or path / ".minecraft") / "mods"
    return len(list(mods_dir.glob("*.jar"))) if mods_dir.is_dir() else 0


def _last_played(value):
    if not value:
        return "Ещё не запускалась"
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y · %H:%M")
    except (TypeError, ValueError):
        return str(value)


class HomePage(QWidget):
    navigate_requested = Signal(int)
    create_instance_requested = Signal()
    import_instance_requested = Signal()
    play_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self.instance_manager = get_instance_manager()
        self.instances = []
        self.active_instance_id = None
        self.launch_state = "ready"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("ScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("HomeContent")
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        column = QWidget()
        column.setMaximumWidth(1320)
        column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        centered = QHBoxLayout()
        centered.setContentsMargins(0, 0, 0, 0)
        centered.addStretch(1)
        centered.addWidget(column, 100)
        centered.addStretch(1)
        root.addLayout(centered)
        root.addStretch()
        page = QVBoxLayout(column)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(20)

        eyebrow = QLabel("NEXUS LAUNCHER / 2.0")
        eyebrow.setObjectName("HomeEyebrow")
        page.addWidget(eyebrow)

        heading = QLabel("Ваш Minecraft начинается здесь")
        heading.setObjectName("HomeHeading")
        page.addWidget(heading)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self._create_empty_state())
        self.content_stack.addWidget(self._create_launch_view())
        page.addWidget(self.content_stack)
        self.refresh()

    def _create_empty_state(self):
        empty = QFrame()
        empty.setObjectName("HomeEmpty")
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(40, 42, 40, 42)
        layout.setSpacing(16)
        layout.addStretch()
        mark = QLabel()
        mark.setPixmap(icon("nexus").pixmap(QSize(88, 88)))
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)
        title = QLabel("У вас пока нет сборок")
        title.setObjectName("HomeEmptyTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        caption = QLabel("Создайте свою первую сборку или импортируйте готовую — и можно играть.")
        caption.setObjectName("HomeMuted")
        caption.setWordWrap(True)
        caption.setAlignment(Qt.AlignCenter)
        layout.addWidget(caption)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()
        create = QPushButton("Создать сборку")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(self.create_instance_requested.emit)
        actions.addWidget(create)
        import_button = QPushButton("Импортировать сборку")
        import_button.setObjectName("SecondaryButton")
        import_button.clicked.connect(self.import_instance_requested.emit)
        actions.addWidget(import_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()
        return empty

    def _create_launch_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        picker_row = QHBoxLayout()
        picker_row.setSpacing(10)
        picker_title = QLabel("АКТИВНАЯ СБОРКА")
        picker_title.setObjectName("HomeEyebrow")
        picker_row.addWidget(picker_title)
        picker_row.addStretch()
        self.instance_picker = QComboBox()
        self.instance_picker.setObjectName("HomeInstancePicker")
        self.instance_picker.setMinimumWidth(210)
        self.instance_picker.setMaximumWidth(320)
        self.instance_picker.currentIndexChanged.connect(self._select_instance)
        picker_row.addWidget(self.instance_picker)
        layout.addLayout(picker_row)

        hero = QFrame()
        hero.setObjectName("LaunchHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(34, 32, 34, 30)
        hero_layout.setSpacing(14)

        hero_top = QHBoxLayout()
        hero_top.setSpacing(20)
        text = QVBoxLayout()
        text.setSpacing(8)
        tag = QLabel("ГОТОВО К ИГРЕ")
        tag.setObjectName("HeroKicker")
        text.addWidget(tag)
        self.instance_title = QLabel()
        self.instance_title.setObjectName("LaunchHeroTitle")
        self.instance_title.setWordWrap(True)
        text.addWidget(self.instance_title)
        self.instance_meta = QLabel()
        self.instance_meta.setObjectName("LaunchHeroMeta")
        self.instance_meta.setWordWrap(True)
        text.addWidget(self.instance_meta)
        text.addStretch()
        hero_top.addLayout(text, 1)
        mark = QLabel()
        mark.setObjectName("LaunchHeroMark")
        mark.setPixmap(icon("nexus").pixmap(QSize(174, 174)))
        mark.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hero_top.addWidget(mark)
        hero_layout.addLayout(hero_top, 1)

        launch_row = QHBoxLayout()
        launch_row.setSpacing(16)
        self.play_button = QPushButton("ИГРАТЬ")
        self.play_button.setObjectName("HeroPlayButton")
        self.play_button.setIcon(icon("play"))
        self.play_button.setIconSize(QSize(22, 22))
        self.play_button.setCursor(Qt.PointingHandCursor)
        self.play_button.setMinimumSize(220, 56)
        self.play_button.clicked.connect(self._play)
        launch_row.addWidget(self.play_button)
        state_block = QVBoxLayout()
        state_block.setSpacing(3)
        self.state_title = QLabel("Готова к запуску")
        self.state_title.setObjectName("LaunchStateTitle")
        self.state_detail = QLabel("Нажмите, чтобы открыть Minecraft")
        self.state_detail.setObjectName("HomeMuted")
        state_block.addWidget(self.state_title)
        state_block.addWidget(self.state_detail)
        launch_row.addLayout(state_block)
        launch_row.addStretch()
        hero_layout.addLayout(launch_row)
        layout.addWidget(hero, 1)

        details = QFrame()
        details.setObjectName("HomeDetails")
        details_layout = QHBoxLayout(details)
        details_layout.setContentsMargins(22, 16, 22, 16)
        details_layout.setSpacing(20)
        self.last_played_label = self._detail(details_layout, "ПОСЛЕДНИЙ ЗАПУСК")
        self.mods_label = self._detail(details_layout, "МОДЫ")
        details_layout.addStretch()
        all_instances = QPushButton("Все сборки")
        all_instances.setObjectName("SmallGhostButton")
        all_instances.clicked.connect(lambda: self.navigate_requested.emit(1))
        details_layout.addWidget(all_instances)
        layout.addWidget(details)
        return page

    def _detail(self, row, label):
        column = QVBoxLayout()
        column.setSpacing(5)
        caption = QLabel(label)
        caption.setObjectName("HomeEyebrow")
        value = QLabel("—")
        value.setObjectName("HomeDetailValue")
        column.addWidget(caption)
        column.addWidget(value)
        row.addLayout(column)
        return value

    def refresh(self):
        try:
            self.instance_manager.reload()
            self.instances = self.instance_manager.get_instances()
        except (OSError, ValueError, RuntimeError):
            logger.warning("Could not load instances for home page", exc_info=True)
            self.instances = []
        if not self.instances:
            self.active_instance_id = None
            self.content_stack.setCurrentIndex(0)
            return
        ids = {item.get("id") for item in self.instances}
        if self.active_instance_id not in ids:
            recent = max(self.instances, key=lambda item: item.get("last_played_at") or item.get("created_at") or "")
            self.active_instance_id = recent.get("id")
        self.instance_picker.blockSignals(True)
        self.instance_picker.clear()
        for item in self.instances:
            self.instance_picker.addItem(item.get("name") or "Без названия", item.get("id"))
        for index in range(self.instance_picker.count()):
            if self.instance_picker.itemData(index) == self.active_instance_id:
                self.instance_picker.setCurrentIndex(index)
                break
        self.instance_picker.blockSignals(False)
        self.instance_picker.setVisible(len(self.instances) > 1)
        self.content_stack.setCurrentIndex(1)
        self._update_instance()

    def _select_instance(self, index):
        if index < 0:
            return
        self.active_instance_id = self.instance_picker.itemData(index)
        self.set_launch_state("ready")
        self._update_instance()

    def _active_instance(self):
        return next((item for item in self.instances if item.get("id") == self.active_instance_id), None)

    def set_active_instance(self, instance):
        self.active_instance_id = (instance or {}).get("id")
        self.refresh()

    def _update_instance(self):
        instance = self._active_instance()
        if not instance:
            return
        loader = str(instance.get("loader") or "vanilla")
        loader_label = loader.capitalize()
        if loader.lower() != "vanilla" and instance.get("loader_version"):
            loader_label += f" {instance['loader_version']}"
        count = _mod_count(instance)
        self.instance_title.setText(instance.get("name") or "Без названия")
        self.instance_meta.setText(f"Minecraft {instance.get('minecraft_version') or '—'}  ·  {loader_label}")
        self.last_played_label.setText(_last_played(instance.get("last_played_at")))
        self.mods_label.setText(f"{count} установлено" if count else "Без модов")

    def _play(self):
        instance = self._active_instance()
        if instance and self.launch_state not in {"preparing", "checking", "installing", "launching"}:
            self.play_requested.emit(instance)

    def set_launch_state(self, state, detail=""):
        labels = {
            "ready": ("ИГРАТЬ", "Готова к запуску", "Нажмите, чтобы открыть Minecraft"),
            "preparing": ("ПОДГОТОВКА", "Подготовка сборки", "Проверяем файлы и параметры"),
            "checking": ("ПРОВЕРКА", "Проверка файлов", "Это может занять немного времени"),
            "installing": ("УСТАНОВКА", "Установка и обновление", "Загружаем необходимые файлы"),
            "launching": ("ЗАПУСК", "Запускаем Minecraft", "Почти готово"),
            "running": ("ИГРА ЗАПУЩЕНА", "Minecraft работает", "Можно вернуться к лаунчеру"),
            "error": ("ПОВТОРИТЬ", "Не удалось запустить", "Проверьте сообщение об ошибке"),
        }
        self.launch_state = state if state in labels else "preparing"
        button, title, default_detail = labels[self.launch_state]
        busy = self.launch_state in {"preparing", "checking", "installing", "launching"}
        self.play_button.setText(button)
        self.play_button.setEnabled(not busy and self.launch_state != "running")
        self.instance_picker.setEnabled(not busy)
        self.state_title.setText(title)
        self.state_detail.setText(detail or default_detail)
