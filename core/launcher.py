import logging
import subprocess
from pathlib import Path

import minecraft_launcher_lib
from auth.account_manager import AccountManager
import requests

from core.java_manager import (
    find_java_executable,
    get_required_java_major,
    ensure_java_is_compatible,
)
from core.loader_manager import LoaderManager
from core.constants import APP_VERSION
from core.instance_manager import get_instance_manager
from core.launcher_settings import get_launcher_settings


logger = logging.getLogger(__name__)


class Launcher:
    def __init__(self, set_status=None, set_progress=None, set_max=None):
        self.set_status = set_status or (lambda text: None)
        self.set_progress = set_progress or (lambda value: None)
        self.set_max = set_max or (lambda value: None)

    def launch_instance(self, instance: dict):
        logger.info("Launch requested")
        logger.info("Instance data: %s", instance)

        minecraft_version = instance["minecraft_version"]
        loader = instance.get("loader", "vanilla").lower()
        minecraft_dir = Path(instance["minecraft_dir"])
        ram_mb = int(instance.get("ram_mb", 4096))

        minecraft_dir.mkdir(parents=True, exist_ok=True)

        callback = {
            "setStatus": self.set_status,
            "setProgress": self.set_progress,
            "setMax": self.set_max,
        }

        try:
            self.set_status("Проверка и скачивание Minecraft...")
            logger.info("Installing base Minecraft version: %s", minecraft_version)

            minecraft_launcher_lib.install.install_minecraft_version(
                minecraft_version,
                str(minecraft_dir),
                callback=callback,
            )

        except requests.exceptions.ConnectTimeout as error:
            logger.exception("Minecraft download timeout")
            raise RuntimeError(
                "Скачивание Minecraft не успело завершиться.\n\n"
                "Проверь интернет, VPN/прокси и попробуй снова.\n"
                "Если версия новая, Mojang runtime может скачиваться долго."
            ) from error

        except Exception:
            logger.exception("Minecraft base installation failed")
            raise

        launch_version = minecraft_version

        if loader != "vanilla":
            self.set_status(f"Установка {loader}...")
            logger.info("Installing loader: %s", loader)

            loader_manager = LoaderManager()
            launch_version = loader_manager.install_loader(
                loader_id=loader,
                minecraft_version=minecraft_version,
                minecraft_dir=str(minecraft_dir),
                callback=callback,
            )

            logger.info("Loader launch version: %s", launch_version)

        required_java = get_required_java_major(
            minecraft_dir=str(minecraft_dir),
            launch_version=launch_version,
            fallback_version=minecraft_version,
        )

        self.set_status(f"Поиск Java {required_java}+...")

        java_path = find_java_executable(min_major=required_java)

        if not java_path:
            from core.java_manager import build_java_required_message

            raise RuntimeError(
                build_java_required_message(required_java)
            )

        actual_java = ensure_java_is_compatible(java_path, required_java)

        logger.info(
            "Java compatible: actual=%s required=%s path=%s",
            actual_java,
            required_java,
            java_path,
        )

        self.set_status("Подготовка команды запуска...")

        options = minecraft_launcher_lib.utils.generate_test_options()

        options["username"] = "NexusPlayer"
        options["launcherName"] = "NexusLauncher"
        options["launcherVersion"] = APP_VERSION
        options["gameDirectory"] = str(minecraft_dir)
        options["executablePath"] = java_path
        options["defaultExecutablePath"] = java_path
        options["jvmArguments"] = [
            f"-Xmx{ram_mb}M",
            "-Xms1024M",
        ]

        command = minecraft_launcher_lib.command.get_minecraft_command(
            launch_version,
            str(minecraft_dir),
            options,
        )

        safe_command = [
            "***TOKEN***" if "token" in str(part).lower() else str(part)
            for part in command
        ]

        logger.debug("Minecraft command: %s", safe_command)

        self.set_status("Запуск Minecraft...")
        logger.info("Starting Minecraft process. launch_version=%s", launch_version)

        subprocess.Popen(
            command,
            cwd=str(minecraft_dir),
        )

        get_instance_manager().mark_played(instance["id"])

        logger.info("Minecraft process started")
        self.set_status("Minecraft запущен")
