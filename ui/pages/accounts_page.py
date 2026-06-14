from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from auth.account_manager import AccountManager
from core.skin_manager import SkinError, SkinManager
from ui.components.skin_preview import SkinFaceWidget


class AccountsPage(QWidget):
    account_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.manager = AccountManager()
        self.skins = SkinManager()
        self.active_account = None
        self.active_skin = None

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(28, 22, 28, 18)
        self.root_layout.setSpacing(18)

        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Аккаунты и персонаж")
        title.setObjectName("PageTitle")

        subtitle = QLabel("Offline-профили, локальная библиотека скинов и предпросмотр персонажа прямо в Nexus Launcher.")
        subtitle.setObjectName("MutedText")
        subtitle.setWordWrap(True)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.active_badge = QLabel("• OFFLINE")
        self.active_badge.setObjectName("StatusBadge")

        header.addLayout(title_box, 1)
        header.addWidget(self.active_badge, 0, Qt.AlignTop)

        self.root_layout.addLayout(header)
        self.root_layout.addWidget(self.create_skin_studio_panel())
        self.root_layout.addWidget(self.create_providers_panel())

        content = QHBoxLayout()
        content.setSpacing(16)
        content.addWidget(self.create_accounts_panel(), 1)
        content.addWidget(self.create_skins_panel(), 2)

        self.root_layout.addLayout(content, 1)

    def create_skin_studio_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Card")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(18)

        self.preview = SkinFaceWidget(118)
        layout.addWidget(self.preview, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)

        self.skin_title = QLabel("Персонаж NexusPlayer")
        self.skin_title.setObjectName("SectionTitle")

        self.skin_subtitle = QLabel("Скин не выбран. Загрузи PNG-скин Minecraft и привяжи его к активному профилю.")
        self.skin_subtitle.setObjectName("MutedText")
        self.skin_subtitle.setWordWrap(True)

        model_row = QHBoxLayout()

        model_label = QLabel("Модель рук:")
        model_label.setObjectName("MutedText")

        self.model_combo = QComboBox()
        self.model_combo.addItem("Авто", "auto")
        self.model_combo.addItem("Classic / Steve", "classic")
        self.model_combo.addItem("Slim / Alex", "slim")
        self.model_combo.setObjectName("Input")

        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo)
        model_row.addStretch(1)

        buttons = QHBoxLayout()

        upload_btn = QPushButton("+ Загрузить PNG-скин")
        upload_btn.setObjectName("PrimaryButton")
        upload_btn.clicked.connect(self.upload_skin)

        clear_btn = QPushButton("Убрать с профиля")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self.clear_active_skin)

        folder_btn = QPushButton("Папка skins")
        folder_btn.setObjectName("SecondaryButton")
        folder_btn.clicked.connect(self.open_skins_folder)

        buttons.addWidget(upload_btn)
        buttons.addWidget(clear_btn)
        buttons.addWidget(folder_btn)
        buttons.addStretch(1)

        note = QLabel("Важно: сейчас скин хранится и показывается внутри лаунчера. Для отображения в самой игре через Offline-профиль нужен отдельный skin-server/authlib или вход Ely.by/Microsoft.")
        note.setObjectName("MutedText")
        note.setWordWrap(True)

        info.addWidget(self.skin_title)
        info.addWidget(self.skin_subtitle)
        info.addLayout(model_row)
        info.addLayout(buttons)
        info.addWidget(note)

        layout.addLayout(info, 1)
        return panel

    def create_providers_panel(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("Card")

        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        layout.addWidget(self.provider_card(
            title="Offline профиль",
            badge="LOCAL",
            description="Локальный профиль для тестов и запуска без авторизации.",
            primary_text="+ Добавить Offline",
            secondary_text="Скопировать UUID",
            primary_action=self.add_offline_account,
            secondary_action=self.copy_active_uuid,
        ))

        layout.addWidget(self.provider_card(
            title="Microsoft",
            badge="SOON",
            description="После OAuth можно будет загружать скин в официальный профиль Minecraft.",
            primary_text="Скоро",
            secondary_text="Что нужно?",
            primary_action=self.microsoft_stub,
            secondary_action=self.microsoft_info,
        ))

        layout.addWidget(self.provider_card(
            title="Ely.by",
            badge="SOON",
            description="После подключения Ely.by можно будет использовать их систему скинов.",
            primary_text="Скоро",
            secondary_text="Открыть сайт",
            primary_action=self.ely_stub,
            secondary_action=self.open_ely_site,
        ))

        return wrap

    def provider_card(self, title, badge, description, primary_text, secondary_text, primary_action, secondary_action):
        card = QFrame()
        card.setObjectName("MiniCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)

        top = QHBoxLayout()

        name = QLabel(title)
        name.setObjectName("CardTitle")

        badge_label = QLabel(badge)
        badge_label.setObjectName("SmallBadge")

        top.addWidget(name)
        top.addStretch(1)
        top.addWidget(badge_label)

        desc = QLabel(description)
        desc.setObjectName("MutedText")
        desc.setWordWrap(True)

        buttons = QHBoxLayout()

        primary = QPushButton(primary_text)
        primary.setObjectName("PrimaryButton")
        primary.clicked.connect(primary_action)

        secondary = QPushButton(secondary_text)
        secondary.setObjectName("SecondaryButton")
        secondary.clicked.connect(secondary_action)

        buttons.addWidget(primary)
        buttons.addWidget(secondary)

        layout.addLayout(top)
        layout.addWidget(desc, 1)
        layout.addLayout(buttons)

        return card

    def create_accounts_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Card")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()

        title = QLabel("Мои профили")
        title.setObjectName("SectionTitle")

        self.accounts_count = QLabel("0")
        self.accounts_count.setObjectName("MutedText")

        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(self.accounts_count)

        layout.addLayout(top)

        self.accounts_scroll = QScrollArea()
        self.accounts_scroll.setWidgetResizable(True)
        self.accounts_scroll.setFrameShape(QFrame.NoFrame)

        self.accounts_container = QWidget()
        self.accounts_layout = QVBoxLayout(self.accounts_container)
        self.accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.accounts_layout.setSpacing(10)

        self.accounts_scroll.setWidget(self.accounts_container)
        layout.addWidget(self.accounts_scroll, 1)

        return panel

    def create_skins_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Card")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()

        title = QLabel("Библиотека скинов")
        title.setObjectName("SectionTitle")

        self.skins_count = QLabel("0")
        self.skins_count.setObjectName("MutedText")

        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(self.skins_count)

        layout.addLayout(top)

        self.skins_scroll = QScrollArea()
        self.skins_scroll.setWidgetResizable(True)
        self.skins_scroll.setFrameShape(QFrame.NoFrame)

        self.skins_container = QWidget()
        self.skins_grid = QGridLayout(self.skins_container)
        self.skins_grid.setContentsMargins(0, 0, 0, 0)
        self.skins_grid.setSpacing(12)

        self.skins_scroll.setWidget(self.skins_container)
        layout.addWidget(self.skins_scroll, 1)

        return panel

    def refresh_all(self):
        self.active_account = self.manager.get_active_account()
        self.active_skin = self.skins.get_account_skin(self.active_account)

        self.refresh_header()
        self.refresh_accounts()
        self.refresh_skins()

    def refresh_header(self):
        account = self.active_account

        if not account:
            self.preview.set_skin(None, "OFF")
            self.active_badge.setText("• OFFLINE")
            return

        username = account.get("username") or account.get("display_name") or "NexusPlayer"
        provider = self.manager.format_provider(account.get("provider", "offline")).upper()

        self.active_badge.setText(f"• {provider}: {username}")

        if self.active_skin:
            self.preview.set_skin(self.active_skin.get("path"), username)
            self.skin_title.setText(f"Персонаж {username}")

            model = account.get("skin_model") or self.active_skin.get("model", "auto")
            self.skin_subtitle.setText(
                f"Активный скин: {self.active_skin.get('name', 'Custom skin')} • "
                f"{self.active_skin.get('width', '?')}x{self.active_skin.get('height', '?')} • model: {model}"
            )

            idx = self.model_combo.findData(model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        else:
            self.preview.set_skin(None, username)
            self.skin_title.setText(f"Персонаж {username}")
            self.skin_subtitle.setText("Скин не выбран. Загрузи PNG-скин Minecraft и привяжи его к активному профилю.")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def refresh_accounts(self):
        self.clear_layout(self.accounts_layout)

        accounts = self.manager.list_accounts()
        active_id = self.active_account.get("id") if self.active_account else None

        self.accounts_count.setText(f"{len(accounts)} профилей")

        for account in accounts:
            self.accounts_layout.addWidget(self.account_row(account, active_id))

        self.accounts_layout.addStretch(1)

    def refresh_skins(self):
        self.clear_layout(self.skins_grid)

        skins = self.skins.list_skins()
        self.skins_count.setText(f"{len(skins)} скинов")

        if not skins:
            empty = QLabel("Скинов пока нет. Нажми «Загрузить PNG-скин» выше.")
            empty.setObjectName("MutedText")
            empty.setAlignment(Qt.AlignCenter)
            self.skins_grid.addWidget(empty, 0, 0)
            return

        for i, skin in enumerate(skins):
            self.skins_grid.addWidget(self.skin_card(skin), i // 2, i % 2)

    def account_row(self, account: dict, active_id: str | None) -> QWidget:
        row = QFrame()
        row.setObjectName("AccountRowActive" if account.get("id") == active_id else "AccountRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        skin = self.skins.get_account_skin(account)

        avatar = SkinFaceWidget(72)
        avatar.set_skin(skin.get("path") if skin else None, account.get("username", "OFF"))

        info = QVBoxLayout()

        name = QLabel(account.get("display_name") or account.get("username") or "NexusPlayer")
        name.setObjectName("CardTitle")

        meta = QLabel(self.manager.status_text(account))
        meta.setObjectName("MutedText")

        skin_text = QLabel("Скин: " + (skin.get("name") if skin else "не выбран"))
        skin_text.setObjectName("MutedText")

        info.addWidget(name)
        info.addWidget(meta)
        info.addWidget(skin_text)

        set_btn = QPushButton("Активировать")
        set_btn.setObjectName("SecondaryButton")
        set_btn.setEnabled(account.get("id") != active_id)
        set_btn.clicked.connect(lambda: self.set_active(account.get("id")))

        del_btn = QPushButton("Удалить")
        del_btn.setObjectName("DangerButton")
        del_btn.clicked.connect(lambda: self.delete_account(account.get("id")))

        layout.addWidget(avatar)
        layout.addLayout(info, 1)
        layout.addWidget(set_btn)
        layout.addWidget(del_btn)

        return row

    def skin_card(self, skin: dict) -> QWidget:
        card = QFrame()
        card.setObjectName("SkinCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()

        preview = SkinFaceWidget(76)
        preview.set_skin(skin.get("path"), skin.get("name", "skin"))

        info = QVBoxLayout()

        name = QLabel(skin.get("name", "Custom skin"))
        name.setObjectName("CardTitle")

        meta = QLabel(f"{skin.get('width', '?')}x{skin.get('height', '?')} • {skin.get('model', 'auto')}")
        meta.setObjectName("MutedText")

        info.addWidget(name)
        info.addWidget(meta)

        top.addWidget(preview)
        top.addLayout(info, 1)

        layout.addLayout(top)

        buttons = QHBoxLayout()

        apply_btn = QPushButton("Применить")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.clicked.connect(lambda: self.apply_skin(skin.get("id")))

        open_btn = QPushButton("Файл")
        open_btn.setObjectName("SecondaryButton")
        open_btn.clicked.connect(lambda: self.open_file(skin.get("path")))

        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(lambda: self.delete_skin(skin.get("id")))

        buttons.addWidget(apply_btn)
        buttons.addWidget(open_btn)
        buttons.addWidget(delete_btn)

        layout.addLayout(buttons)

        return card

    def upload_skin(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите PNG-скин Minecraft",
            str(Path.home() / "Downloads"),
            "Minecraft skin (*.png);;PNG (*.png)",
        )

        if not file_path:
            return

        default_name = Path(file_path).stem
        name, ok = QInputDialog.getText(self, "Название скина", "Как назвать скин?", text=default_name)

        if not ok:
            return

        try:
            skin = self.skins.import_skin(
                file_path,
                name=name,
                model=self.model_combo.currentData() or "auto",
            )

            if self.active_account:
                self.skins.set_account_skin(
                    self.active_account.get("id"),
                    skin.get("id"),
                    self.model_combo.currentData() or "auto",
                )

            self.refresh_all()
            QMessageBox.information(self, "Скин загружен", "Скин добавлен в библиотеку и привязан к активному профилю.")

        except SkinError as e:
            QMessageBox.warning(self, "Не удалось загрузить скин", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить скин:\n{e}")

    def apply_skin(self, skin_id: str):
        if not self.active_account:
            QMessageBox.warning(self, "Нет активного аккаунта", "Сначала создай или выбери профиль.")
            return

        try:
            account = self.skins.set_account_skin(
                self.active_account.get("id"),
                skin_id,
                self.model_combo.currentData() or "auto",
            )

            self.refresh_all()
            self.account_changed.emit(account)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def clear_active_skin(self):
        if not self.active_account:
            return

        account = self.skins.clear_account_skin(self.active_account.get("id"))
        self.refresh_all()

        if account:
            self.account_changed.emit(account)

    def delete_skin(self, skin_id: str):
        result = QMessageBox.question(
            self,
            "Удалить скин?",
            "Удалить скин из локальной библиотеки Nexus?",
        )

        if result != QMessageBox.Yes:
            return

        self.skins.delete_skin(skin_id)
        self.refresh_all()

    def open_skins_folder(self):
        path = str(self.skins.skins_dir)

        if os.name == "nt":
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])

    def open_file(self, path: str | None):
        if not path:
            return

        p = Path(path)

        if not p.exists():
            QMessageBox.warning(self, "Файл не найден", "Файл скина не найден.")
            return

        if os.name == "nt":
            os.startfile(str(p.parent))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(p.parent)])

    def add_offline_account(self):
        name, ok = QInputDialog.getText(self, "Offline профиль", "Введите никнейм:")

        if not ok:
            return

        account = self.manager.create_offline_account(name, make_active=True)
        self.refresh_all()
        self.account_changed.emit(account)

    def set_active(self, account_id: str):
        account = self.manager.set_active_account(account_id)
        self.refresh_all()
        self.account_changed.emit(account)

    def delete_account(self, account_id: str):
        accounts = self.manager.list_accounts()

        if len(accounts) <= 1:
            QMessageBox.information(self, "Нельзя удалить", "Должен остаться хотя бы один профиль.")
            return

        result = QMessageBox.question(
            self,
            "Удалить аккаунт?",
            "Удалить выбранный профиль из Nexus Launcher?",
        )

        if result != QMessageBox.Yes:
            return

        self.manager.delete_account(account_id)
        self.refresh_all()

        active = self.manager.get_active_account()
        if active:
            self.account_changed.emit(active)

    def copy_active_uuid(self):
        account = self.manager.get_active_account()

        if not account:
            return

        QApplication.clipboard().setText(str(account.get("uuid", "")))
        QMessageBox.information(self, "Скопировано", "UUID активного профиля скопирован.")

    def microsoft_stub(self):
        QMessageBox.information(
            self,
            "Microsoft skins",
            "После подключения Microsoft OAuth здесь появится загрузка скина в официальный профиль Minecraft.",
        )

    def microsoft_info(self):
        QMessageBox.information(
            self,
            "Что нужно для Microsoft",
            "Нужен вход Microsoft OAuth, Minecraft Services token и вызов profile/skin API. Пока лаунчер сохраняет локальный скин и preview.",
        )

    def ely_stub(self):
        QMessageBox.information(
            self,
            "Ely.by skins",
            "После подключения Ely.by можно будет связать локальный скин с Ely-профилем или skin-server.",
        )

    def open_ely_site(self):
        import webbrowser
        webbrowser.open("https://ely.by/")

    def refresh(self):
        self.refresh_all()
