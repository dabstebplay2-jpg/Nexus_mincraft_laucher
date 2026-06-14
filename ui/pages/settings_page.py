import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSlider,
    QProgressBar,
    QMessageBox,
    QCheckBox,
    QScrollArea,
    QGridLayout,
)

from core.system_info import (
    get_pc_summary,
    format_ram_gb,
    clamp_ram_mb,
)
from core.launcher_settings import get_launcher_settings

try:
    from storage.paths import DATA_DIR
except Exception:
    DATA_DIR = Path.cwd() / "data"

try:
    from core.java_manager import get_best_installed_java_info
except Exception:
    get_best_installed_java_info = None


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = get_launcher_settings()
        self.pc = get_pc_summary()
        self.preset_buttons = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("ScrollArea")
        self.scroll.setWidgetResizable(True)

        self.content = QWidget()
        self.content.setObjectName("SettingsContent")

        self.root = QVBoxLayout(self.content)
        self.root.setContentsMargins(36, 32, 36, 32)
        self.root.setSpacing(18)

        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll)

        self.build_ui()
        self.refresh()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_live_memory)
        self.timer.start(1500)

    def build_ui(self):
        title = QLabel("Настройки")
        title.setObjectName("PageTitle")

        description = QLabel(
            "Синхронизация с ПК: Nexus видит реальный объём ОЗУ, доступную память "
            "и позволяет выбрать RAM для Minecraft."
        )
        description.setObjectName("PageDescription")
        description.setWordWrap(True)

        self.root.addWidget(title)
        self.root.addWidget(description)

        self.root.addWidget(self.create_pc_info_panel())
        self.root.addWidget(self.create_ram_panel())
        self.root.addWidget(self.create_java_panel())

        self.root.addStretch()

    def create_pc_info_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        top = QHBoxLayout()

        title = QLabel("ПК и ресурсы")
        title.setObjectName("PanelTitle")

        self.memory_load_label = QLabel("Загрузка памяти: —")
        self.memory_load_label.setObjectName("InstanceMeta")

        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.memory_load_label)

        self.cards_grid = QGridLayout()
        self.cards_grid.setHorizontalSpacing(12)
        self.cards_grid.setVerticalSpacing(12)

        self.total_ram_card = self.create_stat_card("Всего ОЗУ", "—")
        self.used_ram_card = self.create_stat_card("Используется", "—")
        self.available_ram_card = self.create_stat_card("Доступно", "—")
        self.safe_ram_card = self.create_stat_card("Можно выделить", "—")
        self.recommended_ram_card = self.create_stat_card("Рекомендация", "—")

        self.cards_grid.addWidget(self.total_ram_card, 0, 0)
        self.cards_grid.addWidget(self.used_ram_card, 0, 1)
        self.cards_grid.addWidget(self.available_ram_card, 0, 2)
        self.cards_grid.addWidget(self.safe_ram_card, 0, 3)
        self.cards_grid.addWidget(self.recommended_ram_card, 0, 4)

        self.memory_load_bar = QProgressBar()
        self.memory_load_bar.setObjectName("BigProgress")
        self.memory_load_bar.setRange(0, 100)
        self.memory_load_bar.setTextVisible(False)
        self.memory_load_bar.setFixedHeight(8)

        layout.addLayout(top)
        layout.addLayout(self.cards_grid)
        layout.addWidget(self.memory_load_bar)

        return panel

    def create_ram_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        top = QHBoxLayout()

        title = QLabel("Оперативная память для Minecraft")
        title.setObjectName("PanelTitle")

        self.selected_ram_label = QLabel("—")
        self.selected_ram_label.setObjectName("SettingsRamValue")

        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.selected_ram_label)

        hint = QLabel(
            "Выбери RAM для Minecraft. Значение сохранится и может быть применено "
            "ко всем существующим сборкам."
        )
        hint.setObjectName("PanelText")
        hint.setWordWrap(True)

        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setObjectName("RamSlider")
        self.ram_slider.setMinimum(1024)
        self.ram_slider.setMaximum(max(2048, self.pc["safe_max_ram_mb"]))
        self.ram_slider.setSingleStep(512)
        self.ram_slider.setPageStep(1024)
        self.ram_slider.setTickInterval(2048)
        self.ram_slider.setTickPosition(QSlider.TicksBelow)
        self.ram_slider.valueChanged.connect(self.on_ram_changed)

        limits = QHBoxLayout()

        self.min_label = QLabel("1 GB")
        self.min_label.setObjectName("InstanceMeta")

        self.max_label = QLabel(self.pc["safe_max_ram_text"])
        self.max_label.setObjectName("InstanceMeta")

        limits.addWidget(self.min_label)
        limits.addStretch()
        limits.addWidget(self.max_label)

        presets_title = QLabel("Быстрый выбор")
        presets_title.setObjectName("SettingsSectionLabel")

        presets = QHBoxLayout()
        presets.setSpacing(10)

        for mb in [2048, 4096, 6144, 8192, 12288, 16384, 20480, 22528]:
            button = QPushButton(format_ram_gb(mb))
            button.setObjectName("RamPresetButton")
            button.clicked.connect(lambda checked=False, value=mb: self.set_ram_value(value))
            self.preset_buttons.append((button, mb))
            presets.addWidget(button)

        presets.addStretch()

        options_box = QFrame()
        options_box.setObjectName("SettingsOptionsBox")

        options_layout = QVBoxLayout(options_box)
        options_layout.setContentsMargins(16, 14, 16, 14)
        options_layout.setSpacing(10)

        self.override_checkbox = QCheckBox("Использовать это значение как глобальное")
        self.override_checkbox.setObjectName("SettingsCheckBox")
        self.override_checkbox.setChecked(self.settings.is_ram_override_enabled())
        self.override_checkbox.stateChanged.connect(self.on_override_changed)

        self.sync_instances_checkbox = QCheckBox("Применять RAM ко всем существующим сборкам")
        self.sync_instances_checkbox.setObjectName("SettingsCheckBox")
        self.sync_instances_checkbox.setChecked(self.settings.sync_ram_to_instances_enabled())
        self.sync_instances_checkbox.stateChanged.connect(self.on_sync_instances_changed)

        options_layout.addWidget(self.override_checkbox)
        options_layout.addWidget(self.sync_instances_checkbox)

        warning = QLabel(
            "Совет: для большинства сборок достаточно 4–8 GB. Если поставить слишком много, "
            "Java иногда может работать хуже. Для твоих 24 GB обычно комфортно 8–12 GB."
        )
        warning.setObjectName("PanelText")
        warning.setWordWrap(True)

        actions = QHBoxLayout()

        recommend_button = QPushButton("Поставить рекомендованное")
        recommend_button.setObjectName("SecondaryButton")
        recommend_button.clicked.connect(lambda: self.set_ram_value(self.pc["recommended_ram_mb"]))

        save_button = QPushButton("Сохранить и применить RAM")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_ram)

        actions.addWidget(recommend_button)
        actions.addStretch()
        actions.addWidget(save_button)

        layout.addLayout(top)
        layout.addWidget(hint)
        layout.addWidget(self.ram_slider)
        layout.addLayout(limits)
        layout.addWidget(presets_title)
        layout.addLayout(presets)
        layout.addWidget(options_box)
        layout.addWidget(warning)
        layout.addLayout(actions)

        return panel

    def create_java_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        title = QLabel("Java")
        title.setObjectName("PanelTitle")

        self.java_label = QLabel("Проверка Java...")
        self.java_label.setObjectName("PanelText")
        self.java_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.java_label)

        return panel

    def create_stat_card(self, title, value):
        card = QFrame()
        card.setObjectName("SettingsStatCard")
        card.setMinimumHeight(72)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("HeroStatTitle")

        value_label = QLabel(value)
        value_label.setObjectName("HeroStatValue")

        card.value_label = value_label

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def refresh(self):
        self.pc = get_pc_summary()

        self.ram_slider.setMaximum(max(2048, self.pc["safe_max_ram_mb"]))
        self.ram_slider.setValue(clamp_ram_mb(self.settings.get_ram_mb()))

        self.max_label.setText(self.pc["safe_max_ram_text"])

        self.update_preset_buttons()
        self.refresh_live_memory()
        self.refresh_java()
        self.on_ram_changed(self.ram_slider.value())

    def update_preset_buttons(self):
        safe_max = self.pc["safe_max_ram_mb"]

        for button, mb in self.preset_buttons:
            button.setEnabled(mb <= safe_max)

            if mb == self.settings.get_ram_mb():
                button.setProperty("selected", True)
            else:
                button.setProperty("selected", False)

            button.style().unpolish(button)
            button.style().polish(button)

    def refresh_live_memory(self):
        self.pc = get_pc_summary()

        self.total_ram_card.value_label.setText(self.pc["total_ram_text"])
        self.used_ram_card.value_label.setText(self.pc["used_ram_text"])
        self.available_ram_card.value_label.setText(self.pc["available_ram_text"])
        self.safe_ram_card.value_label.setText(self.pc["safe_max_ram_text"])
        self.recommended_ram_card.value_label.setText(self.pc["recommended_ram_text"])

        load = self.pc["memory_load_percent"]
        self.memory_load_label.setText(f"Загрузка памяти: {load}%")
        self.memory_load_bar.setValue(load)

    def refresh_java(self):
        if not get_best_installed_java_info:
            self.java_label.setText("Java Manager недоступен.")
            return

        try:
            info = get_best_installed_java_info()

            if not info:
                self.java_label.setText("Java не найдена.")
                return

            self.java_label.setText(
                f"Найдена Java {info.get('version', 'unknown')}\n"
                f"{info.get('path', 'unknown')}"
            )
        except Exception as error:
            self.java_label.setText(f"Не удалось проверить Java:\n{error}")

    def on_ram_changed(self, value):
        value = clamp_ram_mb(value)
        self.selected_ram_label.setText(format_ram_gb(value))

    def set_ram_value(self, value):
        value = clamp_ram_mb(value)
        self.ram_slider.setValue(value)
        self.on_ram_changed(value)

    def save_ram(self):
        value = clamp_ram_mb(self.ram_slider.value())
        saved = self.settings.set_ram_mb(value)

        updated = 0

        if self.settings.sync_ram_to_instances_enabled():
            updated = self.apply_ram_to_all_instances(saved)

        self.update_preset_buttons()

        QMessageBox.information(
            self,
            "RAM сохранена",
            f"Выбрано: {format_ram_gb(saved)}\n"
            f"Обновлено сборок: {updated}\n\n"
            f"Теперь существующие сборки будут запускаться с этим значением RAM."
        )

    def apply_ram_to_all_instances(self, ram_mb):
        instances_file = DATA_DIR / "instances.json"

        if not instances_file.exists():
            return 0

        try:
            data = json.loads(instances_file.read_text(encoding="utf-8"))

            if isinstance(data, dict):
                instances = data.get("instances", [])
            elif isinstance(data, list):
                instances = data
            else:
                return 0

            count = 0

            for instance in instances:
                if isinstance(instance, dict):
                    instance["ram"] = int(ram_mb)
                    count += 1

            instances_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            return count

        except Exception:
            return 0

    def on_override_changed(self):
        self.settings.set_ram_override_enabled(self.override_checkbox.isChecked())

    def on_sync_instances_changed(self):
        self.settings.set_sync_ram_to_instances(self.sync_instances_checkbox.isChecked())
