"""
RSS Reader Skill

Manage RSS/Atom feeds, fetch entries, and produce summaries.
Uses ``feedparser`` when available; falls back to raw XML parsing.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

try:
    import feedparser
    _HAS_FEEDPARSER = True
except Exception:
    _HAS_FEEDPARSER = False


DEFAULT_FEEDS: dict[str, str] = {
    "bbc_turkce": "https://feeds.bbci.co.uk/turkce/rss.xml",
    "webrazzi": "https://webrazzi.com/feed/",
    "hurriyet_teknoloji": "https://www.hurriyet.com.tr/rss/teknoloji",
    "cnnturk": "https://www.cnnturk.com/feed/rss/all/news",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*;q=0.9",
}


class RSSReaderSkill:
    """
    RSS / Atom feed aggregator with caching.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        default_max_items: int = 10,
        timeout: float = 20.0,
    ) -> None:
        self.default_max_items = default_max_items
        self.timeout = timeout
        self._feeds: dict[str, str] = dict(DEFAULT_FEEDS)
        self._cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".turkish_jarvis" / "rss_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # client lifecycle
    # ------------------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    # ------------------------------------------------------------------
    # feed management
    # ------------------------------------------------------------------
    def add_feed(self, name: str, url: str) -> None:
        """Add or overwrite a named feed."""
        self._feeds[name] = url

    def remove_feed(self, name: str) -> bool:
        """Remove a feed by name. Returns ``True`` if removed."""
        if name in self._feeds:
            del self._feeds[name]
            return True
        return False

    def list_feeds(self) -> dict[str, str]:
        """Return a copy of the feed registry."""
        return dict(self._feeds)

    # ------------------------------------------------------------------
    # fetch single feed
    # ------------------------------------------------------------------
    async def fetch_feed(
        self,
        name: str,
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch a single feed and return its entries.
        """
        if name not in self._feeds:
            return [{"error": f"Feed '{name}' not registered."}]

        url = self._feeds[name]
        limit = max_items if max_items is not None else self.default_max_items

        # Try cache first (1-hour TTL)
        cache_path = self._cache_dir / f"{name}_feed.json"
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    cached = json.load(f)
                cached_at = datetime.fromisoformat(cached.get("cached_at", "1970-01-01T00:00:00"))
                if (datetime.now(timezone.utc) - cached_at).total_seconds() < 3600:
                    return cached.get("entries", [])
            except Exception:
                pass

        client = await self._get_client()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return [{"error": f"Failed to fetch feed '{name}': {exc}"}]

        raw_xml = resp.text
        entries = self._parse_xml(raw_xml, limit)

        # Save cache
        try:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(
                    {
                        "name": name,
                        "url": url,
                        "cached_at": datetime.now(timezone.utc).isoformat(),
                        "entries": entries,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

        return entries

    def _parse_xml(self, raw_xml: str, limit: int) -> list[dict[str, Any]]:
        """Parse XML with feedparser or fallback to BeautifulSoup."""
        if _HAS_FEEDPARSER:
            return self._parse_with_feedparser(raw_xml, limit)
        return self._parse_with_bs4(raw_xml, limit)

    def _parse_with_feedparser(self, raw_xml: str, limit: int) -> list[dict[str, Any]]:
        parsed = feedparser.parse(raw_xml)
        entries: list[dict[str, Any]] = []

        for entry in parsed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            # Clean HTML in summary
            if summary:
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text(separator=" ", strip=True)
            published = entry.get("published", "") or entry.get("updated", "")
            entries.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published": published,
                }
            )

        return entries

    def _parse_with_bs4(self, raw_xml: str, limit: int) -> list[dict[str, Any]]:
        soup = BeautifulSoup(raw_xml, "xml")
        entries: list[dict[str, Any]] = []

        # Try RSS <item>
        items = soup.find_all("item")[:limit]
        if not items:
            # Try Atom <entry>
            items = soup.find_all("entry")[:limit]

        for item in items:
            title_tag = item.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            link_tag = item.find("link")
            link = ""
            if link_tag:
                link = link_tag.get("href", "") or link_tag.get_text(strip=True)

            summary_tag = item.find("description") or item.find("summary") or item.find("content")
            summary = ""
            if summary_tag:
                summary = summary_tag.get_text(separator=" ", strip=True)

            pub_tag = item.find("pubDate") or item.find("published") or item.find("updated")
            published = pub_tag.get_text(strip=True) if pub_tag else ""

            entries.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "published": published,
                }
            )

        return entries

    # ------------------------------------------------------------------
    # fetch all feeds
    # ------------------------------------------------------------------
    async def fetch_all(
        self,
        max_items: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch every registered feed and return ``name -> entries``.
        """
        from asyncio import gather

        names = list(self._feeds.keys())
        tasks = [self.fetch_feed(name, max_items) for name in names]
        results = await gather(*tasks, return_exceptions=True)

        out: dict[str, list[dict[str, Any]]] = {}
        for name, result in zip(names, results):
            if isinstance(result, list):
                out[name] = result
            else:
                out[name] = [{"error": str(result)}]

        return out

    # ------------------------------------------------------------------
    # summary
    # ------------------------------------------------------------------
    async def get_summary(self, max_items_per_feed: int = 5) -> str:
        """
        Return a concise Turkish text summary of all feeds.
        """
        all_feeds = await self.fetch_all(max_items=max_items_per_feed)
        lines: list[str] = []

        for name, entries in all_feeds.items():
            if not entries:
                continue
            lines.append(f"\n=== {name.upper()} ===")
            for entry in entries[:max_items_per_feed]:
                if "error" in entry:
                    lines.append(f"  HATA: {entry['error']}")
                    continue
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                published = entry.get("published", "")
                piece = f"  • {title}"
                if summary:
                    snippet = summary[:120]
                    if len(summary) > 120:
                        snippet += "…"
                    piece += f" — {snippet}"
                if published:
                    piece += f" ({published})"
                lines.append(piece)

        return "\n".join(lines)
