"""Regression checks for Java subprocesses used by mod loader installers."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.launcher import Launcher
from core.loader_manager import LoaderManager


class LoaderJavaPreflightTests(unittest.TestCase):
    def test_installer_receives_existing_java_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            java_path = Path(directory) / "Java Runtime" / "java.exe"
            java_path.parent.mkdir()
            java_path.touch()
            loader = Mock()
            loader.install.return_value = "fabric-loader"

            with patch("core.loader_manager.get_required_java_major", return_value=17), patch(
                "core.loader_manager.ensure_java_is_compatible", return_value=17,
            ):
                LoaderManager().run_loader_install(
                    loader, "fabric", "1.20.1", Path(directory), java_path=str(java_path),
                )

            self.assertEqual(loader.install.call_args.kwargs["java"], str(java_path))

    def test_missing_java_stops_before_installer_subprocess(self):
        loader = Mock()
        with tempfile.TemporaryDirectory() as directory, patch(
            "core.loader_manager.get_required_java_major", return_value=17,
        ), patch("core.loader_manager.find_java_executable", return_value=None), patch(
            "core.loader_manager.build_java_required_message", return_value="Нужна Java 17",
        ):
            with self.assertRaisesRegex(RuntimeError, "Нужна Java 17"):
                LoaderManager().run_loader_install(
                    loader, "fabric", "1.20.1", Path(directory),
                )
        loader.install.assert_not_called()

    def test_launcher_checks_java_before_installing_loader(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            Launcher, "_check_disk_space",
        ), patch.object(Launcher, "_check_writable"), patch.object(
            Launcher, "_check_loader_compatibility",
        ), patch("core.launcher.minecraft_launcher_lib.install.install_minecraft_version"), patch(
            "core.launcher.get_required_java_major", return_value=17,
        ), patch("core.launcher.find_java_executable", return_value=None), patch(
            "core.java_manager.build_java_required_message", return_value="Нужна Java 17",
        ), patch("core.launcher.LoaderManager") as manager:
            instance = {
                "minecraft_version": "1.20.1", "loader": "fabric",
                "minecraft_dir": directory, "ram_mb": 4096,
            }
            with self.assertRaisesRegex(RuntimeError, "Нужна Java 17"):
                Launcher().launch_instance(instance)
            manager.assert_not_called()


if __name__ == "__main__":
    unittest.main()
