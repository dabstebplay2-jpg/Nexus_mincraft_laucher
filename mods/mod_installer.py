import hashlib
import logging
import time
from pathlib import Path

import requests

from core.constants import USER_AGENT
from mods.modrinth_api import ModrinthAPI
from storage.json_store import load_json, save_json


logger = logging.getLogger(__name__)


class ModInstaller:
    SUPPORTED_TYPES = {"mod", "resourcepack", "shader"}

    def __init__(self, progress_callback=None, status_callback=None, detail_callback=None):
        self.api = ModrinthAPI()
        self.progress_callback = progress_callback or (lambda value: None)
        self.status_callback = status_callback or (lambda text: None)
        self.detail_callback = detail_callback or (lambda text: None)

    def get_install_dir(self, instance, project_type: str) -> Path:
        minecraft_dir = Path(instance["minecraft_dir"])

        if project_type == "resourcepack":
            return minecraft_dir / "resourcepacks"

        if project_type == "shader":
            return minecraft_dir / "shaderpacks"

        return minecraft_dir / "mods"

    def install_project(self, project, instance, project_type: str = "mod"):
        project_type = (project_type or "mod").lower()

        if project_type == "modpack":
            raise RuntimeError(
                "Установка modpack (.mrpack) пока не поддерживается.\n\n"
                "Используй тип «mod», «resourcepack» или «shader»."
            )

        if project_type not in self.SUPPORTED_TYPES:
            raise RuntimeError(f"Неподдерживаемый тип проекта: {project_type}")

        project_id = project.get("project_id") or project.get("slug")
        title = project.get("title", project_id)

        minecraft_version = instance["minecraft_version"]
        loader = instance["loader"]

        if project_type == "mod" and loader == "vanilla":
            raise RuntimeError("Для установки модов нужна сборка Fabric / Forge / NeoForge / Quilt.")

        self.status_callback(f"Поиск версии мода: {title}")

        versions = self.api.get_project_versions(
            project_id_or_slug=project_id,
            minecraft_version=minecraft_version,
            loader=loader,
        )

        if not versions:
            raise RuntimeError(
                f"Не найдена совместимая версия мода.\n\n"
                f"Мод: {title}\n"
                f"Minecraft: {minecraft_version}\n"
                f"Loader: {loader}"
            )

        selected_version = self.pick_best_version(versions)
        installed = []

        self.install_version(
            selected_version,
            instance,
            installed,
            project_type=project_type,
            depth=0,
        )
        self.save_installed_index(instance, project, selected_version, installed, project_type)

        return installed

    def update_project(self, record, instance):
        project = {
            "project_id": record.get("project_id"),
            "slug": record.get("slug"),
            "title": record.get("title"),
        }

        return self.install_project(project, instance, record.get("project_type", "mod"))

    def install_version(self, version, instance, installed, project_type="mod", depth=0):
        if depth > 6:
            logger.warning("Dependency depth limit reached")
            return

        name = version.get("name") or version.get("version_number") or version.get("id")
        self.status_callback(f"Установка: {name}")

        file_info = self.pick_primary_file(version)

        if not file_info:
            raise RuntimeError(f"У версии {name} нет файла для скачивания.")

        install_dir = self.get_install_dir(instance, project_type)
        install_dir.mkdir(parents=True, exist_ok=True)

        target = install_dir / file_info["filename"]

        if target.exists():
            if self.file_matches_hash(target, file_info):
                self.detail_callback(f"Файл уже есть: {target.name}")
            else:
                self.detail_callback(f"Повторная загрузка (хеш не совпал): {target.name}")
                target.unlink()
                self.download_file(file_info["url"], target)
                self.verify_hash(target, file_info)
        else:
            self.download_file(file_info["url"], target)
            self.verify_hash(target, file_info)

        installed.append(str(target))
        logger.info("Installed mod file: %s", target)

        for dependency in version.get("dependencies", []):
            if dependency.get("dependency_type") != "required":
                continue

            version_id = dependency.get("version_id")
            project_id = dependency.get("project_id")

            if version_id:
                dependency_version = self.api.get_version(version_id)
                self.install_version(
                    dependency_version,
                    instance,
                    installed,
                    project_type=project_type,
                    depth=depth + 1,
                )
                continue

            if project_id:
                versions = self.api.get_project_versions(
                    project_id_or_slug=project_id,
                    minecraft_version=instance["minecraft_version"],
                    loader=instance["loader"],
                )

                if versions:
                    self.install_version(
                        self.pick_best_version(versions),
                        instance,
                        installed,
                        project_type=project_type,
                        depth=depth + 1,
                    )

    def pick_best_version(self, versions):
        releases = [version for version in versions if version.get("version_type") == "release"]

        pool = releases or versions

        return sorted(
            pool,
            key=lambda item: item.get("date_published") or "",
            reverse=True,
        )[0]

    def pick_primary_file(self, version):
        files = version.get("files", [])

        if not files:
            return None

        for file in files:
            if file.get("primary"):
                return file

        return files[0]

    def download_file(self, url, target: Path):
        logger.info("Downloading %s -> %s", url, target)

        with requests.get(url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT}) as response:
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            start_time = time.time()

            with open(target, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue

                    file.write(chunk)
                    downloaded += len(chunk)

                    elapsed = max(time.time() - start_time, 0.001)
                    speed = downloaded / elapsed

                    if total:
                        progress = int(downloaded / total * 100)
                        self.progress_callback(progress)

                    self.detail_callback(
                        f"{self.mb(downloaded)} / {self.mb(total)} • {self.mb(speed)}/s"
                        if total
                        else f"{self.mb(downloaded)} • {self.mb(speed)}/s"
                    )

    def file_matches_hash(self, path: Path, file_info):
        hashes = file_info.get("hashes", {})
        expected_sha512 = hashes.get("sha512")
        expected_sha1 = hashes.get("sha1")

        if expected_sha512:
            return self.file_hash(path, "sha512") == expected_sha512

        if expected_sha1:
            return self.file_hash(path, "sha1") == expected_sha1

        return True

    def verify_hash(self, path: Path, file_info):
        hashes = file_info.get("hashes", {})
        expected_sha512 = hashes.get("sha512")
        expected_sha1 = hashes.get("sha1")

        if expected_sha512:
            actual = self.file_hash(path, "sha512")

            if actual != expected_sha512:
                raise RuntimeError(f"SHA512 не совпал для файла:\n{path}")

        elif expected_sha1:
            actual = self.file_hash(path, "sha1")

            if actual != expected_sha1:
                raise RuntimeError(f"SHA1 не совпал для файла:\n{path}")

    def file_hash(self, path: Path, algorithm: str):
        hasher = hashlib.new(algorithm)

        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 256), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def save_installed_index(self, instance, project, version, installed_files, project_type="mod"):
        index_path = Path(instance["path"]) / "mods_index.json"
        data = load_json(index_path, {"mods": []})

        record = {
            "project_id": project.get("project_id"),
            "slug": project.get("slug"),
            "title": project.get("title"),
            "project_type": project_type,
            "version_id": version.get("id"),
            "version_number": version.get("version_number"),
            "files": installed_files,
            "updated_at": version.get("date_published"),
        }

        data["mods"] = [
            item for item in data.get("mods", [])
            if item.get("project_id") != record["project_id"]
        ]

        data["mods"].append(record)
        save_json(index_path, data)

    def remove_from_index(self, instance, file_path: Path):
        index_path = Path(instance["path"]) / "mods_index.json"
        data = load_json(index_path, {"mods": []})
        file_str = str(file_path)

        changed = False

        for mod in data.get("mods", []):
            files = mod.get("files", [])
            if file_str in files:
                mod["files"] = [item for item in files if item != file_str]
                changed = True

        data["mods"] = [
            item for item in data.get("mods", [])
            if item.get("files")
        ]

        if changed:
            save_json(index_path, data)

        return changed

    def delete_mod_file(self, path: Path):
        if path.exists() and path.is_file():
            path.unlink()
            return True

        return False

    def mb(self, bytes_value):
        return f"{bytes_value / 1024 / 1024:.2f} MB"