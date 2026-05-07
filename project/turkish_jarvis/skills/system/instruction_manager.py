"""Talimat / Instruction Yönetim Sistemi - Asistanın proaktif önerilerini kaydeder."""

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
class Instruction:
    """Talikat veri modeli."""

    id: str
    content: str
    project_id: Optional[str] = None
    type: str = "suggestion"  # suggestion / warning / correction / reminder
    priority: str = "medium"  # low / medium / high / urgent
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    done_at: Optional[str] = None
    related_task_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "project_id": self.project_id,
            "type": self.type,
            "priority": self.priority,
            "created_at": self.created_at,
            "done_at": self.done_at,
            "related_task_id": self.related_task_id,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Instruction":
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            content=row["content"],
            type=row["type"],
            priority=row["priority"],
            created_at=row["created_at"],
            done_at=row["done_at"],
            related_task_id=row["related_task_id"],
        )


class InstructionManager:
    """Asistan talimatlarını yönetir: CRUD, günlük özet, aksiyon öneri."""

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
    def add_instruction(
        self,
        project_id: Optional[str] = None,
        content: str = "",
        type: str = "suggestion",
        priority: str = "medium",
        related_task_id: Optional[str] = None,
    ) -> Instruction:
        """Yeni talimat / öneri ekler."""
        instr = Instruction(
            id=self._generate_id(),
            project_id=project_id,
            content=content,
            type=type,
            priority=priority,
            related_task_id=related_task_id,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO instructions
                (id, project_id, content, type, priority, created_at, done_at, related_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    instr.id,
                    instr.project_id,
                    instr.content,
                    instr.type,
                    instr.priority,
                    instr.created_at,
                    instr.done_at,
                    instr.related_task_id,
                ),
            )
            conn.commit()
        return instr

    def list_instructions(
        self,
        project_id: Optional[str] = None,
        type: Optional[str] = None,
    ) -> list[Instruction]:
        """Talimatları listeler; isteğe bağlı filtreler."""
        conditions: list[str] = []
        params: list[Any] = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if type:
            conditions.append("type = ?")
            params.append(type)

        query = "SELECT * FROM instructions"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Instruction.from_row(r) for r in rows]

    def mark_done(self, instruction_id: str) -> bool:
        """Talimatı tamamlandı olarak işaretler."""
        now = self._now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE instructions SET done_at = ? WHERE id = ?",
                (now, instruction_id),
            )
            conn.commit()
        return cur.rowcount > 0

    def get_pending_instructions(self) -> list[Instruction]:
        """Bekleyen (tamamlanmamış) talimatları döndürür."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM instructions
                WHERE done_at IS NULL
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high'   THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low'    THEN 4
                        ELSE 5
                    END,
                    created_at ASC
                """
            ).fetchall()
        return [Instruction.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Proactive helpers
    # ------------------------------------------------------------------
    def generate_daily_brief(self) -> str:
        """Günlük özet üretir: aktif projeler, yaklaşan deadline, bekleyen talimatlar."""
        lines: list[str] = []
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        lines.append(f"# Günlük Özet ({today})")
        lines.append("")

        with self._connect() as conn:
            # Active projects
            proj_rows = conn.execute(
                """
                SELECT id, name, priority, deadline, progress
                FROM projects
                WHERE status = 'active'
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high'   THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END
                """
            ).fetchall()
            lines.append(f"## Aktif Projeler ({len(proj_rows)})")
            for row in proj_rows:
                dl = f" | deadline: {row['deadline'][:10]}" if row["deadline"] else ""
                lines.append(f"- [{row['progress']}%] {row['name']}{dl}")
            lines.append("")

            # Upcoming task deadlines (next 3 days)
            near = (now + timedelta(days=3)).isoformat()
            now_iso = now.isoformat()
            task_rows = conn.execute(
                """
                SELECT t.title, t.deadline, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.deadline BETWEEN ? AND ?
                      AND t.status NOT IN ('done', 'cancelled')
                ORDER BY t.deadline ASC
                """,
                (now_iso, near),
            ).fetchall()
            lines.append(f"## Yaklaşan Görevler (3 gün içinde, {len(task_rows)})")
            for row in task_rows:
                dl = row["deadline"][:10] if row["deadline"] else "?"
                lines.append(f"- {row['title']} (Proje: {row['project_name'] or '-'}) [{dl}]")
            lines.append("")

            # Pending instructions
            instr_rows = conn.execute(
                """
                SELECT content, type, priority
                FROM instructions
                WHERE done_at IS NULL
                ORDER BY created_at DESC
                LIMIT 5
                """
            ).fetchall()
            lines.append(f"## Bekleyen Talimatlar ({len(instr_rows)} gösteriliyor)")
            for row in instr_rows:
                emoji = {"warning": "⚠️", "correction": "🔧", "reminder": "⏰"}.get(
                    row["type"], "💡"
                )
                lines.append(f"- {emoji} [{row['priority']}] {row['content']}")
            lines.append("")

        return "\n".join(lines)

    def suggest_next_action(self, project_id: str) -> str:
        """Belirli proje için sonraki aksiyon önerir."""
        with self._connect() as conn:
            # Proje bilgisi
            proj = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if not proj:
                return "Proje bulunamadı."

            # Tamamlanmamış görevler
            tasks = conn.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND status NOT IN ('done', 'cancelled')
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high'   THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END,
                    deadline ASC
                """,
                (project_id,),
            ).fetchall()

            # Gecikmiş var mı?
            now_iso = self._now_iso()
            overdue = [t for t in tasks if t["deadline"] and t["deadline"] < now_iso]

            lines: list[str] = []
            lines.append(f"📁 Proje: {proj['name']} (progress: {proj['progress']}%)")
            lines.append("")

            if overdue:
                lines.append(f"⚠️ {len(overdue)} gecikmiş görev var. Öncelikle bunlarla ilgilenmelisiniz:")
                for t in overdue[:3]:
                    lines.append(f"   - {t['title']} (deadline: {t['deadline'][:10]})")
                lines.append("")

            if tasks:
                next_task = tasks[0]
                lines.append(f"💡 Sonraki aksiyon: '{next_task['title']}' görevine başla.")
                if next_task["deadline"]:
                    lines.append(f"   Deadline: {next_task['deadline'][:10]}")
            else:
                lines.append("🎉 Tüm görevler tamamlanmış görünüyor. Projeyi tamamlandı olarak işaretleyebilirsiniz.")

            # Bekleyen talimatlar
            instr = conn.execute(
                """
                SELECT content, type FROM instructions
                WHERE project_id = ? AND done_at IS NULL
                ORDER BY created_at DESC
                LIMIT 3
                """,
                (project_id,),
            ).fetchall()
            if instr:
                lines.append("")
                lines.append("📌 İlgili talimatlar:")
                for i in instr:
                    lines.append(f"   - {i['content']}")

        return "\n".join(lines)
