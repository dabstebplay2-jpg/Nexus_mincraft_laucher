from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
import sys

from core.discord_presence import DiscordPresenceManager


class FakeRpc:
    def __init__(self):
        self.updates = []

    def update(self, **payload):
        self.updates.append(payload)


class DiscordPresenceTests(unittest.TestCase):
    def test_game_status_is_kept_until_minecraft_closes(self) -> None:
        manager = DiscordPresenceManager()
        fake_rpc = FakeRpc()
        manager._rpc = fake_rpc
        manager.connect = lambda: True

        instance = {
            "name": "Survival Pack",
            "minecraft_version": "1.20.1",
            "loader": "fabric",
        }

        self.assertTrue(manager.set_playing(instance))
        self.assertEqual(len(fake_rpc.updates), 1)
        self.assertEqual(fake_rpc.updates[-1]["details"], "Играет в Minecraft через Nexus Launcher")
        self.assertEqual(fake_rpc.updates[-1]["state"], "Survival Pack • 1.20.1 • fabric")

        self.assertTrue(manager.set_launcher_idle("Каталог"))
        self.assertEqual(len(fake_rpc.updates), 1)

        self.assertTrue(manager.set_browsing_mods())
        self.assertEqual(len(fake_rpc.updates), 1)

        self.assertTrue(manager.set_minecraft_closed("Minecraft закрыт"))
        self.assertEqual(len(fake_rpc.updates), 2)
        self.assertEqual(fake_rpc.updates[-1]["details"], "В Nexus Launcher")
        self.assertEqual(fake_rpc.updates[-1]["state"], "Minecraft закрыт")

    def test_launching_status_contains_instance_context(self) -> None:
        manager = DiscordPresenceManager()
        fake_rpc = FakeRpc()
        manager._rpc = fake_rpc
        manager.connect = lambda: True

        self.assertTrue(manager.set_launching({
            "name": "Tech",
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
        }))

        self.assertEqual(fake_rpc.updates[-1]["details"], "Запускает Minecraft через Nexus Launcher")
        self.assertEqual(fake_rpc.updates[-1]["state"], "Tech • 1.21.1 • neoforge")

    def test_first_connection_and_reconnect_keep_game_activity(self) -> None:
        connections = []

        class FakePresence:
            def __init__(self, client_id):
                self.client_id = client_id
                self.updates = []
                connections.append(self)

            def connect(self):
                pass

            def update(self, **payload):
                self.updates.append(payload)

            def close(self):
                pass

        settings = SimpleNamespace(
            is_discord_presence_enabled=lambda: True,
            get_discord_client_id=lambda: "123456789",
        )
        manager = DiscordPresenceManager()
        instance = {"name": "Survival", "minecraft_version": "1.21", "loader": "vanilla"}

        with patch("core.discord_presence.get_launcher_settings", return_value=settings), patch.dict(
            sys.modules, {"pypresence": SimpleNamespace(Presence=FakePresence)}
        ):
            self.assertTrue(manager.set_playing(instance))
            self.assertTrue(manager._game_active)
            self.assertEqual(len(connections), 1)
            self.assertEqual(connections[0].updates[-1]["large_image"], "nexus")

            manager.disconnect()
            self.assertTrue(manager._game_active)
            self.assertTrue(manager.refresh())
            self.assertEqual(len(connections), 2)
            self.assertEqual(connections[1].updates[-1]["details"], "Играет в Minecraft через Nexus Launcher")

            self.assertTrue(manager.set_launcher_idle("Настройки"))
            self.assertEqual(manager._state.mode, "playing")


if __name__ == "__main__":
    unittest.main()
