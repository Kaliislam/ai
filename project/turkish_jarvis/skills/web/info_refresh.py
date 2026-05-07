"""
Info Refresh Skill

Periodically refreshes knowledge by scraping the web and
caching results for later retrieval (simple JSON cache).

Integrates with WebSearchSkill to fetch fresh data and
maintains a lightweight local knowledge store.
"""

from __future__ import annotations

import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any

from .web_search_advanced import WebSearchSkill


DEFAULT_CACHE_DIR = Path.home() / ".turkish_jarvis" / "web_cache"
DEFAULT_TOPICS = ["teknoloji", "bilim", "ekonomi", "spor", "sağlık"]


class InfoRefreshSkill:
    """
    Fetches, caches, and refreshes fresh web information.
    """

    def __init__(
        self,
        web_skill: WebSearchSkill | None = None,
        cache_dir: str | Path | None = None,
        default_ttl_hours: float = 24.0,
    ) -> None:
        self.web_skill = web_skill or WebSearchSkill()
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours
        self._user_interests: list[str] = []
        self._schedules: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # internal cache helpers
    # ------------------------------------------------------------------
    def _cache_path(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()[:16] + ".json"
        return self.cache_dir / safe

    def _load_cache(self, key: str) -> dict[str, Any] | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_cache(self, key: str, data: dict[str, Any]) -> None:
        path = self._cache_path(key)
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _is_fresh(self, data: dict[str, Any]) -> bool:
        ts_str = data.get("cached_at", "")
        if not ts_str:
            return False
        try:
            cached = datetime.fromisoformat(ts_str)
            ttl = timedelta(hours=self.default_ttl_hours)
            return datetime.now(timezone.utc) - cached < ttl
        except Exception:
            return False

    # ------------------------------------------------------------------
    # refresh a single topic
    # ------------------------------------------------------------------
    async def refresh_topic(
        self,
        topic: str,
        engines: list[str] | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """
        Gather fresh results for *topic* across multiple engines and cache them.
        """
        cache_key = f"topic:{topic}"
        cached = self._load_cache(cache_key)
        if cached and self._is_fresh(cached):
            return cached

        if engines is None:
            engines = ["duckduckgo", "news"]

        raw = await self.web_skill.search_all(topic, engines=engines, max_results=max_results)

        payload = {
            "topic": topic,
            "engines": engines,
            "results": raw,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": self.default_ttl_hours,
        }
        self._save_cache(cache_key, payload)
        return payload

    # ------------------------------------------------------------------
    # daily auto-refresh
    # ------------------------------------------------------------------
    async def refresh_daily(
        self,
        topics: list[str] | None = None,
        max_results: int = 8,
    ) -> dict[str, dict[str, Any]]:
        """
        Refresh a default set of daily topics (technology, science, economy, etc.).
        Returns a mapping ``topic -> payload``.
        """
        if topics is None:
            topics = DEFAULT_TOPICS.copy()

        results: dict[str, dict[str, Any]] = {}
        semaphore = asyncio.Semaphore(3)

        async def _refresh_one(t: str) -> tuple[str, dict[str, Any]]:
            async with semaphore:
                return t, await self.refresh_topic(t, max_results=max_results)

        tasks = [asyncio.create_task(_refresh_one(t)) for t in topics]
        for task in tasks:
            topic, payload = await task
            results[topic] = payload

        return results

    # ------------------------------------------------------------------
    # user-interest refresh
    # ------------------------------------------------------------------
    def set_user_interests(self, interests: list[str]) -> None:
        """Store the user's areas of interest."""
        self._user_interests = list(interests)

    async def refresh_user_interests(
        self,
        max_results: int = 8,
    ) -> dict[str, dict[str, Any]]:
        """
        Refresh topics derived from user interests.
        """
        if not self._user_interests:
            return {}
        return await self.refresh_daily(topics=self._user_interests, max_results=max_results)

    # ------------------------------------------------------------------
    # periodic scheduling (in-memory; caller runs the loop)
    # ------------------------------------------------------------------
    def schedule_refresh(
        self,
        topics: list[str],
        interval_hours: float = 24.0,
    ) -> list[dict[str, Any]]:
        """
        Register a periodic refresh schedule.
        Returns the schedule list; the caller should invoke ``run_scheduled()``
        inside an asyncio event loop.
        """
        schedule = {
            "topics": list(topics),
            "interval_hours": interval_hours,
            "last_run": None,
        }
        self._schedules.append(schedule)
        return self._schedules

    async def run_scheduled(self) -> dict[str, dict[str, Any]]:
        """
        Check all registered schedules and refresh those whose interval has passed.
        """
        now = datetime.now(timezone.utc)
        all_results: dict[str, dict[str, Any]] = {}

        for sched in self._schedules:
            last = sched["last_run"]
            delta = timedelta(hours=sched["interval_hours"])
            if last is None or (now - datetime.fromisoformat(last)) >= delta:
                for topic in sched["topics"]:
                    payload = await self.refresh_topic(topic)
                    all_results[topic] = payload
                sched["last_run"] = now.isoformat()

        return all_results

    # ------------------------------------------------------------------
    # RAG-like fresh-info gate
    # ------------------------------------------------------------------
    async def get_fresh_info(
        self,
        query: str,
        rag_checker: Any | None = None,
    ) -> dict[str, Any]:
        """
        If a *rag_checker* callable is provided and returns a truthy value,
        the cached result is returned directly.
        Otherwise, search the web, cache the result, and return it.

        ``rag_checker`` signature: ``rag_checker(query) -> bool | dict | None``
        """
        cache_key = f"query:{query}"
        cached = self._load_cache(cache_key)

        # External RAG lookup
        if rag_checker is not None:
            try:
                rag_result = rag_checker(query)
                # If async callable
                if asyncio.iscoroutine(rag_result):
                    rag_result = await rag_result
                if rag_result:
                    return {
                        "query": query,
                        "source": "rag",
                        "result": rag_result,
                        "cached": True,
                    }
            except Exception:
                pass

        if cached and self._is_fresh(cached):
            return {
                "query": query,
                "source": "cache",
                "result": cached,
                "cached": True,
            }

        # Web fallback
        web_results = await self.web_skill.search_all(query, max_results=10)
        payload = {
            "query": query,
            "web_results": web_results,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": self.default_ttl_hours,
        }
        self._save_cache(cache_key, payload)

        return {
            "query": query,
            "source": "web",
            "result": payload,
            "cached": False,
        }

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    async def close(self) -> None:
        await self.web_skill.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()
