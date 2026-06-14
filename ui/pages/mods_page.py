import hashlib
import json
import re
import traceback
import webbrowser
from pathlib import Path

import requests
from core.download_manager import DownloadManager
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QMessageBox,
    QProgressDialog,
    QDialog,
    QTextEdit,
)

try:
    from core.instance_manager import get_instance_manager
except Exception:
    from core.instance_manager import InstanceManager

    def get_instance_manager():
        return InstanceManager()


MODRINTH_API = "https://api.modrinth.com/v2"
USER_AGENT = "NexusLauncher/0.5.0 (Minecraft Launcher)"
CACHE_DIR = Path.cwd() / "storage" / "modrinth_cache" / "images"


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()
        child_layout = item.layout()

        if widget:
            widget.deleteLater()

        if child_layout:
            clear_layout(child_layout)


def fmt_num(value):
    try:
        value = int(value)
    except Exception:
        return "0"

    return f"{value:,}".replace(",", " ")


def safe_filename(name):
    name = name or "mod.jar"
    return re.sub(r'[<>:"/\\\\|?*]', "_", name)


def cache_key(url):
    return hashlib.sha1(str(url).encode("utf-8", errors="ignore")).hexdigest()


def read_cached_image(url):
    if not url:
        return None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{cache_key(url)}.bin"

    if path.exists():
        try:
            return path.read_bytes()
        except Exception:
            return None

    return None


def write_cached_image(url, data):
    if not url or not data:
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{cache_key(url)}.bin"

    try:
        path.write_bytes(data)
    except Exception:
        pass


def download_image_bytes(url, timeout=12):
    if not url:
        return None

    cached = read_cached_image(url)

    if cached:
        return cached

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        if "image" not in content_type.lower():
            return None

        data = response.content

        if data:
            write_cached_image(url, data)

        return data

    except Exception:
        return None


def set_label_image(label, image_bytes, size=58):
    if not image_bytes:
        label.setText("◆")
        return

    pixmap = QPixmap()

    if not pixmap.loadFromData(image_bytes):
        label.setText("◆")
        return

    pixmap = pixmap.scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )

    label.setText("")
    label.setPixmap(pixmap)


class ModrinthSearchWorker(QThread):
    success = Signal(object, int, int)
    failed = Signal(str, str)

    def __init__(self, query="", project_type="mod", offset=0, limit=24, minecraft_version=None, loader=None):
        super().__init__()

        self.query = query or ""
        self.project_type = project_type or "mod"
        self.offset = int(offset or 0)
        self.limit = int(limit or 24)
        self.minecraft_version = minecraft_version
        self.loader = loader

    def run(self):
        try:
            facets = [[f"project_type:{self.project_type}"]]

            if self.minecraft_version:
                facets.append([f"versions:{self.minecraft_version}"])

            if self.loader and self.loader.lower() not in {"vanilla", "any", "любой"}:
                facets.append([f"categories:{self.loader.lower()}"])

            params = {
                "query": self.query,
                "limit": self.limit,
                "offset": self.offset,
                "index": "downloads",
                "facets": json.dumps(facets),
            }

            response = requests.get(
                f"{MODRINTH_API}/search",
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=25,
            )
            response.raise_for_status()

            data = response.json()
            hits = data.get("hits", [])
            total_hits = int(data.get("total_hits", 0))

            prepared = []

            for hit in hits:
                item = dict(hit)
                icon_url = item.get("icon_url")
                item["_icon_bytes"] = download_image_bytes(icon_url)
                prepared.append(item)

            self.success.emit(prepared, total_hits, self.offset)

        except Exception as error:
            self.download_manager.fail_task(self.download_task_id, str(error), status="Ошибка установки мода")
            self.failed.emit(str(error), traceback.format_exc())


class ProjectDetailsWorker(QThread):
    success = Signal(object)
    failed = Signal(str, str)

    def __init__(self, project):
        super().__init__()
        self.project = project or {}

    def run(self):
        try:
            project_id = self.project.get("project_id") or self.project.get("slug")

            if not project_id:
                raise RuntimeError("У проекта нет project_id.")

            response = requests.get(
                f"{MODRINTH_API}/project/{project_id}",
                headers={"User-Agent": USER_AGENT},
                timeout=25,
            )
            response.raise_for_status()

            details = response.json()

            result = dict(self.project)
            result.update(details)

            result["_icon_bytes"] = download_image_bytes(result.get("icon_url"))

            gallery = result.get("gallery") or []
            screenshots = []

            for item in gallery[:6]:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("raw_url")
                    title = item.get("title") or item.get("description") or ""
                else:
                    url = None
                    title = ""

                data = download_image_bytes(url)

                if data:
                    screenshots.append({
                        "title": title,
                        "url": url,
                        "bytes": data,
                    })

            result["_screenshots"] = screenshots

            self.success.emit(result)

        except Exception as error:
            self.failed.emit(str(error), traceback.format_exc())


class ModInstallWorker(QThread):
    status = Signal(str)
    progress = Signal(int)
    success = Signal(str)
    failed = Signal(str, str)

    def __init__(self, project, instance):
        super().__init__()
        self.project = project or {}
        self.instance = instance or {}
        self.download_manager = DownloadManager()
        self.download_task_id = None

    def run(self):
        try:
            title = self.project.get("title") or self.project.get("slug") or "mod"

            self.download_task_id = self.download_manager.start_task(
                kind="mod",
                title=f"Установка мода: {title}",
                subtitle=f'Сборка: {self.instance.get("name", "Minecraft")}',
                total=100,
                metadata={
                    "project_id": self.project.get("project_id"),
                    "slug": self.project.get("slug"),
                    "instance_id": self.instance.get("id"),
                },
            )
            project_id = self.project.get("project_id") or self.project.get("slug")

            if not project_id:
                raise RuntimeError("У мода нет project_id.")

            minecraft_version = self.instance.get("minecraft_version")
            loader = (self.instance.get("loader") or "vanilla").lower()

            self.download_manager.update_task(self.download_task_id, status=f"Поиск версии для {title}...")
            self.status.emit(f"Поиск версии для {title}...")

            params = {}

            if minecraft_version:
                params["game_versions"] = json.dumps([minecraft_version])

            if loader and loader != "vanilla":
                params["loaders"] = json.dumps([loader])

            versions = self.fetch_versions(project_id, params)

            if not versions and minecraft_version:
                self.status.emit("Совместимая версия не найдена, пробую только версию Minecraft...")
                versions = self.fetch_versions(project_id, {
                    "game_versions": json.dumps([minecraft_version])
                })

            if not versions:
                self.status.emit("Точная совместимость не найдена, пробую последнюю доступную версию...")
                versions = self.fetch_versions(project_id, {})

            if not versions:
                raise RuntimeError(
                    f"Не найден файл для установки.\n"
                    f"Мод: {title}\n"
                    f"Minecraft: {minecraft_version}\n"
                    f"Loader: {loader}"
                )

            file_info = self.pick_file(versions)

            if not file_info:
                raise RuntimeError("В найденных версиях нет .jar файла.")

            url = file_info.get("url")

            if not url:
                raise RuntimeError("У файла нет ссылки на скачивание.")

            filename = safe_filename(file_info.get("filename") or f"{self.project.get('slug', 'mod')}.jar")

            mods_dir = self.get_mods_dir()
            mods_dir.mkdir(parents=True, exist_ok=True)

            target = mods_dir / filename

            self.download_manager.update_task(self.download_task_id, status=f"Скачивание {filename}...")
            self.status.emit(f"Скачивание {filename}...")

            with requests.get(
                url,
                stream=True,
                headers={"User-Agent": USER_AGENT},
                timeout=60,
            ) as response:
                response.raise_for_status()

                total = int(response.headers.get("content-length") or 0)
                downloaded = 0

                with open(target, "wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue

                        file.write(chunk)
                        downloaded += len(chunk)

                        if total > 0:
                            percent = int(downloaded * 100 / total)
                            self.download_manager.update_task(
                                self.download_task_id,
                                progress=percent,
                                downloaded_bytes=downloaded,
                                total_bytes=total,
                                status=f"Скачивание {filename}",
                            )
                            self.progress.emit(percent)

            self.download_manager.finish_task(self.download_task_id, status="Мод установлен")
            self.progress.emit(100)
            self.success.emit(str(target))

        except Exception as error:
            self.failed.emit(str(error), traceback.format_exc())

    def fetch_versions(self, project_id, params):
        response = requests.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=25,
        )
        response.raise_for_status()
        return response.json()

    def pick_file(self, versions):
        for version in versions:
            files = version.get("files", [])

            primary = None
            fallback = None

            for file in files:
                filename = file.get("filename", "").lower()

                if not filename.endswith(".jar"):
                    continue

                if file.get("primary"):
                    primary = file
                    break

                if fallback is None:
                    fallback = file

            if primary:
                return primary

            if fallback:
                return fallback

        return None

    def get_mods_dir(self):
        minecraft_dir = self.instance.get("minecraft_dir")

        if minecraft_dir:
            return Path(minecraft_dir) / "mods"

        instance_path = self.instance.get("path") or self.instance.get("instance_dir")

        if instance_path:
            return Path(instance_path) / ".minecraft" / "mods"

        return Path.cwd() / "mods"


class ModDetailsDialog(QDialog):
    def __init__(self, project, parent=None):
        super().__init__(parent)

        self.project = project or {}
        self.worker = None

        self.setWindowTitle(self.project.get("title") or "Modrinth")
        self.resize(860, 720)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(14)

        self.icon_label = QLabel("◆")
        self.icon_label.setObjectName("ModDetailsIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(86, 86)

        set_label_image(self.icon_label, self.project.get("_icon_bytes"), 78)

        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        self.title_label = QLabel(self.project.get("title") or self.project.get("slug") or "Unknown mod")
        self.title_label.setObjectName("PageTitle")
        self.title_label.setWordWrap(True)

        self.meta_label = QLabel(
            f'by {self.project.get("author", "unknown")}  |  '
            f'{fmt_num(self.project.get("downloads", 0))} скачиваний'
        )
        self.meta_label.setObjectName("InstanceMeta")

        title_block.addWidget(self.title_label)
        title_block.addWidget(self.meta_label)

        top.addWidget(self.icon_label)
        top.addLayout(title_block, 1)

        summary = QLabel(self.project.get("description", "Описание не найдено."))
        summary.setObjectName("PanelText")
        summary.setWordWrap(True)

        self.full_description = QTextEdit()
        self.full_description.setObjectName("ModDescriptionBox")
        self.full_description.setReadOnly(True)
        self.full_description.setPlainText("Загрузка полного описания...")
        self.full_description.setMinimumHeight(210)

        screenshots_title = QLabel("Скриншоты")
        screenshots_title.setObjectName("PanelTitle")

        self.screenshots_row = QHBoxLayout()
        self.screenshots_row.setSpacing(12)

        self.screenshots_empty = QLabel("Скриншоты загружаются...")
        self.screenshots_empty.setObjectName("PanelText")
        self.screenshots_row.addWidget(self.screenshots_empty)

        buttons = QHBoxLayout()

        open_button = QPushButton("Открыть Modrinth")
        open_button.setObjectName("SecondaryButton")
        open_button.clicked.connect(self.open_modrinth)

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("PrimaryButton")
        close_button.clicked.connect(self.accept)

        buttons.addWidget(open_button)
        buttons.addStretch()
        buttons.addWidget(close_button)

        root.addLayout(top)
        root.addWidget(summary)
        root.addWidget(self.full_description)
        root.addWidget(screenshots_title)
        root.addLayout(self.screenshots_row)
        root.addStretch()
        root.addLayout(buttons)

        self.load_details()

    def load_details(self):
        self.worker = ProjectDetailsWorker(self.project)
        self.worker.success.connect(self.on_details_loaded)
        self.worker.failed.connect(self.on_details_failed)
        self.worker.start()

    def on_details_loaded(self, data):
        set_label_image(self.icon_label, data.get("_icon_bytes"), 78)

        title = data.get("title") or self.project.get("title") or "Unknown mod"
        author = data.get("author") or self.project.get("author") or "unknown"
        downloads = data.get("downloads") or self.project.get("downloads") or 0

        self.title_label.setText(title)
        self.meta_label.setText(f"by {author}  |  {fmt_num(downloads)} скачиваний")

        body = data.get("body") or data.get("description") or "Полное описание не найдено."
        self.full_description.setPlainText(body)

        clear_layout(self.screenshots_row)

        screenshots = data.get("_screenshots") or []

        if not screenshots:
            empty = QLabel("У этого проекта нет скриншотов на Modrinth.")
            empty.setObjectName("PanelText")
            self.screenshots_row.addWidget(empty)
            self.screenshots_row.addStretch()
            return

        for shot in screenshots[:4]:
            label = QLabel()
            label.setObjectName("ModScreenshot")
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(180, 105)
            set_label_image(label, shot.get("bytes"), 170)
            self.screenshots_row.addWidget(label)

        self.screenshots_row.addStretch()

    def on_details_failed(self, error_text, details):
        self.full_description.setPlainText(
            "Не удалось загрузить подробное описание.\n\n"
            + str(error_text)
        )

        clear_layout(self.screenshots_row)
        empty = QLabel("Скриншоты не загрузились.")
        empty.setObjectName("PanelText")
        self.screenshots_row.addWidget(empty)
        self.screenshots_row.addStretch()

    def open_modrinth(self):
        slug = self.project.get("slug") or self.project.get("project_id")

        if slug:
            webbrowser.open(f"https://modrinth.com/mod/{slug}")


class ModsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.instance_manager = get_instance_manager()
        self.instances = []
        self.results = []
        self.total_hits = 0
        self.offset = 0
        self.limit = 24

        self.search_worker = None
        self.install_worker = None
        self.progress_dialog = None
        self.did_autoload = False
        self.search_busy = False
        self.current_results = []

        self.build_ui()
        self.load_instances()

    def showEvent(self, event):
        super().showEvent(event)

        if not self.did_autoload:
            self.did_autoload = True
            QTimer.singleShot(250, self.load_all_mods_first_page)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(18)

        title = QLabel("Моды")
        title.setObjectName("PageTitle")

        description = QLabel("Каталог Modrinth, поиск, иконки, описание, скриншоты и установка модов.")
        description.setObjectName("PageDescription")
        description.setWordWrap(True)

        controls = QHBoxLayout()
        controls.setSpacing(14)

        self.instance_combo = QComboBox()
        self.instance_combo.setMinimumWidth(230)

        self.type_combo = QComboBox()
        self.type_combo.addItem("mod")
        self.type_combo.setMinimumWidth(130)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("sodium, iris, jei...")
        self.query_input.returnPressed.connect(self.search_clicked)

        search_button = QPushButton("Найти")
        search_button.setObjectName("PrimaryButton")
        search_button.clicked.connect(self.search_clicked)

        controls.addWidget(self.instance_combo)
        controls.addWidget(self.type_combo)
        controls.addWidget(self.query_input, 1)
        controls.addWidget(search_button)

        self.status_label = QLabel("Популярные моды загрузятся автоматически.")
        self.status_label.setObjectName("PanelText")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("ScrollArea")

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)

        self.scroll.setWidget(self.container)

        bottom = QHBoxLayout()

        self.count_label = QLabel("")
        self.count_label.setObjectName("InstanceMeta")

        self.load_more_button = QPushButton("Загрузить ещё")
        self.load_more_button.setObjectName("SecondaryButton")
        self.load_more_button.clicked.connect(self.load_more)
        self.load_more_button.setEnabled(False)

        bottom.addWidget(self.count_label)
        bottom.addStretch()
        bottom.addWidget(self.load_more_button)

        root.addWidget(title)
        root.addWidget(description)
        root.addLayout(controls)
        root.addWidget(self.status_label)
        root.addWidget(self.scroll, 1)
        root.addLayout(bottom)

    def load_instances(self):
        self.instance_combo.clear()

        try:
            if hasattr(self.instance_manager, "reload"):
                self.instance_manager.reload()

            self.instances = self.instance_manager.get_instances()
        except Exception:
            self.instances = []

        if not self.instances:
            self.instance_combo.addItem("Нет сборок", None)
            return

        for instance in self.instances:
            name = instance.get("name", "Без названия")
            version = instance.get("minecraft_version", "unknown")
            loader = instance.get("loader", "vanilla")
            self.instance_combo.addItem(f"{name} | {version} | {loader}", instance)

    def selected_instance(self):
        data = self.instance_combo.currentData()

        if isinstance(data, dict):
            return data

        return None

    def search_clicked(self):
        self.start_search(reset=True)

    def load_all_mods_first_page(self):
        if self.search_busy:
            return

        self.start_search(reset=True, force_query="")

    def load_more(self):
        if self.search_busy:
            return

        self.start_search(reset=False)

    def start_search(self, reset=True, force_query=None):
        if self.search_worker and self.search_worker.isRunning():
            return

        if reset:
            self.offset = 0
            self.results = []
            self.current_results = []
            self.render_results()

        query = self.query_input.text().strip()

        if force_query is not None:
            query = force_query

        instance = self.selected_instance()

        minecraft_version = None
        loader = None

        if instance:
            minecraft_version = instance.get("minecraft_version")
            loader = instance.get("loader")

        self.search_busy = True
        self.status_label.setText("Загрузка модов и иконок с Modrinth...")
        self.load_more_button.setEnabled(False)

        self.search_worker = ModrinthSearchWorker(
            query=query,
            project_type=self.type_combo.currentText(),
            offset=self.offset,
            limit=self.limit,
            minecraft_version=minecraft_version,
            loader=loader,
        )
        self.search_worker.success.connect(self.on_search_success)
        self.search_worker.failed.connect(self.on_search_failed)
        self.search_worker.start()

    def on_search_success(self, hits, total_hits, offset):
        self.search_busy = False
        self.total_hits = total_hits

        if offset == 0:
            self.results = list(hits)
        else:
            self.results.extend(hits)

        self.current_results = self.results
        self.offset = len(self.results)

        self.render_results()

        self.status_label.setText(f"Показано {len(self.results)} из {self.total_hits}")
        self.count_label.setText(f"Показано {len(self.results)} из {self.total_hits}")

        self.load_more_button.setEnabled(len(self.results) < self.total_hits)

    def on_search_failed(self, error_text, details):
        self.search_busy = False
        self.status_label.setText("Ошибка загрузки Modrinth.")
        self.load_more_button.setEnabled(False)

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("Ошибка Modrinth")
        box.setText("Не удалось загрузить моды.")
        box.setInformativeText(str(error_text))
        box.setDetailedText(str(details))
        box.exec()

    def render_results(self):
        clear_layout(self.grid)

        if not self.results:
            empty = QLabel("Моды пока не загружены. Нажми «Найти» или подожди автозагрузку популярных модов.")
            empty.setObjectName("PanelText")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(260)
            self.grid.addWidget(empty, 0, 0, 1, 2)
            return

        columns = 2

        for index, project in enumerate(self.results):
            row = index // columns
            col = index % columns
            self.grid.addWidget(self.create_mod_card(project), row, col)

        self.grid.setRowStretch((len(self.results) // columns) + 1, 1)

    def create_mod_card(self, project):
        card = QFrame()
        card.setObjectName("ModResultCard")
        card.setMinimumHeight(245)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        icon_box = QLabel("◆")
        icon_box.setObjectName("ModIconImage")
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(64, 64)
        set_label_image(icon_box, project.get("_icon_bytes"), 58)

        title_block = QVBoxLayout()
        title_block.setSpacing(3)

        title = QLabel(project.get("title") or project.get("slug") or "Unknown mod")
        title.setObjectName("InstanceTitle")
        title.setWordWrap(True)

        author = QLabel(f'by {project.get("author", "unknown")}')
        author.setObjectName("InstanceMeta")

        title_block.addWidget(title)
        title_block.addWidget(author)

        top.addWidget(icon_box)
        top.addLayout(title_block, 1)

        description = QLabel(project.get("description", "Без описания"))
        description.setObjectName("PanelText")
        description.setWordWrap(True)
        description.setMinimumHeight(54)

        tags = QHBoxLayout()
        tags.setSpacing(8)

        tags.addWidget(self.tag(f'{fmt_num(project.get("downloads", 0))} скачиваний'))
        tags.addWidget(self.tag(f'{fmt_num(project.get("follows", 0))} подписчиков'))

        for category in (project.get("categories") or [])[:2]:
            tags.addWidget(self.tag(category))

        tags.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(10)

        install = QPushButton("Установить")
        install.setObjectName("PrimaryButton")
        install.clicked.connect(lambda checked=False, p=project: self.install_project(p))

        details = QPushButton("Подробнее")
        details.setObjectName("SecondaryButton")
        details.clicked.connect(lambda checked=False, p=project: self.show_details(p))

        open_link = QPushButton("Modrinth")
        open_link.setObjectName("SecondaryButton")
        open_link.clicked.connect(lambda checked=False, p=project: self.open_modrinth(p))

        actions.addWidget(install)
        actions.addWidget(details)
        actions.addWidget(open_link)
        actions.addStretch()

        layout.addLayout(top)
        layout.addWidget(description)
        layout.addLayout(tags)
        layout.addStretch()
        layout.addLayout(actions)

        return card

    def tag(self, text):
        label = QLabel(str(text))
        label.setObjectName("ModTag")
        return label

    def show_details(self, project):
        dialog = ModDetailsDialog(project, self)
        dialog.exec()

    def install_project(self, project):
        instance = self.selected_instance()

        if not instance:
            QMessageBox.warning(
                self,
                "Нет сборки",
                "Сначала создай сборку и выбери её в списке сверху."
            )
            return

        if self.install_worker and self.install_worker.isRunning():
            QMessageBox.information(self, "Установка уже идёт", "Дождись завершения текущей установки.")
            return

        self.progress_dialog = QProgressDialog(
            "Подготовка установки...",
            "Скрыть",
            0,
            100,
            self,
        )
        self.progress_dialog.setWindowTitle("Установка мода")
        self.progress_dialog.setMinimumWidth(520)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setWindowModality(Qt.NonModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        self.install_worker = ModInstallWorker(project, instance)
        self.install_worker.status.connect(self.on_install_status)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.success.connect(self.on_install_success)
        self.install_worker.failed.connect(self.on_install_failed)
        self.install_worker.start()

    def on_install_status(self, text):
        if self.progress_dialog:
            self.progress_dialog.setLabelText(str(text))

    def on_install_progress(self, value):
        if self.progress_dialog:
            self.progress_dialog.setValue(int(value or 0))

    def on_install_success(self, path):
        if self.progress_dialog:
            self.progress_dialog.setValue(100)
            self.progress_dialog.setLabelText("Мод установлен.")
            self.progress_dialog.close()
            self.progress_dialog = None

        QMessageBox.information(
            self,
            "Мод установлен",
            f"Файл установлен:\n{path}"
        )

    def on_install_failed(self, error_text, details):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("Ошибка установки")
        box.setText("Не удалось установить мод.")
        box.setInformativeText(str(error_text))
        box.setDetailedText(str(details))
        box.exec()

    def open_modrinth(self, project):
        slug = project.get("slug") or project.get("project_id")

        if not slug:
            return

        webbrowser.open(f"https://modrinth.com/mod/{slug}")
