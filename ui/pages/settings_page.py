import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QThread, Signal
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
    QComboBox,
)

from core.system_info import (
    get_pc_summary,
    format_ram_gb,
    clamp_ram_mb,
)
from core.launcher_settings import get_launcher_settings
from core.constants import APP_VERSION

try:
    from storage.paths import DATA_DIR, INSTANCES_FILE
except Exception:
    DATA_DIR = Path.cwd() / "data"

try:
    from core.java_manager import get_best_installed_java_info
except Exception:
    get_best_installed_java_info = None


class JavaCheckWorker(QThread):
    success = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            if not get_best_installed_java_info:
                self.failed.emit("Java Manager недоступен.")
                return

            info = get_best_installed_java_info()
            self.success.emit(info)
        except Exception as error:
            self.failed.emit(str(error))




class UpdateCheckWorker(QThread):
    success = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            from core.updater import fetch_latest_release
            release = fetch_latest_release()
            self.success.emit(release)
        except Exception as error:
            self.failed.emit(str(error))


class UpdateDownloadWorker(QThread):
    progress = Signal(str, int)
    success = Signal(object, object)
    failed = Signal(str)

    def __init__(self, release):
        super().__init__()
        self.release = release

    def run(self):
        try:
            from core.updater import download_asset, create_update_notes

            asset = self.release.preferred_asset
            if not asset:
                raise RuntimeError("В релизе нет подходящего .exe или .zip asset.")

            def on_progress(downloaded, total, speed):
                percent = int(downloaded / total * 100) if total else 0
                self.progress.emit(
                    f"{downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB • {speed / 1024 / 1024:.1f} MB/s"
                    if total
                    else f"{downloaded / 1024 / 1024:.1f} MB • {speed / 1024 / 1024:.1f} MB/s",
                    percent,
                )

            path = download_asset(asset, progress_callback=on_progress)
            notes = create_update_notes(self.release, path)
            self.success.emit(path, notes)
        except Exception as error:
            self.failed.emit(str(error))


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = get_launcher_settings()
        self.pc = get_pc_summary()
        self.preset_buttons = []
        self.java_worker = None
        self.update_check_worker = None
        self.update_download_worker = None
        self.latest_release = None

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
        self.root.addWidget(self.create_language_theme_panel())
        self.root.addWidget(self.create_update_panel())
        self.root.addWidget(self.create_diagnostics_panel())

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
        recommend_button.clicked.connect(lambda checked=False: self.set_ram_value(self.pc["recommended_ram_mb"]))

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

        top = QHBoxLayout()

        title = QLabel("Java")
        title.setObjectName("PanelTitle")

        check_button = QPushButton("Проверить Java")
        check_button.setObjectName("SecondaryButton")
        check_button.clicked.connect(self.refresh_java)

        top.addWidget(title)
        top.addStretch()
        top.addWidget(check_button)

        self.java_label = QLabel("Java проверится при запуске игры или по кнопке. Это ускоряет открытие лаунчера.")
        self.java_label.setObjectName("PanelText")
        self.java_label.setWordWrap(True)

        layout.addLayout(top)
        layout.addWidget(self.java_label)

        return panel

    def create_language_theme_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        title = QLabel("Язык и оформление")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        lang_row = QHBoxLayout()
        lang_label = QLabel("Язык / Language:")
        lang_label.setMinimumWidth(140)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.lang_combo, 1)
        layout.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_label = QLabel("Тема:")
        theme_label.setMinimumWidth(140)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Тёмная", "dark")
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("AMOLED", "amoled")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo, 1)
        layout.addLayout(theme_row)

        return panel



    def create_update_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title_row = QHBoxLayout()

        title = QLabel("Обновления Nexus")
        title.setObjectName("PanelTitle")

        self.update_status_label = QLabel("Проверь наличие новой версии на GitHub Releases.")
        self.update_status_label.setObjectName("PanelText")
        self.update_status_label.setWordWrap(True)

        title_row.addWidget(title)
        title_row.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(10)

        check_btn = QPushButton("Проверить обновления")
        check_btn.setObjectName("SecondaryButton")
        check_btn.clicked.connect(self.check_updates_from_settings)

        self.download_update_btn = QPushButton("Скачать обновление")
        self.download_update_btn.setObjectName("PrimaryButton")
        self.download_update_btn.setEnabled(False)
        self.download_update_btn.clicked.connect(self.download_latest_update)

        release_btn = QPushButton("Открыть GitHub Releases")
        release_btn.setObjectName("SecondaryButton")
        release_btn.clicked.connect(self.open_github_releases)

        actions.addWidget(check_btn)
        actions.addWidget(self.download_update_btn)
        actions.addWidget(release_btn)
        actions.addStretch()

        self.update_progress = QProgressBar()
        self.update_progress.setObjectName("BigProgress")
        self.update_progress.setRange(0, 100)
        self.update_progress.setValue(0)
        self.update_progress.setTextVisible(False)
        self.update_progress.setFixedHeight(8)

        layout.addLayout(title_row)
        layout.addWidget(self.update_status_label)
        layout.addLayout(actions)
        layout.addWidget(self.update_progress)

        return panel

    def check_updates_from_settings(self):
        if self.update_check_worker and self.update_check_worker.isRunning():
            return

        self.update_status_label.setText("Проверяю GitHub Releases...")
        self.update_progress.setValue(0)
        self.download_update_btn.setEnabled(False)

        self.update_check_worker = UpdateCheckWorker()
        self.update_check_worker.success.connect(self.on_update_check_success)
        self.update_check_worker.failed.connect(self.on_update_check_failed)
        self.update_check_worker.start()

    def on_update_check_success(self, release):
        self.latest_release = release

        if not release:
            self.update_status_label.setText(
                "GitHub repo для обновлений пока не настроен или релизов ещё нет. "
                "Проверь core/app_info.py: GITHUB_OWNER и GITHUB_REPO."
            )
            return

        asset_name = release.preferred_asset.name if release.preferred_asset else "asset не найден"

        if release.is_newer:
            self.update_status_label.setText(
                f"Доступна новая версия: {release.tag} / {release.name}\n"
                f"Текущая версия: {APP_VERSION}\n"
                f"Repo: {release.repo}\n"
                f"Asset: {asset_name}"
            )
            self.download_update_btn.setEnabled(bool(release.preferred_asset))
        else:
            self.update_status_label.setText(
                f"Установлена актуальная версия: {APP_VERSION}\n"
                f"Последний релиз GitHub: {release.tag}\n"
                f"Repo: {release.repo}"
            )

    def on_update_check_failed(self, error):
        self.update_status_label.setText(f"Не удалось проверить обновления: {error}")

    def download_latest_update(self):
        if not self.latest_release:
            QMessageBox.information(self, "Нет данных", "Сначала нажми «Проверить обновления».")
            return

        if self.update_download_worker and self.update_download_worker.isRunning():
            return

        self.update_status_label.setText("Скачиваю обновление...")
        self.update_progress.setValue(0)

        self.update_download_worker = UpdateDownloadWorker(self.latest_release)
        self.update_download_worker.progress.connect(self.on_update_download_progress)
        self.update_download_worker.success.connect(self.on_update_download_success)
        self.update_download_worker.failed.connect(self.on_update_download_failed)
        self.update_download_worker.start()

    def on_update_download_progress(self, text, percent):
        self.update_status_label.setText(f"Скачивание обновления: {text}")
        self.update_progress.setValue(percent)

    def on_update_download_success(self, path, notes):
        self.update_progress.setValue(100)
        self.update_status_label.setText(f"Обновление скачано:\n{path}")

        result = QMessageBox.question(
            self,
            "Обновление скачано",
            f"Файл скачан:\n{path}\n\n"
            f"Заметка:\n{notes}\n\n"
            "Открыть скачанный файл сейчас?"
        )

        if result == QMessageBox.Yes:
            from core.updater import open_downloaded_update
            open_downloaded_update(path)

    def on_update_download_failed(self, error):
        self.update_status_label.setText(f"Не удалось скачать обновление: {error}")

    def open_github_releases(self):
        from core.updater import open_release_page
        open_release_page()

    def create_diagnostics_panel(self):
        panel = QFrame()
        panel.setObjectName("DashboardPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Диагностика и папки")
        title.setObjectName("PanelTitle")

        desc = QLabel(
            "Быстрый доступ к рабочим папкам Nexus. Удобно для проверки модов, логов, "
            "сборок и ручной диагностики без поиска файлов по проводнику."
        )
        desc.setObjectName("PanelText")
        desc.setWordWrap(True)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        data_btn = QPushButton("Открыть data")
        data_btn.setObjectName("SecondaryButton")
        data_btn.clicked.connect(lambda checked=False: self.open_folder(DATA_DIR))

        instances_btn = QPushButton("Открыть сборки")
        instances_btn.setObjectName("SecondaryButton")
        instances_btn.clicked.connect(lambda checked=False: self.open_folder(DATA_DIR / "instances"))

        logs_btn = QPushButton("Открыть логи")
        logs_btn.setObjectName("SecondaryButton")
        logs_btn.clicked.connect(lambda checked=False: self.open_folder(DATA_DIR / "logs"))

        reset_btn = QPushButton("Проверить RAM ещё раз")
        reset_btn.setObjectName("PrimaryButton")
        reset_btn.clicked.connect(self.refresh)

        actions.addWidget(data_btn)
        actions.addWidget(instances_btn)
        actions.addWidget(logs_btn)
        actions.addStretch()
        actions.addWidget(reset_btn)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(actions)

        return panel

    def open_folder(self, path):
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(path))
        except Exception as error:
            QMessageBox.warning(self, "Не удалось открыть папку", str(error))


    def _load_launcher_settings_file(self):
        settings_file = DATA_DIR / "launcher_settings.json"
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            if settings_file.exists():
                return settings_file, json.loads(settings_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return settings_file, {}

    def _save_launcher_settings_value(self, key, value):
        settings_file, data = self._load_launcher_settings_file()
        data[key] = value
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _apply_theme_live(self, theme):
        window = self.window()
        if hasattr(window, "apply_theme"):
            window.apply_theme(theme)

    def _on_language_changed(self, index):
        lang = self.lang_combo.itemData(index)
        try:
            from core.i18n import set_language
            set_language(lang)
            self._save_launcher_settings_value("language", lang)
            QMessageBox.information(self, "Готово", "Язык сохранён. Некоторые тексты обновятся после перезапуска.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _on_theme_changed(self, index):
        theme = self.theme_combo.itemData(index)
        try:
            self._save_launcher_settings_value("theme", theme)
            self._apply_theme_live(theme)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

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
        # Java больше не проверяется синхронно при старте: это могло подвешивать окно.
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


    def sync_settings_combos(self):
        try:
            _, data = self._load_launcher_settings_file()
        except Exception:
            data = {}

        lang = data.get("language", "ru")
        theme = data.get("theme", "dark")

        lang_idx = self.lang_combo.findData(lang)
        if lang_idx >= 0 and self.lang_combo.currentIndex() != lang_idx:
            self.lang_combo.blockSignals(True)
            self.lang_combo.setCurrentIndex(lang_idx)
            self.lang_combo.blockSignals(False)

        theme_idx = self.theme_combo.findData(theme)
        if theme_idx >= 0 and self.theme_combo.currentIndex() != theme_idx:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(theme_idx)
            self.theme_combo.blockSignals(False)

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
        if self.java_worker and self.java_worker.isRunning():
            self.java_label.setText("Java уже проверяется...")
            return

        self.java_label.setText("Проверка Java...")
        self.java_worker = JavaCheckWorker(self)
        self.java_worker.success.connect(self.on_java_checked)
        self.java_worker.failed.connect(self.on_java_check_failed)
        self.java_worker.start()

    def on_java_checked(self, info):
        if not info:
            self.java_label.setText("Java не найдена.")
            return

        version = info.get("version") or info.get("major") or "unknown"
        self.java_label.setText(
            f"Найдена Java {version}\n"
            f"{info.get('path', 'unknown')}"
        )

    def on_java_check_failed(self, error_text):
        self.java_label.setText(f"Не удалось проверить Java:\n{error_text}")

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
        try:
            instances_file = INSTANCES_FILE
        except Exception:
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
