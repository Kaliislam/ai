"""Ruflo Goals Plugin Bridge.

Hedef yönetimi: wraps ``turkish_jarvis.skills.system.project_manager.ProjectManager``
ve Ruflo-style hedef kırılımı (goal decomposition) ekler.
Bir hedef -> alt-görev ağacı; ilerleme otomatik hesaplanır.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "ruflo_goals.db"
)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Goal:
    """Ruflo-style goal object."""

    id: str
    title: str
    description: Optional[str] = None
    status: str = "active"  # active / paused / completed / cancelled
    priority: str = "medium"  # low / medium / high / urgent
    deadline: Optional[str] = None
    parent_id: Optional[str] = None
    progress: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "deadline": self.deadline,
            "parent_id": self.parent_id,
            "progress": self.progress,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "tags": self.tags,
        }


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloGoals:
    """Goal manager with hierarchical decomposition.

    Usage
    -----
    goals = RufloGoals()
    g = goals.create_goal("Learn Python", deadline="2025-12-31")
    goals.add_subgoal(g.id, "Finish basics")
    goals.add_subgoal(g.id, "Build a project")
    goals.update_progress(g.id)
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DEFAULT_DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._pm: Any = None
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    priority TEXT DEFAULT 'medium',
                    deadline TEXT,
                    parent_id TEXT,
                    progress INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    tags TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _generate_id(self) -> str:
        return f"goal_{uuid.uuid4().hex[:8]}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_goal(
        self,
        title: str,
        description: Optional[str] = None,
        deadline: Optional[str] = None,
        priority: str = "medium",
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Goal:
        """Create a new goal."""
        goal = Goal(
            id=self._generate_id(),
            title=title,
            description=description,
            deadline=deadline,
            priority=priority,
            parent_id=parent_id,
            tags=tags or [],
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO goals
                (id, title, description, status, priority, deadline, parent_id,
                 progress, created_at, completed_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.id, goal.title, goal.description, goal.status,
                    goal.priority, goal.deadline, goal.parent_id,
                    goal.progress, goal.created_at, goal.completed_at,
                    json.dumps(goal.tags, ensure_ascii=False),
                ),
            )
            conn.commit()
        logger.info("[ruflo-goals] created %s", goal.id)
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Fetch a single goal by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_goal(row)

    def list_goals(
        self, status: Optional[str] = None, parent_id: Optional[str] = None
    ) -> List[Goal]:
        """List goals with optional filters."""
        query = "SELECT * FROM goals WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if parent_id is not None:
            query += " AND parent_id = ?"
            params.append(parent_id)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_goal(r) for r in rows]

    def update_goal(self, goal_id: str, **fields: Any) -> bool:
        """Update goal fields."""
        allowed = {"title", "description", "status", "priority", "deadline", "progress", "completed_at", "tags"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"], ensure_ascii=False)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [goal_id]
        with self._connect() as conn:
            cur = conn.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", values)
            conn.commit()
        return cur.rowcount > 0

    def delete_goal(self, goal_id: str, cascade: bool = True) -> bool:
        """Delete a goal and optionally its children."""
        with self._connect() as conn:
            if cascade:
                conn.execute("DELETE FROM goals WHERE parent_id = ?", (goal_id,))
            cur = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Hierarchy helpers
    # ------------------------------------------------------------------

    def add_subgoal(self, parent_id: str, title: str, **kwargs: Any) -> Goal:
        """Create a child goal under an existing goal."""
        return self.create_goal(title=title, parent_id=parent_id, **kwargs)

    def get_tree(self, root_id: str) -> Dict[str, Any]:
        """Fetch a goal and all descendants as a nested dict."""
        root = self.get_goal(root_id)
        if root is None:
            return {}

        def build(node_id: str) -> Dict[str, Any]:
            children = self.list_goals(parent_id=node_id)
            return {
                **self.get_goal(node_id).to_dict(),  # type: ignore[union-attr]
                "children": [build(c.id) for c in children],
            }

        return build(root_id)

    def update_progress(self, goal_id: str) -> int:
        """Recalculate progress based on sub-goals."""
        subgoals = self.list_goals(parent_id=goal_id)
        if not subgoals:
            return self.get_goal(goal_id).progress if self.get_goal(goal_id) else 0  # type: ignore[union-attr]
        done = sum(1 for g in subgoals if g.status == "completed")
        progress = int((done / len(subgoals)) * 100)
        self.update_goal(goal_id, progress=progress)
        # bubble up if there is a parent
        parent = self.get_goal(goal_id)
        if parent and parent.parent_id:
            self.update_progress(parent.parent_id)
        return progress

    def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal and all sub-goals as completed."""
        now = datetime.now().isoformat()
        self.update_goal(goal_id, status="completed", completed_at=now, progress=100)
        for child in self.list_goals(parent_id=goal_id):
            self.complete_goal(child.id)
        # bubble progress up
        parent = self.get_goal(goal_id)
        if parent and parent.parent_id:
            self.update_progress(parent.parent_id)
        return True

    # ------------------------------------------------------------------
    # Integration with ProjectManager
    # ------------------------------------------------------------------

    def promote_to_project(self, goal_id: str) -> Optional[str]:
        """Convert a goal into a ProjectManager project and return the new project ID."""
        goal = self.get_goal(goal_id)
        if goal is None:
            return None
        try:
            from turkish_jarvis.skills.system.project_manager import ProjectManager

            pm = ProjectManager()
            project = pm.create_project(
                name=goal.title,
                description=goal.description or "",
                deadline=goal.deadline,
                priority=goal.priority,
                tags=goal.tags,
            )
            logger.info("[ruflo-goals] promoted %s -> project %s", goal_id, project.id)
            return project.id
        except Exception as exc:
            logger.warning("[ruflo-goals] promote failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Goal statistics."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM goals WHERE status = 'active'").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM goals WHERE status = 'completed'").fetchone()[0]
            overdue = conn.execute(
                "SELECT COUNT(*) FROM goals WHERE deadline < ? AND status NOT IN ('completed', 'cancelled')",
                (datetime.now().isoformat(),),
            ).fetchone()[0]
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "overdue": overdue,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_goal(row: sqlite3.Row) -> Goal:
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except json.JSONDecodeError:
                pass
        return Goal(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            deadline=row["deadline"],
            parent_id=row["parent_id"],
            progress=row["progress"] or 0,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            tags=tags,
        )
