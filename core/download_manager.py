from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from storage.paths import DATA_DIR


class DownloadManager:
    def __init__(self):
        self._lock = threading.RLock()
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / "downloads.json"

        if not self.file_path.exists():
            self.save({"tasks": []})

    def load(self):
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            data = {"tasks": []}

        data.setdefault("tasks", [])
        return data

    def save(self, data):
        tmp = self.file_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.file_path)

    def list_tasks(self):
        with self._lock:
            return list(self.load().get("tasks", []))

    def add_task(self, title, kind="download", status="Готово", progress=100, state="completed", subtitle=""):
        with self._lock:
            data = self.load()

            task = {
                "id": str(uuid.uuid4()),
                "kind": kind,
                "title": title,
                "subtitle": subtitle,
                "status": status,
                "progress": int(progress),
                "state": state,
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
                "finished_at": int(time.time()) if state != "active" else None,
                "error": None,
            }

            data["tasks"].insert(0, task)
            self.save(data)
            return task

    def clear_all(self):
        with self._lock:
            data = self.load()
            count = len(data.get("tasks", []))
            data["tasks"] = []
            self.save(data)
            return count

    def clear_completed(self):
        with self._lock:
            data = self.load()
            before = len(data.get("tasks", []))
            data["tasks"] = [task for task in data["tasks"] if task.get("state") == "active"]
            self.save(data)
            return before - len(data["tasks"])

    def seed_demo_if_empty(self):
        if self.list_tasks():
            return

        self.add_task(
            title="Центр загрузок подключён",
            kind="system",
            status="Раздел «Загрузки» теперь работает",
            progress=100,
            state="completed",
            subtitle="Nexus Downloads Center",
        )

    @staticmethod
    def time_text(ts):
        if not ts:
            return "—"
        try:
            return time.strftime("%d.%m.%Y %H:%M", time.localtime(int(ts)))
        except Exception:
            return "—"

    def start_task(self, kind, title, subtitle="", total=100, metadata=None):
        with self._lock:
            data = self.load()
            task_id = str(uuid.uuid4())
            task = {
                "id": task_id,
                "kind": kind,
                "title": title,
                "subtitle": subtitle,
                "status": "Начинается...",
                "progress": 0,
                "total": int(total),
                "state": "active",
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
                "finished_at": None,
                "error": None,
                "metadata": metadata or {},
            }
            data["tasks"].insert(0, task)
            self.save(data)
            return task_id

    def update_task(self, task_id, status=None, progress=None, downloaded_bytes=None, total_bytes=None):
        with self._lock:
            data = self.load()
            for task in data["tasks"]:
                if task.get("id") == task_id:
                    if status is not None:
                        task["status"] = str(status)
                    if progress is not None:
                        task["progress"] = int(progress)
                    if downloaded_bytes is not None:
                        task["downloaded_bytes"] = int(downloaded_bytes)
                    if total_bytes is not None:
                        task["total_bytes"] = int(total_bytes)
                    task["updated_at"] = int(time.time())
                    self.save(data)
                    return task
            return None

    def finish_task(self, task_id, status="Завершено"):
        with self._lock:
            data = self.load()
            for task in data["tasks"]:
                if task.get("id") == task_id:
                    task["status"] = str(status)
                    task["progress"] = task.get("total", 100)
                    task["state"] = "completed"
                    task["updated_at"] = int(time.time())
                    task["finished_at"] = int(time.time())
                    self.save(data)
                    return task
            return None

    def fail_task(self, task_id, error, status="Ошибка"):
        with self._lock:
            data = self.load()
            for task in data["tasks"]:
                if task.get("id") == task_id:
                    task["status"] = str(status)
                    task["state"] = "failed"
                    task["error"] = str(error)
                    task["updated_at"] = int(time.time())
                    task["finished_at"] = int(time.time())
                    self.save(data)
                    return task
            return None

    @staticmethod
    def icon(kind):
        kind = (kind or "").lower()

        if kind == "minecraft":
            return "▣"
        if kind == "mod":
            return "✥"
        if kind == "java":
            return "☕"
        if kind == "skin":
            return "▧"
        if kind == "system":
            return "✓"

        return "↓"
