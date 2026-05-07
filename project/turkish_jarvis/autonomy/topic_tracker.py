"""Topic Tracker — konu takip ve trend skorlama sistemi."""

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("jarvis.topic_tracker")


@dataclass
class TrackedTopic:
    """Takip edilen bir konunun durumu."""
    topic: str
    added_at: str
    last_update: str
    update_count: int = 0
    trend_score: float = 0.0
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1-5 arası, 5 en yüksek

    def bump_update(self, source: str = ""):
        """Bir güncelleme kaydet."""
        self.last_update = datetime.now().isoformat()
        self.update_count += 1
        if source and source not in self.sources:
            self.sources.append(source)
        # Trend skoru: son güncelleme yakınlığı + update sıklığı
        self.trend_score = self._compute_trend_score()

    def _compute_trend_score(self) -> float:
        """Basit trend skoru."""
        try:
            last = datetime.fromisoformat(self.last_update)
        except Exception:
            last = datetime.now()
        hours_ago = (datetime.now() - last).total_seconds() / 3600
        recency = max(0, 100 - hours_ago * 2)
        frequency = self.update_count * 5
        return round(recency + frequency, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "added_at": self.added_at,
            "last_update": self.last_update,
            "update_count": self.update_count,
            "trend_score": self.trend_score,
            "sources": self.sources,
            "tags": self.tags,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedTopic":
        obj = cls(
            topic=data["topic"],
            added_at=data["added_at"],
            last_update=data["last_update"],
            update_count=data.get("update_count", 0),
            trend_score=data.get("trend_score", 0.0),
            sources=data.get("sources", []),
            tags=data.get("tags", []),
            priority=data.get("priority", 1),
        )
        return obj


@dataclass
class TopicUpdate:
    """Bir konudaki tek güncelleme."""
    topic: str
    source: str
    title: str
    url: str
    snippet: str
    timestamp: str
    sentiment: Optional[str] = None  # 'positive', 'negative', 'neutral'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "timestamp": self.timestamp,
            "sentiment": self.sentiment,
        }


class TopicTracker:
    """
    Konu takip sistemi.

    - ``track_topic(topic)`` — Bir konuyu takibe al.
    - ``untrack_topic(topic)`` — Takibi bırak.
    - ``get_updates()`` — Takip edilen konulardaki güncellemeler.
    - ``get_trending()`` — Trend skorlarına göre sıralı konular.
    """

    def __init__(
        self,
        search_engine=None,
        knowledge_miner=None,
        data_dir: str = "./data",
    ):
        self.search = search_engine
        self.miner = knowledge_miner
        self.topics: Dict[str, TrackedTopic] = {}
        self.updates: List[TopicUpdate] = []
        self._lock = None  # lazy asyncio.Lock

        self.data_dir = Path(data_dir)
        self.topics_path = self.data_dir / "tracked_topics.json"
        self.updates_path = self.data_dir / "topic_updates.json"
        self._ensure_data_dir()
        self._load()

    # ------------------------------------------------------------------ #
    #  Core tracking API
    # ------------------------------------------------------------------ #

    def track_topic(
        self,
        topic: str,
        tags: Optional[List[str]] = None,
        priority: int = 1,
    ) -> TrackedTopic:
        """Bir konuyu takibe al."""
        topic = topic.strip().lower()
        if topic in self.topics:
            logger.info("Topic '%s' zaten takipte.", topic)
            return self.topics[topic]

        now = datetime.now().isoformat()
        tracked = TrackedTopic(
            topic=topic,
            added_at=now,
            last_update=now,
            tags=tags or [],
            priority=priority,
        )
        self.topics[topic] = tracked
        self._save()
        logger.info("🔔 Konu takibe alındı: %s", topic)
        return tracked

    def untrack_topic(self, topic: str) -> bool:
        """Bir konunun takibini bırak."""
        topic = topic.strip().lower()
        if topic in self.topics:
            del self.topics[topic]
            self._save()
            logger.info("🔕 Konu takibi bırakıldı: %s", topic)
            return True
        return False

    def list_topics(self) -> List[TrackedTopic]:
        """Tüm takip edilen konuları listele."""
        return list(self.topics.values())

    def get_topic(self, topic: str) -> Optional[TrackedTopic]:
        """Tek bir konunun durumunu döndür."""
        return self.topics.get(topic.strip().lower())

    # ------------------------------------------------------------------ #
    #  Updates
    # ------------------------------------------------------------------ #

    async def get_updates(
        self,
        limit: int = 20,
        since_hours: Optional[int] = None,
    ) -> List[TopicUpdate]:
        """Takip edilen konulardaki güncellemeleri getir."""
        # Önce internetten taze güncellemeleri çek
        if self.search or self.miner:
            await self._fetch_fresh_updates()

        # Bellekteki güncellemeleri filtrele
        updates = self.updates[::-1]  # en yeniden eskiye
        if since_hours is not None:
            cutoff = datetime.now() - timedelta(hours=since_hours)
            updates = [
                u
                for u in updates
                if datetime.fromisoformat(u.timestamp) > cutoff
            ]
        return updates[:limit]

    async def _fetch_fresh_updates(self):
        """Takip edilen konular için internetten güncelleme çek."""
        if not self.topics:
            return

        for tracked in list(self.topics.values())[:10]:
            try:
                results = []
                if self.search and hasattr(self.search, "search"):
                    raw = await self.search.search(tracked.topic, max_results=5)
                    for r in raw:
                        results.append({
                            "title": getattr(r, "title", "") or str(r),
                            "url": getattr(r, "url", ""),
                            "snippet": getattr(r, "snippet", ""),
                            "source": getattr(r, "source", "web"),
                        })

                elif self.miner and hasattr(self.miner, "web_search"):
                    raw = await self.miner.web_search(tracked.topic, max_results=5)
                    for r in raw:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("snippet", ""),
                            "source": r.get("source", "web"),
                        })

                # Yeni sonuçları ekle
                for item in results:
                    if not any(
                        u.url == item["url"]
                        for u in self.updates
                        if u.topic == tracked.topic
                    ):
                        update = TopicUpdate(
                            topic=tracked.topic,
                            source=item["source"],
                            title=item["title"],
                            url=item["url"],
                            snippet=item["snippet"],
                            timestamp=datetime.now().isoformat(),
                        )
                        self.updates.append(update)
                        tracked.bump_update(source=item["source"])

            except Exception as exc:
                logger.debug("Fetch error for '%s': %s", tracked.topic, exc)

        self._save()

    # ------------------------------------------------------------------ #
    #  Trending
    # ------------------------------------------------------------------ #

    def get_trending(
        self,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> List[TrackedTopic]:
        """Trend skorlarına göre sıralı konuları döndür."""
        # Skorları yeniden hesapla
        for t in self.topics.values():
            t.trend_score = t._compute_trend_score()

        sorted_topics = sorted(
            self.topics.values(),
            key=lambda x: (x.trend_score, x.priority),
            reverse=True,
        )
        filtered = [t for t in sorted_topics if t.trend_score >= min_score]
        return filtered[:limit]

    def get_trending_report(self, limit: int = 10) -> str:
        """İnsan-okunabilir trend raporu."""
        topics = self.get_trending(limit=limit)
        if not topics:
            return "Henüz takip edilen konu yok veya güncelleme bulunamadı."
        lines = ["📈 Trend Raporu", "=" * 40]
        for i, t in enumerate(topics, 1):
            lines.append(
                f"{i}. {t.topic.title()}"
                f"   (skor={t.trend_score}, "
                f"güncelleme={t.update_count}, "
                f"öncelik={t.priority})"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Analytics
    # ------------------------------------------------------------------ #

    def get_stats(self) -> Dict[str, Any]:
        """Takip sisteminin istatistikleri."""
        if not self.topics:
            return {"total_topics": 0, "total_updates": 0, "avg_score": 0.0}
        scores = [t.trend_score for t in self.topics.values()]
        return {
            "total_topics": len(self.topics),
            "total_updates": len(self.updates),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": round(max(scores), 2),
            "top_topic": max(self.topics.values(), key=lambda x: x.trend_score).topic,
        }

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _ensure_data_dir(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        """Diskten takip edilen konuları ve güncellemeleri yükle."""
        if self.topics_path.exists():
            try:
                data = json.loads(self.topics_path.read_text())
                for k, v in data.items():
                    self.topics[k] = TrackedTopic.from_dict(v)
            except Exception as exc:
                logger.warning("TopicTracker load error: %s", exc)

        if self.updates_path.exists():
            try:
                raw = json.loads(self.updates_path.read_text())
                self.updates = [TopicUpdate(**u) for u in raw]
            except Exception as exc:
                logger.warning("TopicTracker updates load error: %s", exc)

    def _save(self):
        """Diske kaydet."""
        self._ensure_data_dir()
        self.topics_path.write_text(
            json.dumps({k: v.to_dict() for k, v in self.topics.items()}, indent=2)
        )
        self.updates_path.write_text(
            json.dumps([u.to_dict() for u in self.updates[-500:]], indent=2)
        )
