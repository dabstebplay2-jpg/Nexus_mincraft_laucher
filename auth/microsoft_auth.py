import logging
import webbrowser

import minecraft_launcher_lib

from auth.oauth_config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_REDIRECT_URI,
    microsoft_is_configured,
)
from auth.account_manager import get_account_manager


logger = logging.getLogger(__name__)


class MicrosoftAuthService:
    def __init__(self):
        self.secure_data = None

    def ensure_configured(self):
        if not microsoft_is_configured():
            raise RuntimeError(
                "Microsoft OAuth не настроен.\n\n"
                "Нужно задать переменные окружения:\n"
                "NEXUS_MICROSOFT_CLIENT_ID\n"
                "NEXUS_MICROSOFT_REDIRECT_URI\n\n"
                "Для полноценного входа также нужен Azure App с доступом к Minecraft API."
            )

    def open_login_page(self):
        self.ensure_configured()

        self.secure_data = (
            minecraft_launcher_lib.microsoft_account.get_secure_login_data(
                MICROSOFT_CLIENT_ID,
                MICROSOFT_REDIRECT_URI,
            )
        )

        login_url = self.secure_data["url"]
        webbrowser.open(login_url)

        return login_url

    def complete_login_from_redirect_url(self, redirect_url: str):
        self.ensure_configured()

        redirect_url = str(redirect_url or "").strip()

        if not redirect_url:
            raise RuntimeError("Вставь redirect URL после входа Microsoft.")

        if not self.secure_data:
            raise RuntimeError("Сначала нажми кнопку входа Microsoft.")

        parsed = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(
            redirect_url,
            self.secure_data["state"],
        )

        auth_code = parsed["code"]
        code_verifier = self.secure_data["code_verifier"]

        login_result = minecraft_launcher_lib.microsoft_account.complete_login(
            MICROSOFT_CLIENT_ID,
            MICROSOFT_REDIRECT_URI,
            auth_code,
            code_verifier,
        )

        manager = get_account_manager()

        account = {
            "type": "microsoft",
            "username": login_result.get("name"),
            "display_name": login_result.get("name"),
            "uuid": login_result.get("id"),
            "provider": "Microsoft",
            "skins": login_result.get("skins", []),
            "capes": login_result.get("capes", []),
        }

        saved = manager.upsert_account(account)

        manager.save_tokens(
            saved["id"],
            {
                "access_token": login_result.get("access_token", ""),
                "refresh_token": login_result.get("refresh_token", ""),
            },
        )

        return saved

    def refresh_account(self, account):
        self.ensure_configured()

        manager = get_account_manager()
        tokens = manager.load_tokens(account["id"])

        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            raise RuntimeError("Refresh token отсутствует. Нужно войти заново.")

        result = minecraft_launcher_lib.microsoft_account.complete_refresh(
            MICROSOFT_CLIENT_ID,
            refresh_token,
        )

        account["username"] = result.get("name", account.get("username"))
        account["display_name"] = result.get("name", account.get("display_name"))
        account["uuid"] = result.get("id", account.get("uuid"))
        account["skins"] = result.get("skins", account.get("skins", []))
        account["capes"] = result.get("capes", account.get("capes", []))

        saved = manager.upsert_account(account)

        manager.save_tokens(
            saved["id"],
            {
                "access_token": result.get("access_token", ""),
                "refresh_token": result.get("refresh_token", refresh_token),
            },
        )

        return saved