"""Minecraft download callbacks must be presented as percentages."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.download_manager import DownloadManager


class DownloadProgressTests(unittest.TestCase):
    def test_old_and_new_progress_never_exceed_100_percent(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "core.download_manager.DATA_DIR", Path(directory),
        ):
            manager = DownloadManager()
            task_id = manager.start_task("minecraft", "Запуск Minecraft")
            manager.update_task(task_id, progress=486)
            self.assertEqual(manager.list_tasks()[0]["progress"], 100)

            manager.file_path.write_text(json.dumps({
                "tasks": [{"id": "old", "progress": 486, "state": "failed"}],
            }), encoding="utf-8")
            self.assertEqual(manager.list_tasks()[0]["progress"], 100)


if __name__ == "__main__":
    unittest.main()
