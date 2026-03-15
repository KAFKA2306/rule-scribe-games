from datetime import UTC, datetime, timedelta
from typing import Any


class TaskManager:
    def __init__(self, retention_hours: int = 1):
        self._tasks: dict[str, dict[str, Any]] = {}
        self.retention_hours = retention_hours

    def add_task(self, task_id: str, data: dict[str, Any]):
        data["created_at"] = datetime.now(UTC)
        self._tasks[task_id] = data
        self.cleanup()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, updates: dict[str, Any]):
        if task_id in self._tasks:
            self._tasks[task_id].update(updates)
            self._tasks[task_id]["updated_at"] = datetime.now(UTC)

    def cleanup(self):
        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=self.retention_hours)
        expired = [
            tid
            for tid, tdata in self._tasks.items()
            if tdata.get("created_at", now) < cutoff
        ]
        for tid in expired:
            del self._tasks[tid]


task_manager = TaskManager()
