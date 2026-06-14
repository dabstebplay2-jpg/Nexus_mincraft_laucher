from PySide6.QtCore import Signal, Qt, QSize, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
)

try:
    from core.instance_manager import get_instance_manager
except Exception:
    from core.instance_manager import InstanceManager

    def get_instance_manager():
        return InstanceManager()

try:
    from core.system_info import get_pc_summary
except Exception:
    get_pc_summary = None

try:
    from core.launcher_settings import get_launcher_settings
except Exception:
    get_launcher_settings = None

try:
    from ui.icon_utils import icon
except Exception:
    icon = None


def qicon(name):
    if not icon:
        return None

    try:
        return icon(name)
    except Exception:
        return None


def format_ram_mb(mb):
    try:
        gb = int(mb) / 1024
        if abs(gb - round(gb)) < 0.05:
            return f"{int(round(gb))} GB"
        return f"{gb:.1f} GB"
    except Exception:
        return "—"


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()
        child_layout = item.layout()

        if widget is not None:
            widget.deleteLater()

        if child_layout is not None:
            clear_layout(child_layout)


class MinecraftHero(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("MinecraftHero")
        self.setMinimumHeight(250)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        w = self.width()
        h = self.height()

        for i in range(24):
            x = (i * 67) % max(w, 1)
            y = 24 + ((i * 19) % 80)
            painter.fillRect(x, y, 42, 12, QColor(90, 111, 145, 70))

        for i in range(54):
            x = (i * 31) % max(w, 1)
            base = h - 70 - ((i * 17) % 42)

            painter.fillRect(x + 8, base + 20, 8, 38, QColor(72, 45, 24, 100))
            painter.fillRect(x, base, 30, 28, QColor(22, 101, 52, 125))
            painter.fillRect(x + 5, base - 16, 22, 22, QColor(34, 197, 94, 95))

        block = 18
        top = h - 54

        colors = [
            QColor(22, 101, 52, 130),
            QColor(34, 197, 94, 90),
            QColor(75, 50, 28, 100),
            QColor(20, 83, 45, 150),
        ]

        for row in range(4):
            for col in range((w // block) + 2):
                x = col * block
                y = top + row * block + ((col + row) % 2) * 3
                painter.fillRect(x, y, block, block, colors[(row + col) % len(colors)])

        painter.fillRect(0, 0, w, h, QColor(2, 6, 23, 105))


class HomePage(QWidget):
    navigate_requested = Signal(int)
    create_instance_requested = Signal()

    def __init__(self):
        super().__init__()

        self.instance_manager = get_instance_manager()
        self.stat_value_labels = {}

        self.settings = get_launcher_settings() if get_launcher_settings else None

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        root.addWidget(self.create_hero())
        root.addWidget(self.create_download_panel())

        lower = QHBoxLayout()
        lower.setSpacing(18)

        lower.addWidget(self.create_instances_panel(), 1)
        lower.addWidget(self.create_create_panel(), 1)

        root.addLayout(lower)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_pc_stats)
        self.timer.start(1500)

        self.refresh_pc_stats()

    def refresh(self):
        self.rebuild_instances_panel()
        self.refresh_pc_stats()

    def create_hero(self):
        hero = MinecraftHero()

        layout = QVBoxLayout(hero)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        top = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(4)

        welcome = QLabel("Добро пожаловать в")
        welcome.setObjectName("HeroWelcome")

        title = QLabel('Nexus <span style="color:#22C55E;">Launcher</span>')
        title.setObjectName("HeroTitle")
        title.setTextFormat(Qt.RichText)

        subtitle = QLabel("Твоё премиальное пространство для Minecraft.")
        subtitle.setObjectName("HeroSubtitle")

        text.addWidget(welcome)
        text.addWidget(title)
        text.addWidget(subtitle)

        play = QPushButton("ИГРАТЬ")
        play.setObjectName("HeroPlayButton")

        play_icon = qicon("play")
        if play_icon:
            play.setIcon(play_icon)
            play.setIconSize(QSize(22, 22))

        play.clicked.connect(lambda: self.navigate_requested.emit(1))

        top.addLayout(text)
        top.addStretch()
        top.addWidget(play)

        stats = QHBoxLayout()
        stats.setSpacing(14)

        self.ram_card = self.create_hero_stat("ram", "Оперативная память", "—", 0, "ram")
        self.available_card = self.create_hero_stat("ram", "Доступно", "—", 0, "available")
        self.minecraft_ram_card = self.create_hero_stat("loader", "RAM для Minecraft", "—", 100, "minecraft_ram")
        self.java_card = self.create_hero_stat("java", "Java", "Eclipse Temurin 25", 100, "java")

        stats.addWidget(self.ram_card)
        stats.addWidget(self.available_card)
        stats.addWidget(self.minecraft_ram_card)
        stats.addWidget(self.java_card)
        stats.addStretch()

        layout.addStretch()
        layout.addLayout(top)
        layout.addLayout(stats)

        return hero

    def create_hero_stat(self, icon_name, title, value, progress, key):
        card = QFrame()
        card.setObjectName("HeroStatCard")
        card.setMinimumHeight(88)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        row = QHBoxLayout()

        icon_label = QLabel("◆")
        icon_label.setObjectName("HeroStatIcon")

        icon_obj = qicon(icon_name)
        if icon_obj:
            icon_label.setPixmap(icon_obj.pixmap(QSize(20, 20)))

        title_label = QLabel(title)
        title_label.setObjectName("HeroStatTitle")

        row.addWidget(icon_label)
        row.addWidget(title_label)
        row.addStretch()

        value_label = QLabel(value)
        value_label.setObjectName("HeroStatValue")
        self.stat_value_labels[key] = value_label

        bar = QProgressBar()
        bar.setObjectName("MiniProgress")
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)
        bar.setFixedHeight(7)

        card.progress_bar = bar

        layout.addLayout(row)
        layout.addWidget(value_label)
        layout.addWidget(bar)

        return card

    def refresh_pc_stats(self):
        if not get_pc_summary:
            return

        try:
            pc = get_pc_summary()

            self.stat_value_labels["ram"].setText(pc.get("hero_ram_text", "—"))
            self.stat_value_labels["available"].setText(pc.get("available_ram_text", "—"))

            if self.settings:
                self.stat_value_labels["minecraft_ram"].setText(format_ram_mb(self.settings.get_ram_mb()))
            else:
                self.stat_value_labels["minecraft_ram"].setText(pc.get("recommended_ram_text", "—"))

            self.stat_value_labels["java"].setText("Eclipse Temurin 25")

            self.ram_card.progress_bar.setValue(int(pc.get("memory_load_percent", 0)))

            total = int(pc.get("total_ram_mb", 0))
            available = int(pc.get("available_ram_mb", 0))

            if total > 0:
                self.available_card.progress_bar.setValue(int((available / total) * 100))
        except Exception:
            pass

    def create_download_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")
        panel.setMinimumHeight(92)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()

        title = QLabel("Загрузка и подготовка")
        title.setObjectName("PanelTitle")

        details = QPushButton("Подробности⌄")
        details.setObjectName("SmallGhostButton")
        details.clicked.connect(lambda: self.navigate_requested.emit(7))

        top.addWidget(title)
        top.addStretch()
        top.addWidget(details)

        bar = QProgressBar()
        bar.setObjectName("BigProgress")
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        text = QLabel("Нет активных загрузок")
        text.setObjectName("PanelText")

        layout.addLayout(top)
        layout.addWidget(bar)
        layout.addWidget(text)

        return panel

    def create_instances_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        self.instances_layout = QVBoxLayout(panel)
        self.instances_layout.setContentsMargins(20, 18, 20, 18)
        self.instances_layout.setSpacing(12)

        self.rebuild_instances_panel()

        return panel

    def rebuild_instances_panel(self):
        if not hasattr(self, "instances_layout"):
            return

        clear_layout(self.instances_layout)

        top = QHBoxLayout()

        title = QLabel("Мои сборки")
        title.setObjectName("PanelTitle")

        new_button = QPushButton("Новая сборка")
        new_button.setObjectName("SmallGhostButton")

        plus_icon = qicon("plus")
        if plus_icon:
            new_button.setIcon(plus_icon)
            new_button.setIconSize(QSize(16, 16))

        new_button.clicked.connect(self.create_instance_requested.emit)

        top.addWidget(title)
        top.addStretch()
        top.addWidget(new_button)

        self.instances_layout.addLayout(top)

        try:
            if hasattr(self.instance_manager, "reload"):
                self.instance_manager.reload()
            instances = self.instance_manager.get_instances()
        except Exception:
            instances = []

        if not instances:
            empty = QLabel("Сборок пока нет. Создай первую сборку Nexus.")
            empty.setObjectName("PanelText")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(120)
            self.instances_layout.addWidget(empty)
        else:
            for index, instance in enumerate(instances[:4]):
                self.instances_layout.addWidget(self.create_instance_row(instance, index))

        show_all = QPushButton(f"Показать все сборки ({len(instances)})")
        show_all.setObjectName("WideGhostButton")
        show_all.clicked.connect(lambda: self.navigate_requested.emit(1))

        self.instances_layout.addStretch()
        self.instances_layout.addWidget(show_all)

    def create_instance_row(self, instance, index):
        row = QFrame()
        row.setObjectName("InstanceDashboardRowActive" if index == 0 else "InstanceDashboardRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        block = QLabel("▣")
        block.setObjectName("BlockIcon")
        block.setAlignment(Qt.AlignCenter)
        block.setFixedSize(44, 44)

        icon_obj = qicon("instances")
        if icon_obj:
            block.setPixmap(icon_obj.pixmap(QSize(24, 24)))

        text = QVBoxLayout()
        text.setSpacing(2)

        name = QLabel(instance.get("name", "Без названия"))
        name.setObjectName("InstanceTitle")

        meta = QLabel(
            f'{instance.get("minecraft_version", "unknown")}  •  '
            f'{instance.get("loader", "vanilla").capitalize()}'
        )
        meta.setObjectName("InstanceMeta")

        text.addWidget(name)
        text.addWidget(meta)

        play = QPushButton()
        play.setObjectName("MiniPlayButton")
        play.setFixedSize(38, 38)

        play_icon = qicon("play")
        if play_icon:
            play.setIcon(play_icon)
            play.setIconSize(QSize(16, 16))
        else:
            play.setText("▶")

        play.clicked.connect(lambda: self.navigate_requested.emit(1))

        layout.addWidget(block)
        layout.addLayout(text)
        layout.addStretch()
        layout.addWidget(play)

        return row

    def create_create_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Создать новую сборку")
        title.setObjectName("PanelTitle")

        text = QLabel(
            "Выбери версию, loader и создай сборку на странице «Сборки». "
            "Так мы сохраняем рабочую логику создания сборок и не ломаем функционал."
        )
        text.setObjectName("PanelText")
        text.setWordWrap(True)

        button = QPushButton("Создать сборку")
        button.setObjectName("PrimaryButton")

        plus_icon = qicon("plus")
        if plus_icon:
            button.setIcon(plus_icon)
            button.setIconSize(QSize(18, 18))

        button.clicked.connect(self.create_instance_requested.emit)

        layout.addWidget(title)
        layout.addWidget(text)
        layout.addStretch()
        layout.addWidget(button)

        return panel
