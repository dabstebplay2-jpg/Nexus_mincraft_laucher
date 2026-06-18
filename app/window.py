import json
from PySide6.QtCore import QTimer, QThread, Signal

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QStackedWidget,
    QMessageBox,
)

from core.constants import APP_VERSION


class PageIndex:
    HOME = 0
    INSTANCES = 1
    MODS = 2
    LIBRARY = 3
    DOWNLOADS = 4
    ACCOUNTS = 5
    SETTINGS = 6
    LOGS = 7
from storage.paths import DATA_DIR
from ui.styles import get_app_style
from ui.components.sidebar import Sidebar
from ui.components.topbar import Topbar
from ui.components.toast import Toast
from ui.pages.home_page import HomePage
from ui.pages.instances_page import InstancesPage
from ui.pages.instance_detail_page import InstanceDetailPage
from ui.pages.mods_page import ModsPage
from ui.pages.library_page import LibraryPage
from ui.pages.downloads_page import DownloadsPage
from ui.pages.accounts_page import AccountsPage
from ui.pages.logs_page import LogsPage
from ui.pages.settings_page import SettingsPage



class StartupUpdateCheckWorker(QThread):
    success = Signal(object)

    def run(self):
        try:
            from core.updater import fetch_latest_release
            self.success.emit(fetch_latest_release(timeout=6))
        except Exception:
            self.success.emit(None)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nexus Launcher")
        self.setMinimumSize(560, 420)
        self.resize(1320, 800)
        self.setStyleSheet(get_app_style())

        self.last_play_instance = None

        self.page_meta = [
            ("Главная", "Центр управления Nexus Launcher"),
            ("Сборки", "Создание, запуск и настройка Minecraft-сборок"),
            ("Моды", "Каталог Modrinth, поиск, установка и подробности модов"),
            ("Библиотека", "Установленные моды по сборкам"),
            ("Загрузки", "Центр загрузок Minecraft, модов, Java и ресурсов"),
            ("Аккаунты", "Offline, Microsoft, Ely.by профили и скины"),
            ("Настройки", "Java, RAM, сеть, папки и диагностика"),
            ("Логи", "Логи лаунчера, Minecraft и crash-отчёты"),
        ]

        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.change_page)
        self.sidebar.profile_clicked.connect(lambda: self.change_page(PageIndex.ACCOUNTS))

        if hasattr(self.sidebar, "set_disabled_pages"):
            self.sidebar.set_disabled_pages(set())

        self.content = QWidget()
        self.content.setObjectName("AppContent")

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = Topbar()
        self.topbar.search_submitted.connect(self.handle_search)
        self.topbar.play_clicked.connect(self.handle_quick_play)
        self.topbar.theme_toggle_clicked.connect(self.toggle_theme)

        self.home_page = HomePage()
        self.home_page.navigate_requested.connect(self.change_page)
        self.home_page.create_instance_requested.connect(self.open_create_instance)

        self.instances_page = InstancesPage()
        self.instances_page.instance_details_requested.connect(self.open_instance_details)

        self.instance_detail_page = InstanceDetailPage()
        self.instance_detail_page.back_clicked.connect(lambda checked=False: self.change_page(PageIndex.INSTANCES))
        self.instance_detail_page.play_clicked.connect(self.instances_page.launch_instance)

        self.mods_page = ModsPage()
        self.library_page = LibraryPage()
        self.downloads_page = DownloadsPage()
        self.accounts_page = AccountsPage()
        self.settings_page = SettingsPage()
        self.logs_page = LogsPage()

        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.instances_page)
        self.pages.addWidget(self.mods_page)
        self.pages.addWidget(self.library_page)
        self.pages.addWidget(self.downloads_page)
        self.pages.addWidget(self.accounts_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self.logs_page)
        self.pages.addWidget(self.instance_detail_page)

        self.status_bar = self.create_status_bar()

        content_layout.addWidget(self.topbar)
        content_layout.addWidget(self.pages)
        content_layout.addWidget(self.status_bar)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.content)

        self.startup_update_worker = None
        self.change_page(0)
        self.topbar.set_theme(self.current_theme())
        QTimer.singleShot(3000, self.check_updates_on_startup)




    def closeEvent(self, event):
        if self.startup_update_worker and self.startup_update_worker.isRunning():
            self.startup_update_worker.quit()
            self.startup_update_worker.wait(3000)
        super().closeEvent(event)

    def check_updates_on_startup(self):
        if self.startup_update_worker and self.startup_update_worker.isRunning():
            return

        self.startup_update_worker = StartupUpdateCheckWorker()
        self.startup_update_worker.success.connect(self.on_startup_update_checked)
        self.startup_update_worker.start()

    def on_startup_update_checked(self, release):
        if not release or not getattr(release, "is_newer", False):
            return

        asset = release.preferred_asset.name if release.preferred_asset else "asset не найден"
        source = "GitHub Releases" if getattr(release, "source", "github") == "github" else "сайт release.json"

        result = QMessageBox.question(
            self,
            "Доступно обновление Nexus",
            f"Найдена новая версия: {release.tag}\n"
            f"Текущая версия: {APP_VERSION}\n"
            f"Источник: {source}\n"
            f"Repo: {release.repo}\n"
            f"Asset: {asset}\n\n"
            "Скачать, проверить SHA256 и установить обновление?"
        )

        if result == QMessageBox.Yes:
            self.change_page(PageIndex.SETTINGS)
            if hasattr(self.settings_page, "start_update_from_release"):
                self.settings_page.start_update_from_release(release)
            elif hasattr(self.settings_page, "check_updates_from_settings"):
                self.settings_page.check_updates_from_settings()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 1040
        if hasattr(self.sidebar, "set_compact"):
            self.sidebar.set_compact(compact)
        if hasattr(self.topbar, "set_compact"):
            self.topbar.set_compact(compact)

    def current_theme(self):
        try:
            settings_file = DATA_DIR / "launcher_settings.json"
            if settings_file.exists():
                data = json.loads(settings_file.read_text(encoding="utf-8"))
                return str(data.get("theme", "dark"))
        except Exception:
            pass
        return "dark"

    def save_theme(self, theme):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            settings_file = DATA_DIR / "launcher_settings.json"
            data = {}
            if settings_file.exists():
                data = json.loads(settings_file.read_text(encoding="utf-8"))
            data["theme"] = theme
            tmp = settings_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(settings_file)
        except Exception:
            pass

    def toggle_theme(self):
        current = self.current_theme().lower()
        next_theme = "light" if current in {"dark", "amoled"} else "dark"
        self.save_theme(next_theme)
        self.apply_theme(next_theme)
        if hasattr(self.settings_page, "sync_settings_combos"):
            self.settings_page.sync_settings_combos()

    def apply_theme(self, theme=None):
        theme = theme or self.current_theme()
        self.setStyleSheet(get_app_style(theme))
        if hasattr(self.topbar, "set_theme"):
            self.topbar.set_theme(theme)

    def change_page(self, index):
        if index == PageIndex.HOME and hasattr(self.home_page, "refresh"):
            self.home_page.refresh()

        if index == PageIndex.MODS and hasattr(self.mods_page, "load_instances"):
            self.mods_page.load_instances()

        if index == PageIndex.LIBRARY and hasattr(self.library_page, "refresh"):
            self.library_page.refresh()

        if index == PageIndex.DOWNLOADS and hasattr(self.downloads_page, "refresh"):
            self.downloads_page.refresh()

        if index == PageIndex.ACCOUNTS and hasattr(self.accounts_page, "refresh"):
            self.accounts_page.refresh()

        if index == PageIndex.SETTINGS and hasattr(self.settings_page, "refresh"):
            self.settings_page.refresh()

        if index == PageIndex.LOGS and hasattr(self.logs_page, "refresh"):
            self.logs_page.refresh()

        self.pages.setCurrentIndex(index)

        if index < len(self.page_meta):
            title, subtitle = self.page_meta[index]
            self.topbar.set_page(title, subtitle)
            self.status_label.setText(f"Готово • {title}")
            self.sidebar.set_active(index)

    def open_create_instance(self):
        self.change_page(PageIndex.INSTANCES)
        self.instances_page.open_create_dialog()

    def handle_search(self, query):
        query = query.strip().lower()

        if not query:
            return

        instances = self.instances_page.instance_manager.get_instances()
        matches = [
            item for item in instances
            if query in item.get("name", "").lower()
        ]

        if matches:
            self.change_page(PageIndex.INSTANCES)
            if hasattr(self.instances_page, "search_input"):
                self.instances_page.search_input.setText(query)
                self.instances_page.refresh_instances()
            return

        self.change_page(PageIndex.MODS)

        if hasattr(self.mods_page, "query_input"):
            self.mods_page.query_input.setText(query)

        if hasattr(self.mods_page, "search_clicked"):
            self.mods_page.search_clicked()

    def handle_quick_play(self):
        instances = self.instances_page.instance_manager.get_instances()

        if not instances:
            QMessageBox.information(
                self,
                "Нет сборок",
                "Сначала создай сборку на вкладке «Сборки».",
            )
            self.change_page(PageIndex.INSTANCES)
            return

        latest = max(
            instances,
            key=lambda item: item.get("last_played_at") or item.get("created_at") or "",
        )
        self.instances_page.launch_instance(latest)

    def open_instance_details(self, instance):
        try:
            instance = instance or {}
            self.last_play_instance = instance
            self.instance_detail_page.set_instance(instance)

            detail_index = self.pages.indexOf(self.instance_detail_page)
            if detail_index >= 0:
                self.pages.setCurrentIndex(detail_index)
            else:
                self.pages.setCurrentWidget(self.instance_detail_page)

            self.topbar.set_page(
                instance.get("name", "Сборка"),
                f'Minecraft {instance.get("minecraft_version", "unknown")} • {instance.get("loader", "vanilla").capitalize()}'
            )

            self.status_label.setText(f'Открыта сборка • {instance.get("name", "Сборка")}')
            self.sidebar.set_active(PageIndex.INSTANCES)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка страницы сборки",
                f"Не удалось открыть подробности сборки.\n\n{error}",
            )
            self.change_page(PageIndex.INSTANCES)

    def show_toast(self, title, text):
        toast = Toast(self, title, text)
        toast.show_toast()

    def placeholder_page(self, title_text, description_text):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(14)

        title = QLabel(title_text)
        title.setObjectName("PageTitle")

        description = QLabel(description_text)
        description.setObjectName("PageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()

        return page

    def create_status_bar(self):
        bar = QWidget()
        bar.setObjectName("BottomStatusBar")
        bar.setFixedHeight(34)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(10)

        self.status_label = QLabel("Готово")
        self.status_label.setObjectName("BottomStatusText")

        version = QLabel(f"Nexus Launcher {APP_VERSION} • Downloads Center")
        version.setObjectName("BottomStatusText")

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(version)

        return bar
