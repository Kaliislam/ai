"""Todo / Görev Yönetim Sistemi - SQLite backend, subtask, reminder, tree view."""

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "projects.db"
)


@dataclass
class Task:
    """Görev veri modeli."""

    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: str = "todo"  # todo / in_progress / done / cancelled
    priority: str = "medium"  # low / medium / high / urgent
    deadline: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    parent_task_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    reminder_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "parent_task_id": self.parent_task_id,
            "tags": self.tags,
            "notes": self.notes,
            "reminder_at": self.reminder_at,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Task":
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except json.JSONDecodeError:
                tags = []
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            deadline=row["deadline"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            parent_task_id=row["parent_task_id"],
            tags=tags,
            notes=row["notes"],
            reminder_at=row["reminder_at"],
        )


class TodoManager:
    """Görev yönetimi: CRUD, subtask, reminder, tree view, project transfer."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT REFERENCES projects(id),
                    parent_task_id TEXT REFERENCES tasks(id),
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    deadline TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    tags TEXT,
                    notes TEXT,
                    reminder_at TEXT
                )
                """
            )
            conn.commit()

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _now_iso(self) -> str:
        return datetime.now().isoformat()

    def _update_project_progress(self, project_id: str) -> None:
        """Bağlı projenin progress yüzdesini recalculate eder."""
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
                (project_id,),
            ).fetchone()[0]
            done = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ? AND status = 'done'",
                (project_id,),
            ).fetchone()[0]
            progress = int((done / total) * 100) if total else 0
            conn.execute(
                "UPDATE projects SET progress = ? WHERE id = ?",
                (progress, project_id),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def add_task(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        deadline: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[list[str]] = None,
        parent_task_id: Optional[str] = None,
    ) -> Task:
        """Yeni görev ekler."""
        task = Task(
            id=self._generate_id(),
            project_id=project_id,
            title=title,
            description=description,
            deadline=deadline,
            priority=priority,
            tags=tags or [],
            parent_task_id=parent_task_id,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks
                (id, project_id, parent_task_id, title, description, status,
                 priority, deadline, created_at, completed_at, tags, notes, reminder_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.project_id,
                    task.parent_task_id,
                    task.title,
                    task.description,
                    task.status,
                    task.priority,
                    task.deadline,
                    task.created_at,
                    task.completed_at,
                    json.dumps(task.tags, ensure_ascii=False),
                    task.notes,
                    task.reminder_at,
                ),
            )
            conn.commit()
        self._update_project_progress(project_id)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Tekil görev döndürür."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return Task.from_row(row) if row else None

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[Task]:
        """Görevleri listeler; isteğe bağlı filtreler."""
        conditions: list[str] = []
        params: list[Any] = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if priority:
            conditions.append("priority = ?")
            params.append(priority)

        query = "SELECT * FROM tasks"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Task.from_row(r) for r in rows]

    def update_task(self, task_id: str, **fields: Any) -> bool:
        """Görev alanlarını günceller."""
        allowed = {
            "title",
            "description",
            "status",
            "priority",
            "deadline",
            "completed_at",
            "tags",
            "notes",
            "reminder_at",
            "parent_task_id",
            "project_id",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"], ensure_ascii=False)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]

        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return cur.rowcount > 0

    def complete_task(self, task_id: str, notes: Optional[str] = None) -> bool:
        """Görevi tamamlar (status=done, completed_at=now)."""
        now = self._now_iso()
        updates: dict[str, Any] = {
            "status": "done",
            "completed_at": now,
        }
        if notes:
            updates["notes"] = notes
        ok = self.update_task(task_id, **updates)
        if ok:
            task = self.get_task(task_id)
            if task:
                self._update_project_progress(task.project_id)
        return ok

    def delete_task(self, task_id: str) -> bool:
        """Görevi ve alt görevlerini siler."""
        with self._connect() as conn:
            # önce alt görevleri bul
            child_rows = conn.execute(
                "SELECT id FROM tasks WHERE parent_task_id = ?", (task_id,)
            ).fetchall()
            child_ids = [r["id"] for r in child_rows]
            # recursive alt görev silme
            for cid in child_ids:
                conn.execute("DELETE FROM tasks WHERE id = ?", (cid,))
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        # progress recalc
        task = self.get_task(task_id)
        if task:
            self._update_project_progress(task.project_id)
        return cur.rowcount > 0

    def move_task(self, task_id: str, new_project_id: str) -> bool:
        """Görevi başka projeye taşır."""
        old = self.get_task(task_id)
        if not old:
            return False
        old_project_id = old.project_id
        ok = self.update_task(task_id, project_id=new_project_id)
        if ok:
            self._update_project_progress(old_project_id)
            self._update_project_progress(new_project_id)
        return ok

    # ------------------------------------------------------------------
    # Tree & reminder
    # ------------------------------------------------------------------
    def get_task_tree(self, project_id: str) -> dict[str, Any]:
        """Parent-child ilişkileri ile görev ağacı döndürür."""
        tasks = self.list_tasks(project_id=project_id)
        task_map: dict[str, dict[str, Any]] = {}
        for t in tasks:
            task_map[t.id] = {
                **t.to_dict(),
                "children": [],
            }
        roots: list[dict[str, Any]] = []
        for t in tasks:
            node = task_map[t.id]
            if t.parent_task_id and t.parent_task_id in task_map:
                task_map[t.parent_task_id]["children"].append(node)
            else:
                roots.append(node)
        return {"project_id": project_id, "tasks": roots}

    def set_reminder(self, task_id: str, remind_at: str) -> bool:
        """Göreve hatırlatma zamanı ekler / günceller."""
        return self.update_task(task_id, reminder_at=remind_at)

    def get_due_reminders(self) -> list[Task]:
        """Zamanı gelmiş hatırlatıcıları döndürür."""
        now = self._now_iso()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE reminder_at <= ? AND status NOT IN ('done', 'cancelled')
                ORDER BY reminder_at ASC
                """,
                (now,),
            ).fetchall()
        return [Task.from_row(r) for r in rows]
