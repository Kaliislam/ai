"""News APIs — free tiers, API keys required but free."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import httpx


@dataclass
class NewsResult:
    """Unified news article result."""

    title: str
    url: str
    snippet: str
    source: str
    score: float = 0.0
    published_at: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Per-domain rate limiter."""

    def __init__(self, default_delay: float = 1.0):
        self._last_request: Dict[str, float] = {}
        self._default_delay = default_delay
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str, custom_delay: Optional[float] = None):
        async with self._lock:
            now = time.time()
            delay = custom_delay or self._default_delay
            last = self._last_request.get(domain, 0)
            wait = max(0, delay - (now - last))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request[domain] = time.time()


class NewsAPISearch:
    """NewsAPI.org — free 100 requests/day, API key required (free tier)."""

    API_URL = "https://newsapi.org/v2/everything"
    TOP_URL = "https://newsapi.org/v2/top-headlines"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10, language: str = "en", sort_by: str = "relevancy") -> List[NewsResult]:
        """Search all news via NewsAPI."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="NewsAPI: no API key configured", source="newsapi", score=0.0)]
        await self.limiter.acquire("newsapi.org", 1.0)
        params: Dict[str, Any] = {
            "q": query,
            "apiKey": self.api_key,
            "pageSize": min(max_results, 100),
            "language": language,
            "sortBy": sort_by,
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"NewsAPI error: {e}", source="newsapi", score=0.0)]

    async def top_headlines(self, country: str = "tr", category: Optional[str] = None, max_results: int = 10) -> List[NewsResult]:
        """Get top headlines."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="NewsAPI: no API key configured", source="newsapi", score=0.0)]
        await self.limiter.acquire("newsapi.org", 1.0)
        params: Dict[str, Any] = {"apiKey": self.api_key, "pageSize": min(max_results, 100), "country": country}
        if category:
            params["category"] = category
        try:
            resp = await self.client.get(self.TOP_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"NewsAPI headlines error: {e}", source="newsapi", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[NewsResult]:
        results: List[NewsResult] = []
        for item in data.get("articles", [])[:max_results]:
            results.append(
                NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", "") or "",
                    source="newsapi",
                    score=0.9,
                    published_at=item.get("publishedAt"),
                    author=item.get("author"),
                    image_url=item.get("urlToImage"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class GNewsSearch:
    """GNews.io — free 100 requests/day, API key required (free tier)."""

    API_URL = "https://gnews.io/api/v4/search"
    TOP_URL = "https://gnews.io/api/v4/top-headlines"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10, language: str = "tr", country: str = "tr") -> List[NewsResult]:
        """Search via GNews."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="GNews: no API key configured", source="gnews", score=0.0)]
        await self.limiter.acquire("gnews.io", 1.0)
        params: Dict[str, Any] = {
            "q": query,
            "apikey": self.api_key,
            "max": min(max_results, 100),
            "lang": language,
            "country": country,
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"GNews error: {e}", source="gnews", score=0.0)]

    async def top_headlines(self, language: str = "tr", country: str = "tr", max_results: int = 10) -> List[NewsResult]:
        """Get top headlines via GNews."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="GNews: no API key configured", source="gnews", score=0.0)]
        await self.limiter.acquire("gnews.io", 1.0)
        params: Dict[str, Any] = {"apikey": self.api_key, "max": min(max_results, 100), "lang": language, "country": country}
        try:
            resp = await self.client.get(self.TOP_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"GNews headlines error: {e}", source="gnews", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[NewsResult]:
        results: List[NewsResult] = []
        for item in data.get("articles", [])[:max_results]:
            results.append(
                NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", "") or "",
                    source="gnews",
                    score=0.88,
                    published_at=item.get("publishedAt"),
                    author=item.get("source", {}).get("name"),
                    image_url=item.get("image"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class CurrentsAPISearch:
    """Currents API — free tier available, API key required."""

    API_URL = "https://api.currentsapi.services/v1/search"
    LATEST_URL = "https://api.currentsapi.services/v1/latest-news"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10, language: str = "en") -> List[NewsResult]:
        """Search via Currents API."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="Currents: no API key configured", source="currents", score=0.0)]
        await self.limiter.acquire("currentsapi.services", 1.0)
        params: Dict[str, Any] = {"keywords": query, "apiKey": self.api_key, "page_size": min(max_results, 100), "language": language}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"Currents error: {e}", source="currents", score=0.0)]

    async def latest_news(self, language: str = "en", max_results: int = 10) -> List[NewsResult]:
        """Get latest news via Currents."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="Currents: no API key configured", source="currents", score=0.0)]
        await self.limiter.acquire("currentsapi.services", 1.0)
        params: Dict[str, Any] = {"apiKey": self.api_key, "page_size": min(max_results, 100), "language": language}
        try:
            resp = await self.client.get(self.LATEST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"Currents latest error: {e}", source="currents", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[NewsResult]:
        results: List[NewsResult] = []
        for item in data.get("news", [])[:max_results]:
            results.append(
                NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", "") or item.get("body", "")[:300],
                    source="currents",
                    score=0.85,
                    published_at=item.get("published"),
                    author=item.get("author"),
                    image_url=item.get("image"),
                    category=(item.get("category", []) or [None])[0],
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class MediaStackSearch:
    """MediaStack — free tier (1000/month), API key required."""

    API_URL = "http://api.mediastack.com/v1/news"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10, languages: str = "tr,en") -> List[NewsResult]:
        """Search via MediaStack."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="MediaStack: no API key configured", source="mediastack", score=0.0)]
        await self.limiter.acquire("mediastack.com", 1.0)
        params: Dict[str, Any] = {
            "access_key": self.api_key,
            "keywords": query,
            "limit": min(max_results, 100),
            "languages": languages,
            "sort": "published_desc",
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"MediaStack error: {e}", source="mediastack", score=0.0)]

    async def latest(self, countries: str = "tr", languages: str = "tr", max_results: int = 10) -> List[NewsResult]:
        """Get latest news via MediaStack."""
        if not self.api_key:
            return [NewsResult(title="", url="", snippet="MediaStack: no API key configured", source="mediastack", score=0.0)]
        await self.limiter.acquire("mediastack.com", 1.0)
        params: Dict[str, Any] = {
            "access_key": self.api_key,
            "countries": countries,
            "limit": min(max_results, 100),
            "languages": languages,
            "sort": "published_desc",
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [NewsResult(title="", url="", snippet=f"MediaStack latest error: {e}", source="mediastack", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[NewsResult]:
        results: List[NewsResult] = []
        for item in data.get("data", [])[:max_results]:
            results.append(
                NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", "") or "",
                    source="mediastack",
                    score=0.82,
                    published_at=item.get("published_at"),
                    author=item.get("author"),
                    image_url=item.get("image"),
                    category=item.get("category"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class NewsAggregator:
    """Run all news APIs and aggregate."""

    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        gnews_key: Optional[str] = None,
        currents_key: Optional[str] = None,
        mediastack_key: Optional[str] = None,
    ):
        self.newsapi = NewsAPISearch(api_key=newsapi_key)
        self.gnews = GNewsSearch(api_key=gnews_key)
        self.currents = CurrentsAPISearch(api_key=currents_key)
        self.mediastack = MediaStackSearch(api_key=mediastack_key)

    async def search_all(self, query: str, max_results: int = 10) -> Dict[str, List[NewsResult]]:
        """Search all configured news APIs."""
        tasks: Dict[str, asyncio.Task] = {}
        if self.newsapi.api_key:
            tasks["newsapi"] = asyncio.create_task(self.newsapi.search(query, max_results))
        if self.gnews.api_key:
            tasks["gnews"] = asyncio.create_task(self.gnews.search(query, max_results))
        if self.currents.api_key:
            tasks["currents"] = asyncio.create_task(self.currents.search(query, max_results))
        if self.mediastack.api_key:
            tasks["mediastack"] = asyncio.create_task(self.mediastack.search(query, max_results))
        if not tasks:
            return {"_none": [NewsResult(title="", url="", snippet="No news API keys configured", source="none", score=0.0)]}
        results: Dict[str, List[NewsResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=35.0)
            except asyncio.TimeoutError:
                results[name] = [NewsResult(title="", url="", snippet="Timeout", source=name, score=0.0)]
            except Exception as e:
                results[name] = [NewsResult(title="", url="", snippet=f"Error: {e}", source=name, score=0.0)]
        return results

    async def top_headlines(self, max_results: int = 10, country: str = "tr") -> Dict[str, List[NewsResult]]:
        """Get top headlines from all configured APIs."""
        tasks: Dict[str, asyncio.Task] = {}
        if self.newsapi.api_key:
            tasks["newsapi"] = asyncio.create_task(self.newsapi.top_headlines(country=country, max_results=max_results))
        if self.gnews.api_key:
            tasks["gnews"] = asyncio.create_task(self.gnews.top_headlines(language="tr", country=country, max_results=max_results))
        if self.currents.api_key:
            tasks["currents"] = asyncio.create_task(self.currents.latest_news(language="tr", max_results=max_results))
        if self.mediastack.api_key:
            tasks["mediastack"] = asyncio.create_task(self.mediastack.latest(countries=country, max_results=max_results))
        if not tasks:
            return {"_none": [NewsResult(title="", url="", snippet="No news API keys configured", source="none", score=0.0)]}
        results: Dict[str, List[NewsResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=35.0)
            except asyncio.TimeoutError:
                results[name] = [NewsResult(title="", url="", snippet="Timeout", source=name, score=0.0)]
            except Exception as e:
                results[name] = [NewsResult(title="", url="", snippet=f"Error: {e}", source=name, score=0.0)]
        return results

    async def close(self):
        await asyncio.gather(
            self.newsapi.close(),
            self.gnews.close(),
            self.currents.close(),
            self.mediastack.close(),
            return_exceptions=True,
        )


# ── Quick test helper ─────────────────────────────────────────────────────────
async def _demo():
    agg = NewsAggregator()
    print("NewsAggregator initialized (no keys = demo mode)")
    await agg.close()


if __name__ == "__main__":
    asyncio.run(_demo())
