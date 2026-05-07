"""
Chat History Manager - SQLite + FTS5 tabanlı sohbet geçmişi kayıt sistemi.

Özellikler:
    - Mesaj ve session kaydetme
    - Full-text search (FTS5) ile session ve mesaj arama
    - Session özetleme, konu çıkarımı, bilgi çıkarımı
    - Dışa aktarma ve arşivleme

Kullanım:
    >>> from chat_history import ChatHistoryManager, Message, SessionSummary
    >>> manager = ChatHistoryManager("chat.db")
    >>> manager.save_message("sess-001", "user", "Merhaba!")
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Veri modelleri
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """Tekil sohbet mesajı."""

    id: int
    session_id: str
    role: str  # user / assistant / system / tool
    content: str
    timestamp: datetime
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Message:
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            timestamp=cls._parse_dt(row["timestamp"]),
            tokens_used=row["tokens_used"] or 0,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    @staticmethod
    def _parse_dt(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if value:
            # SQLite varsayılan ISO formatı
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return datetime.utcnow()


@dataclass
class SessionSummary:
    """Session'ın kısa özeti (list_sessions için)."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    message_count: int
    topic_preview: str
    last_message_preview: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "message_count": self.message_count,
            "topic_preview": self.topic_preview,
            "last_message_preview": self.last_message_preview,
        }


# ---------------------------------------------------------------------------
# ChatHistoryManager
# ---------------------------------------------------------------------------

class ChatHistoryManager:
    """
    SQLite + FTS5 tabanlı sohbet geçmişi yönetimi.

    Args:
        db_path: SQLite veritabanı dosya yolu.
    """

    _INIT_SQL: str = """
    -- Ana mesaj tablosu
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        tokens_used INTEGER,
        metadata TEXT
    );

    -- Session meta tablosu
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        message_count INTEGER DEFAULT 0,
        topic TEXT,
        summary TEXT,
        archived BOOLEAN DEFAULT FALSE
    );

    -- FTS5 sanal tablosu (full-text search)
    -- 'content' ve 'session_id' alanları indekslenir.
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
        content, session_id,
        content_rowid='id',
        tokenize='porter unicode61'
    );

    -- Çıkarılan gerçekler (fact extraction)
    CREATE TABLE IF NOT EXISTS extracted_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        subject TEXT,
        predicate TEXT,
        object TEXT,
        confidence REAL DEFAULT 1.0,
        extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Çıkarılan tercihler (preference extraction)
    CREATE TABLE IF NOT EXISTS extracted_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        category TEXT,
        key TEXT,
        value TEXT,
        confidence REAL DEFAULT 1.0,
        extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Schema / bağlantı yardımcıları
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        """Yeni bir SQLite bağlantısı döndürür (row_factory=Row)."""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _ensure_schema(self) -> None:
        """Tabloları yoksa oluşturur."""
        with self._conn() as conn:
            conn.executescript(self._INIT_SQL)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        tokens_used: int = 0,
    ) -> int:
        """
        Yeni bir mesaj kaydeder; session meta verisini günceller;
        FTS5 indeksine de yazar.

        Returns:
            Eklenen mesajın ``id`` değeri.
        """
        if role not in {"user", "assistant", "system", "tool"}:
            raise ValueError(f"Bilinmeyen role: {role}")

        meta_json = json.dumps(metadata, ensure_ascii=False, default=str) if metadata else "{}"

        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, timestamp, tokens_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, datetime.utcnow(), tokens_used, meta_json),
            )
            message_id = cur.lastrowid

            # FTS5 senkronizasyonu
            conn.execute(
                "INSERT INTO messages_fts (rowid, content, session_id) VALUES (?, ?, ?)",
                (message_id, content, session_id),
            )

            # Session var mı kontrol et, yoksa oluştur
            sess = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if sess is None:
                conn.execute(
                    "INSERT INTO sessions (session_id, start_time) VALUES (?, ?)",
                    (session_id, datetime.utcnow()),
                )

            # Session istatistiklerini güncelle
            conn.execute(
                """
                UPDATE sessions
                SET end_time = ?,
                    message_count = (SELECT COUNT(*) FROM messages WHERE session_id = ?)
                WHERE session_id = ?
                """,
                (datetime.utcnow(), session_id, session_id),
            )
            conn.commit()

        return message_id  # type: ignore[return-value]

    def get_session(self, session_id: str, limit: Optional[int] = None) -> list[Message]:
        """
        Belirtilen session'a ait mesajları döndürür.

        Args:
            session_id: Session kimliği.
            limit: Döndürülecek maksimum mesaj sayısı (en yeniler).

        Returns:
            ``Message`` listesi (eskiden yeniye sıralı).
        """
        sql = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp"
        params: tuple[Any, ...] = (session_id,)
        if limit:
            sql += " LIMIT ?"
            params += (limit,)

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Message.from_row(r) for r in rows]

    def search_sessions(self, query: str) -> list[SessionSummary]:
        """
        FTS5 ile session'larda full-text arama yapar.
        Bir session içinde arama sorgusuyla eşleşen mesaj varsa
        o session özet olarak döndürülür.

        Args:
            query: Arama sorgusu (FTS5 query syntax destekler).

        Returns:
            Eşleşen ``SessionSummary`` listesi.
        """
        # FTS5 sorgusundan önce özel karakterleri temizle (basit escape)
        safe_query = query.replace("'", "''")

        with self._conn() as conn:
            # Eşleşen session_id'leri bul
            rows = conn.execute(
                """
                SELECT DISTINCT session_id FROM messages_fts
                WHERE messages_fts MATCH ?
                """,
                (safe_query,),
            ).fetchall()

            session_ids = [r["session_id"] for r in rows]
            if not session_ids:
                return []

            # Session özetlerini çek
            placeholders = ",".join("?" * len(session_ids))
            sess_rows = conn.execute(
                f"""
                SELECT
                    s.session_id,
                    s.start_time,
                    s.end_time,
                    s.message_count,
                    s.topic,
                    (SELECT content FROM messages
                     WHERE session_id = s.session_id
                     ORDER BY timestamp DESC LIMIT 1) AS last_msg
                FROM sessions s
                WHERE s.session_id IN ({placeholders})
                ORDER BY s.end_time DESC
                """,
                tuple(session_ids),
            ).fetchall()

        results: list[SessionSummary] = []
        for r in sess_rows:
            last_msg = r["last_msg"] or ""
            preview = last_msg[:120] + "..." if len(last_msg) > 120 else last_msg
            topic = r["topic"] or "Belirtilmemiş"
            results.append(
                SessionSummary(
                    session_id=r["session_id"],
                    start_time=Message._parse_dt(r["start_time"]),
                    end_time=Message._parse_dt(r["end_time"]) if r["end_time"] else None,
                    message_count=r["message_count"] or 0,
                    topic_preview=topic,
                    last_message_preview=preview,
                )
            )
        return results

    def search_messages(self, query: str) -> list[Message]:
        """
        FTS5 ile doğrudan mesaj içeriği arar.

        Args:
            query: Arama sorgusu.

        Returns:
            Eşleşen ``Message`` listesi (en yeniden eskiye).
        """
        safe_query = query.replace("'", "''")
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT m.* FROM messages m
                JOIN messages_fts fts ON m.id = fts.rowid
                WHERE messages_fts MATCH ?
                ORDER BY m.timestamp DESC
                """,
                (safe_query,),
            ).fetchall()
        return [Message.from_row(r) for r in rows]

    def list_sessions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[SessionSummary]:
        """
        Session'ları listeler; isteğe bağlı tarih aralığı ile filtreler.

        Args:
            start_date: Başlangıç tarihi (dahil).
            end_date: Bitiş tarihi (dahil).

        Returns:
            ``SessionSummary`` listesi.
        """
        conditions: list[str] = ["archived = FALSE"]
        params: list[Any] = []
        if start_date:
            conditions.append("start_time >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("start_time <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT
                s.session_id,
                s.start_time,
                s.end_time,
                s.message_count,
                s.topic,
                (SELECT content FROM messages
                 WHERE session_id = s.session_id
                 ORDER BY timestamp DESC LIMIT 1) AS last_msg
            FROM sessions s
            WHERE {where_clause}
            ORDER BY s.end_time DESC
        """

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        results: list[SessionSummary] = []
        for r in rows:
            last_msg = r["last_msg"] or ""
            preview = last_msg[:120] + "..." if len(last_msg) > 120 else last_msg
            topic = r["topic"] or "Belirtilmemiş"
            results.append(
                SessionSummary(
                    session_id=r["session_id"],
                    start_time=Message._parse_dt(r["start_time"]),
                    end_time=Message._parse_dt(r["end_time"]) if r["end_time"] else None,
                    message_count=r["message_count"] or 0,
                    topic_preview=topic,
                    last_message_preview=preview,
                )
            )
        return results

    def get_session_summary(self, session_id: str) -> str:
        """
        Session'ın tüm mesajlarını okuyup basit bir özet metni üretir.
        Gelişmiş özetleme için harici bir LLM çağrısı yapılabilir;
        burada basit bir heuristic kullanılır.

        Returns:
            Özet metin.
        """
        messages = self.get_session(session_id)
        if not messages:
            return "Bu session'da henüz mesaj yok."

        user_msgs = [m.content for m in messages if m.role == "user"]
        assistant_msgs = [m.content for m in messages if m.role == "assistant"]

        # Basit özet: ilk kullanıcı sorusu + son asistan yanıtı
        first_question = user_msgs[0] if user_msgs else "Bilinmiyor"
        last_answer = assistant_msgs[-1] if assistant_msgs else "Bilinmiyor"

        summary = (
            f"Session '{session_id}' özeti:\n"
            f"- Toplam mesaj: {len(messages)}\n"
            f"- İlk soru: {first_question[:200]}\n"
            f"- Son yanıt: {last_answer[:200]}\n"
        )

        # Session topic/summary alanını da güncelle
        topic_guess = first_question[:80] + "..." if len(first_question) > 80 else first_question
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET summary = ?, topic = ? WHERE session_id = ?",
                (summary, topic_guess, session_id),
            )
            conn.commit()

        return summary

    def get_topics_from_session(self, session_id: str) -> list[str]:
        """
        Session mesajlarından anahtar kelimeler / konular çıkarır.
        Basit bir token tabanlı yaklaşım; gelişmiş kullanım için
        LLM tabanlı ``conversation_indexer.extract_facts`` önerilir.

        Returns:
            Konu başlığı listesi.
        """
        messages = self.get_session(session_id)
        if not messages:
            return []

        all_text = " ".join(m.content for m in messages).lower()
        # Basit Türkçe stop-word listesi
        stop_words = {
            "bir", "ve", "ile", "için", "bu", "da", "de", "mi", "ki",
            "ben", "sen", "o", "biz", "siz", "onlar", "çok", "daha",
            "ne", "kadar", "gibi", "her", "tüm", "hiç", "ise", "ya",
            "ama", "fakat", "çünkü", "veya", "ise", "the", "a", "an",
            "is", "are", "was", "were", "to", "of", "in", "on", "at",
        }
        import re

        tokens = re.findall(r"[a-zçğıöşü0-9]+", all_text)
        freq: dict[str, int] = {}
        for t in tokens:
            if len(t) < 3 or t in stop_words:
                continue
            freq[t] = freq.get(t, 0) + 1

        # En sık geçen 10 kelimeyi konu olarak döndür
        sorted_topics = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:10]]

    def get_knowledge_from_session(self, session_id: str) -> list[dict[str, Any]]:
        """
        Session'dan çıkarılan bilgi parçalarını (facts) döndürür.

        Returns:
            Fact dictionary listesi.
        """
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT subject, predicate, object, confidence
                FROM extracted_facts
                WHERE session_id = ?
                ORDER BY confidence DESC
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "subject": r["subject"],
                "predicate": r["predicate"],
                "object": r["object"],
                "confidence": r["confidence"],
            }
            for r in rows
        ]

    def export_session(self, session_id: str, fmt: str = "json") -> str:
        """
        Session'ı dışa aktarır.

        Args:
            session_id: Session kimliği.
            fmt: ``json`` veya ``markdown``.

        Returns:
            Dışa aktarılan metin.
        """
        messages = self.get_session(session_id)
        if fmt == "json":
            payload = {
                "session_id": session_id,
                "exported_at": datetime.utcnow().isoformat(),
                "messages": [m.to_dict() for m in messages],
            }
            return json.dumps(payload, ensure_ascii=False, indent=2, default=str)

        if fmt == "markdown":
            lines = [f"# Session: {session_id}\n"]
            for m in messages:
                role_label = {"user": "Kullanıcı", "assistant": "Asistan", "system": "Sistem", "tool": "Araç"}.get(m.role, m.role)
                ts = m.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"## {role_label} ({ts})")
                lines.append(m.content)
                lines.append("")
            return "\n".join(lines)

        raise ValueError(f"Desteklenmeyen format: {fmt}")

    def delete_session(self, session_id: str) -> None:
        """
        Session ve bağlı tüm mesaj, fact, preference kayıtlarını siler.
        FTS5 indeksini de senkronize siler.
        """
        with self._conn() as conn:
            # FTS5 satırlarını sil (rowid üzerinden)
            conn.execute(
                "DELETE FROM messages_fts WHERE rowid IN (SELECT id FROM messages WHERE session_id = ?)",
                (session_id,),
            )
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM extracted_facts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM extracted_preferences WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    def archive_old_sessions(self, days: int = 30) -> int:
        """
        ``days`` günden eski session'ları arşivler (archived = TRUE).

        Returns:
            Arşivlenen session sayısı.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE sessions SET archived = TRUE WHERE end_time < ? AND archived = FALSE",
                (cutoff,),
            )
            conn.commit()
            return cur.rowcount

    # ------------------------------------------------------------------
    # Fact / Preference kaydetme (ConversationIndexer tarafından çağrılır)
    # ------------------------------------------------------------------

    def save_fact(
        self,
        session_id: str,
        subject: str,
        predicate: str,
        object_: str,
        confidence: float = 1.0,
    ) -> int:
        """
        Çıkarılan bir gerçeği kaydeder.

        Returns:
            Eklenen kaydın ``id`` değeri.
        """
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO extracted_facts (session_id, subject, predicate, object, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, subject, predicate, object_, confidence),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    def save_preference(
        self,
        session_id: str,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0,
    ) -> int:
        """
        Çıkarılan bir tercihi kaydeder.

        Returns:
            Eklenen kaydın ``id`` değeri.
        """
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO extracted_preferences (session_id, category, key, value, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, category, key, value, confidence),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Profil yükleme (user_profile.md vb.)
    # ------------------------------------------------------------------

    def load_user_profile_facts(self, profile_path: Path | str) -> int:
        """
        ``user_profile.md`` dosyasını okuyup satır satır fact olarak kaydeder.
        Format: ``- subject: predicate object`` veya ``- category: key = value``

        Returns:
            Kaydedilen fact/tercih sayısı.
        """
        path = Path(profile_path)
        if not path.exists():
            return 0

        count = 0
        session_id = f"profile-{uuid.uuid4().hex[:8]}"
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Basit parser: "- subject: predicate object"
                if line.startswith("-"):
                    line = line[1:].strip()
                if ":" in line:
                    parts = line.split(":", 1)
                    left = parts[0].strip()
                    right = parts[1].strip()
                    # preference format: "category: key = value"
                    if "=" in right:
                        k, v = right.split("=", 1)
                        self.save_preference(session_id, left, k.strip(), v.strip(), confidence=1.0)
                        count += 1
                    else:
                        # fact format: "subject: predicate object"
                        words = right.split(None, 1)
                        pred = words[0] if words else "bilinmiyor"
                        obj = words[1] if len(words) > 1 else ""
                        self.save_fact(session_id, left, pred, obj, confidence=1.0)
                        count += 1
        return count
