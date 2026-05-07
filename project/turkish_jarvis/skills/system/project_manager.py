"""Proje Yönetim Sistemi - SQLite backend ile proje CRUD, istatistik ve deadline takibi."""

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
class Project:
    """Proje veri modeli."""

    id: str
    name: str
    description: Optional[str] = None
    status: str = "active"  # active / paused / completed / archived
    priority: str = "medium"  # low / medium / high / urgent
    deadline: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    progress: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "tags": self.tags,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Project":
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except json.JSONDecodeError:
                tags = []
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            deadline=row["deadline"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            progress=row["progress"] or 0,
            tags=tags,
        )


class ProjectManager:
    """Proje yönetimi: CRUD, istatistik, deadline takibi."""

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
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    priority TEXT DEFAULT 'medium',
                    deadline TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    progress INTEGER DEFAULT 0,
                    tags TEXT
                )
                """
            )
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS instructions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT REFERENCES projects(id),
                    content TEXT NOT NULL,
                    type TEXT DEFAULT 'suggestion',
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    done_at TEXT,
                    related_task_id TEXT
                )
                """
            )
            conn.commit()

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _now_iso(self) -> str:
        return datetime.now().isoformat()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        deadline: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[list[str]] = None,
    ) -> Project:
        """Yeni proje oluşturur."""
        project = Project(
            id=self._generate_id(),
            name=name,
            description=description,
            deadline=deadline,
            priority=priority,
            tags=tags or [],
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects
                (id, name, description, status, priority, deadline, created_at,
                 completed_at, progress, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.name,
                    project.description,
                    project.status,
                    project.priority,
                    project.deadline,
                    project.created_at,
                    project.completed_at,
                    project.progress,
                    json.dumps(project.tags, ensure_ascii=False),
                ),
            )
            conn.commit()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Tekil proje döndürür."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return Project.from_row(row) if row else None

    def list_projects(self, status: Optional[str] = None) -> list[Project]:
        """Projeleri listeler; isteğe bağlı status filtresi."""
        query = "SELECT * FROM projects"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Project.from_row(r) for r in rows]

    def update_project(self, project_id: str, **fields: Any) -> bool:
        """Proje alanlarını günceller."""
        allowed = {
            "name",
            "description",
            "status",
            "priority",
            "deadline",
            "completed_at",
            "progress",
            "tags",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"], ensure_ascii=False)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [project_id]

        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return cur.rowcount > 0

    def delete_project(self, project_id: str) -> bool:
        """Projeyi ve bağlı task / instruction kayıtlarını siler."""
        with self._connect() as conn:
            conn.execute("DELETE FROM instructions WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
        return cur.rowcount > 0

    def archive_project(self, project_id: str) -> bool:
        """Projeyi arşivler (status = archived)."""
        return self.update_project(project_id, status="archived")

    # ------------------------------------------------------------------
    # Statistics & helpers
    # ------------------------------------------------------------------
    def _recalculate_progress(self, project_id: str) -> None:
        """Tüm görevlerin durumuna göre project.progress günceller."""
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
        self.update_project(project_id, progress=progress)

    def get_project_stats(self) -> dict[str, Any]:
        """Genel proje istatistikleri."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE status = 'active'"
            ).fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE status = 'completed'"
            ).fetchone()[0]
            archived = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE status = 'archived'"
            ).fetchone()[0]
            overdue = conn.execute(
                """
                SELECT COUNT(*) FROM projects
                WHERE deadline < ? AND status NOT IN ('completed', 'archived')
                """,
                (self._now_iso(),),
            ).fetchone()[0]
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "archived": archived,
            "overdue": overdue,
        }

    def get_overdue_items(self) -> list[dict[str, Any]]:
        """Gecikmiş projeleri ve görevleri bulur."""
        now = self._now_iso()
        items: list[dict[str, Any]] = []
        with self._connect() as conn:
            # overdue projects
            proj_rows = conn.execute(
                """
                SELECT * FROM projects
                WHERE deadline < ? AND status NOT IN ('completed', 'archived')
                """,
                (now,),
            ).fetchall()
            for row in proj_rows:
                items.append(
                    {
                        "type": "project",
                        "id": row["id"],
                        "name": row["name"],
                        "deadline": row["deadline"],
                        "priority": row["priority"],
                    }
                )
            # overdue tasks
            task_rows = conn.execute(
                """
                SELECT t.*, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.deadline < ? AND t.status NOT IN ('done', 'cancelled')
                """,
                (now,),
            ).fetchall()
            for row in task_rows:
                items.append(
                    {
                        "type": "task",
                        "id": row["id"],
                        "title": row["title"],
                        "project_name": row["project_name"],
                        "deadline": row["deadline"],
                        "priority": row["priority"],
                    }
                )
        return items

    def get_upcoming_deadlines(self, days: int = 7) -> list[dict[str, Any]]:
        """Yaklaşan deadline'ları döndürür (proje + görev)."""
        now = datetime.now()
        future = (now + timedelta(days=days)).isoformat()
        now_iso = now.isoformat()
        items: list[dict[str, Any]] = []
        with self._connect() as conn:
            # projects
            proj_rows = conn.execute(
                """
                SELECT * FROM projects
                WHERE deadline BETWEEN ? AND ?
                      AND status NOT IN ('completed', 'archived')
                """,
                (now_iso, future),
            ).fetchall()
            for row in proj_rows:
                items.append(
                    {
                        "type": "project",
                        "id": row["id"],
                        "name": row["name"],
                        "deadline": row["deadline"],
                        "priority": row["priority"],
                        "days_left": days,
                    }
                )
            # tasks
            task_rows = conn.execute(
                """
                SELECT t.*, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.deadline BETWEEN ? AND ?
                      AND t.status NOT IN ('done', 'cancelled')
                """,
                (now_iso, future),
            ).fetchall()
            for row in task_rows:
                items.append(
                    {
                        "type": "task",
                        "id": row["id"],
                        "title": row["title"],
                        "project_name": row["project_name"],
                        "deadline": row["deadline"],
                        "priority": row["priority"],
                        "days_left": days,
                    }
                )
        # Sort by deadline
        items.sort(key=lambda x: x["deadline"] or "")
        return items
