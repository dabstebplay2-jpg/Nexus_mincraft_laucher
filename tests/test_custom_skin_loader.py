"""Local skin handoff to the Minecraft client."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.custom_skin_loader import prepare_custom_skin_loader
from core.launcher import Launcher


class CustomSkinLoaderTests(unittest.TestCase):
    def test_fabric_skin_uses_legacy_profile_and_keeps_other_providers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            minecraft_dir = root / ".minecraft"
            config_path = minecraft_dir / "CustomSkinLoader" / "CustomSkinLoader.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps({
                "cacheExpiry": 12,
                "loadlist": [
                    {"name": "LocalSkin", "type": "LocalSkin", "root": "wrong"},
                    {"name": "OtherSite", "type": "CustomSkinAPI", "root": "https://example.org/"},
                ],
            }), encoding="utf-8")
            mod = minecraft_dir / "mods" / "CustomSkinLoader.jar"
            mod.parent.mkdir()
            mod.write_bytes(b"existing mod")
            source = root / "chosen.png"
            source.write_bytes(b"chosen skin")

            result = prepare_custom_skin_loader(
                {"loader": "fabric", "minecraft_version": "1.20.1", "minecraft_dir": str(minecraft_dir)},
                {"username": "Player_1", "skin_model": "slim"},
                {"path": str(source)},
            )

            self.assertTrue(result.prepared)
            self.assertEqual(result.mod_path, mod)
            self.assertEqual(result.skin_path.read_bytes(), b"chosen skin")
            self.assertEqual(result.skin_path.name, "Player_1.png")
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["cacheExpiry"], 12)
            self.assertEqual(config["loadlist"][0], {
                "name": "LocalSkin",
                "type": "Legacy",
                "checkPNG": True,
                "skin": "LocalSkin/skins/{USERNAME}.png",
                "model": "slim",
            })
            self.assertEqual(config["loadlist"][1]["name"], "OtherSite")

    def test_vanilla_does_not_claim_to_apply_local_skin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "chosen.png"
            source.write_bytes(b"chosen skin")
            result = prepare_custom_skin_loader(
                {"loader": "vanilla", "minecraft_dir": str(root / ".minecraft")},
                {"username": "Player_1"},
                {"path": str(source)},
            )
            self.assertFalse(result.prepared)
            self.assertIn("Vanilla", result.message)
            self.assertFalse((root / ".minecraft").exists())

    def test_launcher_does_not_start_vanilla_with_unapplied_skin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "chosen.png"
            source.write_bytes(b"chosen skin")
            instance = {
                "id": "test", "loader": "vanilla", "minecraft_version": "1.20.1",
                "minecraft_dir": str(root / ".minecraft"),
            }
            with patch.object(Launcher, "_check_disk_space"), patch.object(
                Launcher, "_check_writable",
            ), patch.object(Launcher, "_check_loader_compatibility"), patch(
                "core.launcher.minecraft_launcher_lib.install.install_minecraft_version",
            ), patch("core.launcher.get_required_java_major", return_value=17), patch(
                "core.launcher.find_java_executable", return_value="java",
            ), patch("core.launcher.ensure_java_is_compatible", return_value=17), patch(
                "core.launcher.AccountManager",
            ) as manager, patch("core.skin_manager.SkinManager") as skins, patch(
                "core.launcher.subprocess.Popen",
            ) as popen:
                manager.return_value.get_active_account.return_value = {"username": "Player_1"}
                manager.return_value.get_launch_profile.return_value = {
                    "username": "Player_1", "uuid": "1234", "token": "0", "provider": "offline",
                }
                skins.return_value.get_account_skin.return_value = {"path": str(source)}
                with self.assertRaisesRegex(RuntimeError, "Vanilla"):
                    Launcher().launch_instance(instance)
                popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
