import os
import traceback
from pathlib import Path

from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QScrollArea,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QProgressDialog,
)

try:
    from core.instance_manager import get_instance_manager
except Exception:
    from core.instance_manager import InstanceManager

    def get_instance_manager():
        return InstanceManager()

from core.launcher import Launcher
from core.download_manager import DownloadManager


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()
        child_layout = item.layout()

        if widget:
            widget.deleteLater()

        if child_layout:
            clear_layout(child_layout)


class LaunchWorker(QThread):
    status = Signal(str)
    progress = Signal(int)
    maximum = Signal(int)
    finished_ok = Signal()
    failed = Signal(str, str)

    def __init__(self, instance):
        super().__init__()
        self.instance = instance
        self.download_manager = DownloadManager()
        self.download_task_id = None

    def run(self):
        try:
            instance_name = self.instance.get("name", "Minecraft")
            self.download_task_id = self.download_manager.start_task(
                kind="minecraft",
                title=f"Запуск Minecraft: {instance_name}",
                subtitle=f'{self.instance.get("minecraft_version", "unknown")} • {self.instance.get("loader", "vanilla")}',
                total=100,
                metadata={
                    "instance_id": self.instance.get("id"),
                    "instance_name": instance_name,
                },
            )

            def emit_status(text):
                self.download_manager.update_task(self.download_task_id, status=str(text))
                self.status.emit(str(text))

            def emit_progress(value):
                try:
                    progress = int(value or 0)
                except Exception:
                    progress = 0

                self.download_manager.update_task(self.download_task_id, progress=progress)
                self.progress.emit(progress)

            def emit_maximum(value):
                self.maximum.emit(int(value or 0))

            callback = {
                "setStatus": emit_status,
                "setProgress": emit_progress,
                "setMax": emit_maximum,
            }

            try:
                launcher = Launcher(callback=callback)
            except TypeError:
                launcher = Launcher()

                if hasattr(launcher, "callback"):
                    launcher.callback = callback

            try:
                launcher.launch_instance(self.instance, callback=callback)
            except TypeError:
                launcher.launch_instance(self.instance)

            self.download_manager.finish_task(self.download_task_id, status="Minecraft запущен")
            self.finished_ok.emit()

        except Exception as error:
            self.download_manager.fail_task(self.download_task_id, str(error), status="Ошибка запуска")
            self.failed.emit(str(error), traceback.format_exc())


class CreateInstanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Создать сборку")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Survival 1.20.1")

        self.version_combo = QComboBox()
        self.version_combo.addItems([
            "1.20.1",
            "1.20.4",
            "1.20.6",
            "1.21",
            "1.21.1",
            "1.19.2",
            "1.18.2",
            "1.16.5",
            "1.12.2",
        ])

        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["vanilla", "fabric", "forge", "neoforge", "quilt"])

        form.addRow("Название:", self.name_input)
        form.addRow("Версия:", self.version_combo)
        form.addRow("Loader:", self.loader_combo)

        buttons = QHBoxLayout()

        cancel = QPushButton("Отмена")
        cancel.setObjectName("SecondaryButton")
        cancel.clicked.connect(self.reject)

        create = QPushButton("Создать")
        create.setObjectName("PrimaryButton")
        create.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(create)

        layout.addLayout(form)
        layout.addLayout(buttons)

    def get_data(self):
        name = self.name_input.text().strip() or f"Minecraft {self.version_combo.currentText()}"

        return {
            "name": name,
            "minecraft_version": self.version_combo.currentText(),
            "loader": self.loader_combo.currentText(),
        }


class InstancesPage(QWidget):
    instance_details_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        self.instance_manager = get_instance_manager()
        self.last_launched = None
        self.launch_worker = None
        self.progress_dialog = None

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(18)

        top = QHBoxLayout()

        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        title = QLabel("Сборки")
        title.setObjectName("PageTitle")

        desc = QLabel("Создание, запуск и настройка Minecraft-сборок")
        desc.setObjectName("PageDescription")

        title_block.addWidget(title)
        title_block.addWidget(desc)

        create_button = QPushButton("+ Создать сборку")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(self.open_create_dialog)

        top.addLayout(title_block)
        top.addStretch()
        top.addWidget(create_button)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Поиск сборки...")
        self.search_input.textChanged.connect(self.refresh_instances)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("ScrollArea")

        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(14)

        self.scroll.setWidget(self.container)

        root.addLayout(top)
        root.addWidget(self.search_input)
        root.addWidget(self.scroll)

        self.refresh_instances()

    def get_instances(self):
        try:
            if hasattr(self.instance_manager, "reload"):
                self.instance_manager.reload()

            return self.instance_manager.get_instances()
        except Exception:
            return []

    def refresh_instances(self):
        clear_layout(self.cards_layout)

        query = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        instances = self.get_instances()

        if query:
            instances = [
                item for item in instances
                if query in item.get("name", "").lower()
            ]

        if not instances:
            empty = QLabel("Сборок пока нет. Нажми «Создать сборку».")
            empty.setObjectName("PanelText")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(220)

            self.cards_layout.addWidget(empty)
            self.cards_layout.addStretch()
            return

        for instance in instances:
            self.cards_layout.addWidget(self.create_instance_card(instance))

        self.cards_layout.addStretch()

    def create_instance_card(self, instance):
        card = QFrame()
        card.setObjectName("InstanceCard")
        card.setMinimumHeight(170)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()

        name_block = QVBoxLayout()
        name_block.setSpacing(5)

        title = QLabel(instance.get("name", "Без названия"))
        title.setObjectName("InstanceTitle")

        ram = instance.get("ram_mb") or instance.get("ram") or 4096

        meta = QLabel(
            f'Minecraft {instance.get("minecraft_version", "unknown")} • '
            f'{instance.get("loader", "vanilla")} • {ram} MB'
        )
        meta.setObjectName("InstanceMeta")

        name_block.addWidget(title)
        name_block.addWidget(meta)

        top.addLayout(name_block)
        top.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(10)

        play = QPushButton("▶ Играть")
        play.setObjectName("PrimaryButton")
        play.clicked.connect(lambda: self.launch_instance(instance))

        details = QPushButton("Подробнее")
        details.setObjectName("SecondaryButton")
        details.clicked.connect(lambda: self.instance_details_requested.emit(instance))

        folder = QPushButton("Папка")
        folder.setObjectName("SecondaryButton")
        folder.clicked.connect(lambda: self.open_instance_folder(instance))

        delete = QPushButton("Удалить")
        delete.setObjectName("DangerButton")
        delete.clicked.connect(lambda: self.delete_instance(instance))

        actions.addWidget(play)
        actions.addWidget(details)
        actions.addWidget(folder)
        actions.addWidget(delete)

        layout.addLayout(top)
        layout.addStretch()
        layout.addLayout(actions)

        return card

    def open_create_dialog(self):
        dialog = CreateInstanceDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        try:
            try:
                self.instance_manager.create_instance(
                    data["name"],
                    data["minecraft_version"],
                    data["loader"],
                )
            except TypeError:
                self.instance_manager.create_instance(data)

            self.refresh_instances()

        except Exception as error:
            QMessageBox.critical(self, "Ошибка создания", str(error))

    def launch_instance(self, instance):
        if self.launch_worker and self.launch_worker.isRunning():
            QMessageBox.information(self, "Запуск уже идёт", "Дождись завершения текущего запуска.")
            return

        self.last_launched = instance

        self.progress_dialog = QProgressDialog(
            "Подготовка запуска...",
            "Скрыть",
            0,
            100,
            self,
        )
        self.progress_dialog.setWindowTitle("Запуск Minecraft")
        self.progress_dialog.setMinimumWidth(520)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setWindowModality(Qt.NonModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        self.launch_worker = LaunchWorker(instance)
        self.launch_worker.status.connect(self.on_launch_status)
        self.launch_worker.progress.connect(self.on_launch_progress)
        self.launch_worker.maximum.connect(self.on_launch_maximum)
        self.launch_worker.finished_ok.connect(self.on_launch_finished)
        self.launch_worker.failed.connect(self.on_launch_error)
        self.launch_worker.start()

    def on_launch_status(self, text):
        if self.progress_dialog:
            self.progress_dialog.setLabelText(str(text))

    def on_launch_maximum(self, value):
        if not self.progress_dialog:
            return

        value = int(value or 0)

        if value <= 0:
            self.progress_dialog.setRange(0, 0)
        else:
            self.progress_dialog.setRange(0, value)

    def on_launch_progress(self, value):
        if self.progress_dialog:
            self.progress_dialog.setValue(int(value or 0))

    def on_launch_finished(self):
        if self.progress_dialog:
            self.progress_dialog.setRange(0, 100)
            self.progress_dialog.setValue(100)
            self.progress_dialog.setLabelText("Minecraft запущен.")
            self.progress_dialog.close()
            self.progress_dialog = None

        self.refresh_instances()

    def on_launch_error(self, error_text, details):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("Ошибка запуска")
        box.setText("Не удалось выполнить действие.")
        box.setInformativeText(str(error_text))
        box.setDetailedText(str(details))
        box.exec()

    def open_instance_folder(self, instance):
        path = Path(instance.get("path") or instance.get("instance_dir") or "")

        if not path.exists():
            QMessageBox.warning(self, "Папка не найдена", str(path))
            return

        os.startfile(str(path))

    def delete_instance(self, instance):
        result = QMessageBox.question(
            self,
            "Удалить сборку?",
            f'Удалить сборку «{instance.get("name", "Без названия")}»?'
        )

        if result != QMessageBox.Yes:
            return

        try:
            if hasattr(self.instance_manager, "delete_instance"):
                self.instance_manager.delete_instance(instance.get("id"))
            else:
                path = Path(instance.get("path") or "")
                if path.exists():
                    import shutil
                    shutil.rmtree(path)

            self.refresh_instances()
        except Exception as error:
            QMessageBox.critical(self, "Ошибка удаления", str(error))
