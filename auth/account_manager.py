import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any


class AccountManager:
    """
    Nexus Account Core v0.7.0

    Сейчас стабильно работает Offline-профиль.
    Microsoft/Ely.by будут подключаться поверх этой архитектуры позже.
    """

    SCHEMA_VERSION = 1

    def __init__(self, data_path: str | Path | None = None):
        root = Path(__file__).resolve().parents[1]
        self.data_path = Path(data_path) if data_path else root / "data" / "accounts.json"
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_storage()

    # ---------- low level ----------

    def ensure_storage(self) -> None:
        if not self.data_path.exists():
            self._save({
                "schema_version": self.SCHEMA_VERSION,
                "active_account_id": None,
                "accounts": [],
            })
        self.ensure_default_account()

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("accounts.json is not an object")
        except Exception:
            data = {
                "schema_version": self.SCHEMA_VERSION,
                "active_account_id": None,
                "accounts": [],
            }

        data.setdefault("schema_version", self.SCHEMA_VERSION)
        data.setdefault("active_account_id", None)
        data.setdefault("accounts", [])

        if not isinstance(data["accounts"], list):
            data["accounts"] = []

        return data

    def _save(self, data: dict[str, Any]) -> None:
        tmp = self.data_path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.data_path)

    # ---------- helpers ----------

    @staticmethod
    def normalize_username(username: str) -> str:
        username = (username or "").strip()
        username = re.sub(r"[^A-Za-z0-9_]", "", username)
        username = username[:16]
        return username or "NexusPlayer"

    @staticmethod
    def make_offline_uuid(username: str) -> str:
        """
        Minecraft-compatible offline UUID:
        UUID.nameUUIDFromBytes(("OfflinePlayer:" + username).getBytes("UTF-8"))
        """
        raw = hashlib.md5(("OfflinePlayer:" + username).encode("utf-8")).digest()
        b = bytearray(raw)
        b[6] = (b[6] & 0x0F) | 0x30
        b[8] = (b[8] & 0x3F) | 0x80
        return str(uuid.UUID(bytes=bytes(b)))

    @staticmethod
    def now() -> int:
        return int(time.time())

    # ---------- public api ----------

    def ensure_default_account(self) -> dict[str, Any]:
        data = self._load()

        if data["accounts"]:
            if not data.get("active_account_id"):
                data["active_account_id"] = data["accounts"][0]["id"]
                self._save(data)
            return self.get_active_account() or data["accounts"][0]

        account = self.create_offline_account("NexusPlayer", make_active=True)
        return account

    def list_accounts(self) -> list[dict[str, Any]]:
        return list(self._load()["accounts"])

    def get_active_account(self) -> dict[str, Any] | None:
        data = self._load()
        active_id = data.get("active_account_id")

        for account in data["accounts"]:
            if account.get("id") == active_id:
                return account

        if data["accounts"]:
            data["active_account_id"] = data["accounts"][0]["id"]
            self._save(data)
            return data["accounts"][0]

        return None

    def create_offline_account(self, username: str, make_active: bool = True) -> dict[str, Any]:
        username = self.normalize_username(username)
        data = self._load()

        for account in data["accounts"]:
            if account.get("provider") == "offline" and account.get("username", "").lower() == username.lower():
                if make_active:
                    data["active_account_id"] = account["id"]
                    self._save(data)
                return account

        account_id = str(uuid.uuid4())
        created = self.now()

        account = {
            "id": account_id,
            "provider": "offline",
            "username": username,
            "display_name": username,
            "uuid": self.make_offline_uuid(username),
            "access_token": "0",
            "status": "active",
            "created_at": created,
            "updated_at": created,
            "note": "Local offline Nexus profile",
            "skin_id": None,
            "skin_path": None,
            "skin_name": None,
            "skin_model": "auto",
        }

        data["accounts"].append(account)

        if make_active or not data.get("active_account_id"):
            data["active_account_id"] = account_id

        self._save(data)
        return account

    def set_active_account(self, account_id: str) -> dict[str, Any]:
        data = self._load()

        for account in data["accounts"]:
            if account.get("id") == account_id:
                data["active_account_id"] = account_id
                self._save(data)
                return account

        raise RuntimeError("Аккаунт не найден")

    def delete_account(self, account_id: str) -> None:
        data = self._load()
        before = len(data["accounts"])
        data["accounts"] = [a for a in data["accounts"] if a.get("id") != account_id]

        if len(data["accounts"]) == before:
            raise RuntimeError("Аккаунт не найден")

        if data.get("active_account_id") == account_id:
            data["active_account_id"] = data["accounts"][0]["id"] if data["accounts"] else None

        self._save(data)
        self.ensure_default_account()

    def get_launch_profile(self, preferred_account_id: str | None = None) -> dict[str, str]:
        account = None

        if preferred_account_id:
            for item in self.list_accounts():
                if item.get("id") == preferred_account_id:
                    account = item
                    break

        if not account:
            account = self.get_active_account()

        if not account:
            account = self.ensure_default_account()

        username = self.normalize_username(account.get("username") or account.get("display_name") or "NexusPlayer")
        account_uuid = account.get("uuid") or self.make_offline_uuid(username)

        return {
            "username": username,
            "uuid": str(account_uuid).replace("-", ""),
            "token": account.get("access_token") or "0",
            "access_token": account.get("access_token") or "0",
            "user_type": account.get("provider") or "offline",
            "account_id": account.get("id") or "",
            "provider": account.get("provider") or "offline",
        }

    def format_provider(self, provider: str) -> str:
        provider = (provider or "offline").lower()
        if provider == "offline":
            return "Offline"
        if provider == "microsoft":
            return "Microsoft"
        if provider in {"ely", "ely.by", "ely_by"}:
            return "Ely.by"
        return provider

    def status_text(self, account: dict[str, Any]) -> str:
        provider = self.format_provider(account.get("provider", "offline"))
        status = account.get("status", "active")
        if status == "active":
            return f"{provider} • готов"
        if status == "needs_reauth":
            return f"{provider} • нужен повторный вход"
        return f"{provider} • {status}"
