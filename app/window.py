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
from ui.styles import APP_STYLE
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nexus Launcher")
        self.setMinimumSize(1280, 760)
        self.resize(1440, 860)
        self.setStyleSheet(APP_STYLE)

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

        self.home_page = HomePage()
        self.home_page.navigate_requested.connect(self.change_page)
        self.home_page.create_instance_requested.connect(self.open_create_instance)

        self.instances_page = InstancesPage()
        self.instances_page.instance_details_requested.connect(self.open_instance_details)

        self.instance_detail_page = InstanceDetailPage()
        self.instance_detail_page.back_clicked.connect(lambda: self.change_page(1))
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

        self.change_page(0)

    def change_page(self, index):
        if index == 0 and hasattr(self.home_page, "refresh"):
            self.home_page.refresh()

        if index == 2 and hasattr(self.mods_page, "load_instances"):
            self.mods_page.load_instances()

        if index == 3 and hasattr(self.library_page, "refresh"):
            self.library_page.refresh()

        if index == 4 and hasattr(self.downloads_page, "refresh"):
            self.downloads_page.refresh()

        if index == 5 and hasattr(self.accounts_page, "refresh"):
            self.accounts_page.refresh()

        if index == 6 and hasattr(self.settings_page, "refresh"):
            self.settings_page.refresh()

        if index == 7 and hasattr(self.logs_page, "refresh"):
            self.logs_page.refresh()

        self.pages.setCurrentIndex(index)

        if index < len(self.page_meta):
            title, subtitle = self.page_meta[index]
            self.topbar.set_page(title, subtitle)
            self.status_label.setText(f"Готово • {title}")
            self.sidebar.set_active(index)

    def open_create_instance(self):
        self.change_page(1)
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
            self.change_page(1)
            if hasattr(self.instances_page, "search_input"):
                self.instances_page.search_input.setText(query)
                self.instances_page.refresh_instances()
            return

        self.change_page(2)

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
            self.change_page(1)
            return

        latest = max(
            instances,
            key=lambda item: item.get("last_played_at") or item.get("created_at") or "",
        )
        self.instances_page.launch_instance(latest)

    def open_instance_details(self, instance):
        self.last_play_instance = instance
        self.instance_detail_page.set_instance(instance)
        self.pages.setCurrentWidget(self.instance_detail_page)

        self.topbar.set_page(
            instance.get("name", "Сборка"),
            f'Minecraft {instance.get("minecraft_version", "unknown")} • {instance.get("loader", "vanilla").capitalize()}'
        )

        self.status_label.setText(f'Открыта сборка • {instance.get("name", "Сборка")}')
        self.sidebar.set_active(1)

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
