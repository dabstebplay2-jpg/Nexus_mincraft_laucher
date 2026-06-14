import re
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path

from storage.paths import INSTANCES_DIR, INSTANCES_FILE, ensure_project_dirs
from storage.json_store import load_json, save_json


logger = logging.getLogger(__name__)

_manager_instance = None


def get_instance_manager():
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = InstanceManager()

    return _manager_instance


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-я0-9]+", "-", text)
    text = text.strip("-")
    return text or "instance"


class InstanceManager:
    def __init__(self):
        ensure_project_dirs()
        self.reload()

    def reload(self):
        self.data = load_json(INSTANCES_FILE, {"instances": []})
        return self.data

    def get_instances(self):
        return self.data.get("instances", [])

    def get_instance(self, instance_id: str):
        for instance in self.get_instances():
            if instance.get("id") == instance_id:
                return instance

        return None

    def save(self):
        save_json(INSTANCES_FILE, self.data)

    def create_instance(
        self,
        name: str,
        minecraft_version: str,
        loader: str = "vanilla",
        ram_mb: int = 4096,
    ):
        instance_id = str(uuid.uuid4())
        folder_name = slugify(name)

        instance_path = INSTANCES_DIR / folder_name

        counter = 2
        while instance_path.exists():
            instance_path = INSTANCES_DIR / f"{folder_name}-{counter}"
            counter += 1

        minecraft_dir = instance_path / ".minecraft"
        mods_dir = minecraft_dir / "mods"

        mods_dir.mkdir(parents=True, exist_ok=True)

        instance = {
            "id": instance_id,
            "name": name,
            "minecraft_version": minecraft_version,
            "loader": loader,
            "ram_mb": ram_mb,
            "path": str(instance_path),
            "minecraft_dir": str(minecraft_dir),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "last_played_at": None,
        }

        save_json(instance_path / "instance.json", instance)

        self.data.setdefault("instances", [])
        self.data["instances"].append(instance)
        self.save()

        return instance

    def update_instance(self, instance_id: str, updates: dict):
        for instance in self.get_instances():
            if instance.get("id") == instance_id:
                instance.update(updates)

                instance_path = Path(instance["path"])
                save_json(instance_path / "instance.json", instance)
                self.save()

                return instance

        raise RuntimeError("Сборка не найдена.")

    def mark_played(self, instance_id: str):
        return self.update_instance(
            instance_id,
            {"last_played_at": datetime.now().isoformat(timespec="seconds")},
        )

    def delete_instance(self, instance_id: str, delete_files: bool = True):
        instance = self.get_instance(instance_id)

        if not instance:
            raise RuntimeError("Сборка не найдена.")

        instance_path = Path(instance["path"])

        self.data["instances"] = [
            item for item in self.get_instances()
            if item.get("id") != instance_id
        ]

        self.save()

        if delete_files and instance_path.exists():
            shutil.rmtree(instance_path)

        return instance