"""
Conversation Indexer - ChromaDB ile anlamsal indeksleme ve bilgi çıkarımı.

Özellikler:
    - Session'ları vektör olarak indeksleme
    - Semantic search (anlamsal arama)
    - Fact extraction (gerçek çıkarımı)
    - Preference extraction (tercih çıkarımı)
    - Kullanıcı profili oluşturma

Kullanım:
    >>> from conversation_indexer import ConversationIndexer, Fact, Preference, UserProfile
    >>> indexer = ConversationIndexer(chat_manager)
    >>> indexer.index_session("sess-001")
    >>> results = indexer.semantic_search("geçen hafta ne konuşmuştuk")
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Opsiyonel bağımlılıklar
# ---------------------------------------------------------------------------

try:
    import chromadb
    from chromadb.config import Settings
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False
    chromadb = None  # type: ignore[assignment]

try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Veri modelleri
# ---------------------------------------------------------------------------

@dataclass
class Fact:
    """Çıkarılan gerçek (fact)."""

    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source_session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Preference:
    """Çıkarılan tercih (preference)."""

    category: str  # hitap, renk, yemek, vb.
    key: str
    value: str
    confidence: float = 1.0
    source_session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserProfile:
    """Tüm geçmişten oluşturulan kullanıcı profili."""

    total_sessions: int = 0
    total_messages: int = 0
    facts: list[Fact] = field(default_factory=list)
    preferences: list[Preference] = field(default_factory=list)
    common_topics: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sessions": self.total_sessions,
            "total_messages": self.total_messages,
            "facts": [f.to_dict() for f in self.facts],
            "preferences": [p.to_dict() for p in self.preferences],
            "common_topics": self.common_topics,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# ConversationIndexer
# ---------------------------------------------------------------------------

class ConversationIndexer:
    """
    ChromaDB ve sentence-transformers ile konuşma indeksleme.

    Args:
        chat_manager: ``ChatHistoryManager`` örneği.
        chroma_dir: ChromaDB persist dizini.
        model_name: Embedding modeli (sentence-transformers).
    """

    # LLM extraction için basit Türkçe kalıplar
    _FACT_PATTERNS = [
        # "... yaşıyor ..."
        re.compile(r"(\w+)\s+(yaşıyor|yaşar|yaşıyorum|yaşıyorsun)\s+(\w+)", re.IGNORECASE),
        # "... seviyor ..."
        re.compile(r"(\w+)\s+(seviyor|seviyorum|seviyorsun|sevdiğim|sevdiği)\s+(\w+)", re.IGNORECASE),
        # "... çalışıyor ..."
        re.compile(r"(\w+)\s+(çalışıyor|çalışır|çalışıyorum|çalışıyorsun)\s+(\w+)", re.IGNORECASE),
        # "... adı ..."
        re.compile(r"adı[n]?\s+(\w+)", re.IGNORECASE),
        # "... hobisi ..."
        re.compile(r"hobisi\s+(\w+)", re.IGNORECASE),
    ]

    _PREFERENCE_PATTERNS = [
        # "... severim"
        re.compile(r"(\w+)\s+severim", re.IGNORECASE),
        # "... sevmem"
        re.compile(r"(\w+)\s+sevmem", re.IGNORECASE),
        # "... hoşlanırım"
        re.compile(r"(\w+)\s+hoşlanırım", re.IGNORECASE),
        # "... istemem"
        re.compile(r"(\w+)\s+istemem", re.IGNORECASE),
        # "... tercih ederim"
        re.compile(r"(\w+)\s+tercih\s+ederim", re.IGNORECASE),
    ]

    def __init__(
        self,
        chat_manager: Any,
        chroma_dir: str | Path = "/mnt/agents/output/project/chroma_db",
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        self.chat_manager = chat_manager
        self.chroma_dir = Path(chroma_dir)
        self.model_name = model_name

        # ChromaDB istemci
        self._chroma_client: Any = None
        self._collection: Any = None
        self._model: Any = None

        self._init_chroma()

    def _init_chroma(self) -> None:
        """ChromaDB istemcisini ve embedding modelini başlatır."""
        if not _CHROMADB_AVAILABLE:
            import warnings
            warnings.warn("ChromaDB yüklü değil. Semantic search devre dışı.", stacklevel=2)
            return

        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._chroma_client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.chroma_dir),
                anonymized_telemetry=False,
            )
        )
        self._collection = self._chroma_client.get_or_create_collection(
            name="conversations",
            metadata={"hnsw:space": "cosine"},
        )

        if _SENTENCE_TRANSFORMERS_AVAILABLE:
            self._model = SentenceTransformer(self.model_name)
        else:
            import warnings
            warnings.warn("sentence-transformers yüklü değil. Basit embedding kullanılacak.", stacklevel=2)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Metin(ler)i embedding vektörüne dönüştürür."""
        if self._model is not None:
            return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()

        # Basit fallback: TF-IDF benzeri rastgele seedli vektör
        # (Gerçek uygulamada mutlaka sentence-transformers yüklenmeli)
        import hashlib

        dim = 384
        vectors = []
        for text in texts:
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
            import random

            rng = random.Random(seed)
            vec = [rng.random() for _ in range(dim)]
            # normalize
            norm = sum(x * x for x in vec) ** 0.5
            vec = [x / norm for x in vec] if norm else vec
            vectors.append(vec)
        return vectors

    # ------------------------------------------------------------------
    # İndeksleme
    # ------------------------------------------------------------------

    def index_session(self, session_id: str) -> int:
        """
        Bir session'daki tüm mesajları ChromaDB'ye ekler.

        Returns:
            İndekslenen mesaj sayısı.
        """
        if not _CHROMADB_AVAILABLE or self._collection is None:
            return 0

        messages = self.chat_manager.get_session(session_id)
        if not messages:
            return 0

        # Sadece user ve assistant mesajlarını indeksle
        indexable = [m for m in messages if m.role in {"user", "assistant"}]
        if not indexable:
            return 0

        ids = [f"{session_id}-{m.id}" for m in indexable]
        texts = [m.content for m in indexable]
        embeddings = self._embed(texts)
        metadatas = [
            {
                "session_id": session_id,
                "role": m.role,
                "timestamp": m.timestamp.isoformat(),
                "message_id": m.id,
            }
            for m in indexable
        ]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(indexable)

    # ------------------------------------------------------------------
    # Anlamsal arama
    # ------------------------------------------------------------------

    def semantic_search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """
        ChromaDB üzerinde anlamsal arama yapar.

        Args:
            query: Arama sorgusu.
            k: Döndürülecek sonuç sayısı.

        Returns:
            Her sonuç ``{session_id, role, content, distance, timestamp}`` içerir.
        """
        if not _CHROMADB_AVAILABLE or self._collection is None:
            return []

        query_embedding = self._embed([query])[0]
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        out: list[dict[str, Any]] = []
        if results["ids"] and results["ids"][0]:
            for idx, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][idx] if results["metadatas"] else {}
                dist = results["distances"][0][idx] if results["distances"] else None
                content = results["documents"][0][idx] if results["documents"] else ""
                out.append(
                    {
                        "id": doc_id,
                        "session_id": meta.get("session_id", ""),
                        "role": meta.get("role", ""),
                        "content": content,
                        "distance": dist,
                        "timestamp": meta.get("timestamp", ""),
                    }
                )
        return out

    def find_related_sessions(self, topic: str, k: int = 5) -> list[str]:
        """
        Belirli bir konuyla ilgili session ID'lerini döndürür.

        Args:
            topic: Aranacak konu/anahtar kelime.
            k: Döndürülecek maksimum session sayısı.

        Returns:
            Benzersiz session ID listesi.
        """
        results = self.semantic_search(topic, k=k * 3)  # fazla çek, unique al
        seen: set[str] = set()
        out: list[str] = []
        for r in results:
            sid = r.get("session_id", "")
            if sid and sid not in seen:
                seen.add(sid)
                out.append(sid)
                if len(out) >= k:
                    break
        return out

    # ------------------------------------------------------------------
    # Bilgi çıkarımı
    # ------------------------------------------------------------------

    def extract_facts(self, session_id: str) -> list[Fact]:
        """
        Session mesajlarından gerçek (fact) çıkarır.
        Basit rule-based extraction; LLM entegrasyonu sonradan eklenebilir.

        Returns:
            ``Fact`` listesi.
        """
        messages = self.chat_manager.get_session(session_id)
        facts: list[Fact] = []

        for m in messages:
            if m.role != "user":
                continue
            text = m.content

            # Pattern matching
            for pat in self._FACT_PATTERNS:
                for match in pat.finditer(text):
                    groups = match.groups()
                    if len(groups) >= 2:
                        subject = groups[0].strip()
                        predicate = groups[1].strip() if len(groups) > 1 else "bilinmiyor"
                        object_ = groups[2].strip() if len(groups) > 2 else ""
                        fact = Fact(
                            subject=subject,
                            predicate=predicate,
                            object=object_,
                            confidence=0.7,
                            source_session_id=session_id,
                        )
                        facts.append(fact)
                        # ChatHistoryManager'a da kaydet
                        self.chat_manager.save_fact(
                            session_id, subject, predicate, object_, confidence=0.7
                        )

            # Özel pattern: "yaşım ..." / "yaşı ..."
            age_match = re.search(r"yaşım?\s+(\d+)", text, re.IGNORECASE)
            if age_match:
                age = age_match.group(1)
                facts.append(
                    Fact("kullanıcı", "yaşı", age, 0.8, session_id)
                )
                self.chat_manager.save_fact(session_id, "kullanıcı", "yaşı", age, 0.8)

            # "...'de yaşıyorum" / "...'da yaşıyorum"
            loc_match = re.search(r"(\w+(?:\s+\w+)?)\s+(?:de|da)\s+yaşıyorum", text, re.IGNORECASE)
            if loc_match:
                loc = loc_match.group(1).strip()
                facts.append(Fact("kullanıcı", "yaşıyor", loc, 0.8, session_id))
                self.chat_manager.save_fact(session_id, "kullanıcı", "yaşıyor", loc, 0.8)

        return facts

    def extract_preferences(self, session_id: str) -> list[Preference]:
        """
        Session mesajlarından tercih (preference) çıkarır.

        Returns:
            ``Preference`` listesi.
        """
        messages = self.chat_manager.get_session(session_id)
        prefs: list[Preference] = []

        for m in messages:
            if m.role != "user":
                continue
            text = m.content

            for pat in self._PREFERENCE_PATTERNS:
                for match in pat.finditer(text):
                    groups = match.groups()
                    if groups:
                        item = groups[0].strip()
                        # olumlu / olumsuz belirle
                        if "sevmem" in text.lower() or "istemem" in text.lower():
                            value = "sevmiyor"
                            confidence = 0.75
                        else:
                            value = "seviyor"
                            confidence = 0.75

                        pref = Preference(
                            category="genel",
                            key=item,
                            value=value,
                            confidence=confidence,
                            source_session_id=session_id,
                        )
                        prefs.append(pref)
                        self.chat_manager.save_preference(
                            session_id, "genel", item, value, confidence
                        )

            # Renk tercihi
            color_match = re.search(
                r"(kırmızı|mavi|yeşil|sarı|beyaz|siyah|mor|turuncu|pembe|gri)\s+" +
                r"(renk|rengi|seviyorum|severim|hoşlanırım|sevmem|hoşlanmam)",
                text,
                re.IGNORECASE,
            )
            if color_match:
                color = color_match.group(1).lower()
                action = color_match.group(2).lower()
                value = "seviyor" if action in {"seviyorum", "severim", "hoşlanırım"} else "sevmiyor"
                pref = Preference("renk", color, value, 0.8, session_id)
                prefs.append(pref)
                self.chat_manager.save_preference(session_id, "renk", color, value, 0.8)

            # Hitap tercihi
            hitap_match = re.search(
                r"(sen|sana|bana)\s+(\w+)\s+de\s*" +
                r"|(hitap\s+et|çağır|seslen|diye\s+çağır)",
                text,
                re.IGNORECASE,
            )
            if hitap_match:
                # Çok basit: "bana X de" gibi
                simple_hitap = re.search(r"bana\s+(\w+)\s+de", text, re.IGNORECASE)
                if simple_hitap:
                    name = simple_hitap.group(1).strip()
                    pref = Preference("hitap", "isim", name, 0.7, session_id)
                    prefs.append(pref)
                    self.chat_manager.save_preference(session_id, "hitap", "isim", name, 0.7)

        return prefs

    # ------------------------------------------------------------------
    # Kullanıcı profili
    # ------------------------------------------------------------------

    def build_user_profile(self) -> UserProfile:
        """
        Tüm geçmiş session'lardan kullanıcı profili oluşturur.

        Returns:
            ``UserProfile`` nesnesi.
        """
        sessions = self.chat_manager.list_sessions()
        all_facts: list[Fact] = []
        all_prefs: list[Preference] = []
        all_topics: list[str] = []

        for sess in sessions:
            facts = self.extract_facts(sess.session_id)
            prefs = self.extract_preferences(sess.session_id)
            topics = self.chat_manager.get_topics_from_session(sess.session_id)

            all_facts.extend(facts)
            all_prefs.extend(prefs)
            all_topics.extend(topics)

        # Tekrar eden konuları birleştir, en sık olanları al
        topic_freq: dict[str, int] = {}
        for t in all_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1
        common_topics = sorted(topic_freq, key=lambda x: topic_freq[x], reverse=True)[:20]

        total_messages = sum(s.message_count for s in sessions)

        return UserProfile(
            total_sessions=len(sessions),
            total_messages=total_messages,
            facts=all_facts,
            preferences=all_prefs,
            common_topics=common_topics,
        )

    def persist_user_profile(self, profile_path: str | Path = "/mnt/agents/output/project/user_profile.md") -> Path:
        """
        Oluşturulan profili ``user_profile.md`` dosyasına yazar.

        Returns:
            Yazılan dosyanın yolu.
        """
        profile = self.build_user_profile()
        path = Path(profile_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = ["# Kullanıcı Profili\n", f"Oluşturulma: {profile.created_at.isoformat()}\n"]
        lines.append(f"## İstatistikler\n")
        lines.append(f"- Toplam session: {profile.total_sessions}\n")
        lines.append(f"- Toplam mesaj: {profile.total_messages}\n")

        lines.append(f"\n## Bilinen Gerçekler\n")
        for f in profile.facts:
            lines.append(f"- {f.subject}: {f.predicate} {f.object} (güven: {f.confidence})\n")

        lines.append(f"\n## Tercihler\n")
        for p in profile.preferences:
            lines.append(f"- {p.category}: {p.key} = {p.value} (güven: {p.confidence})\n")

        lines.append(f"\n## Sık Konuşulan Konular\n")
        for t in profile.common_topics:
            lines.append(f"- {t}\n")

        path.write_text("".join(lines), encoding="utf-8")
        return path
