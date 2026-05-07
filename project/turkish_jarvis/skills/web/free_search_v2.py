"""Advanced free search — 10+ sources with no API key required."""

import asyncio
import hashlib
import html
import json
import random
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import httpx
from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    """Unified search result across all sources."""

    title: str
    url: str
    snippet: str
    source: str
    score: float = 0.0
    published_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Simple per-domain rate limiter."""

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


class DuckDuckGoSearch:
    """DuckDuckGo HTML search scraping — no API key."""

    BASE_URL = "https://html.duckduckgo.com/html/"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search DuckDuckGo HTML endpoint."""
        await self.limiter.acquire("duckduckgo.com", 1.5)
        params = {"q": query, "kl": "tr-tr", "num": str(max_results)}
        try:
            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"DuckDuckGo error: {e}", source="duckduckgo", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SearchResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SearchResult] = []
        for link in soup.find_all("a", class_="result__a")[:max_results]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if href.startswith("/"):
                href = urllib.parse.urljoin("https://duckduckgo.com", href)
            snippet_tag = link.find_parent("div", class_="result__body")
            snippet = ""
            if snippet_tag:
                snippet_div = snippet_tag.find("a", class_="result__snippet")
                if snippet_div:
                    snippet = snippet_div.get_text(strip=True)
            if title and href:
                results.append(SearchResult(title=title, url=href, snippet=snippet, source="duckduckgo", score=0.9))
        return results

    async def close(self):
        await self.client.aclose()


class SearXNGSearch:
    """SearXNG self-hosted / public instance search."""

    INSTANCES = [
        "https://search.sapti.me",
        "https://search.bus-hit.me",
        "https://search.privacyredirect.com",
        "https://search.hbubli.cc",
        "https://search.smnz.de",
    ]

    def __init__(self, instance_url: Optional[str] = None):
        self.instance = instance_url or random.choice(self.INSTANCES)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search via SearXNG JSON API."""
        await self.limiter.acquire(urllib.parse.urlparse(self.instance).netloc, 1.0)
        params = {"q": query, "format": "json", "language": "tr", "safesearch": "0"}
        try:
            resp = await self.client.get(f"{self.instance.rstrip('/')}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_json(data, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"SearXNG error: {e}", source="searxng", score=0.0)]

    def _parse_json(self, data: Dict, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        for item in data.get("results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="searxng",
                    score=0.85,
                    published_at=item.get("publishedDate"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class BingPublicSearch:
    """Bing public search HTML scraping."""

    BASE_URL = "https://www.bing.com/search"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                ),
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Accept": "text/html",
                "Cookie": "MUID=; MUIDB=; SRCHD=AF=NOFORM; SRCHUID=V=2&GUID=; SRCHUSR=DOB=",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=2.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Scrape Bing search results."""
        await self.limiter.acquire("bing.com", 2.0)
        params = {"q": query, "count": str(max_results), "setmkt": "tr-TR", "setlang": "tr"}
        try:
            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Bing error: {e}", source="bing", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SearchResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SearchResult] = []
        for li in soup.find_all("li", class_="b_algo")[:max_results]:
            a = li.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet_p = li.find("p")
            snippet = snippet_p.get_text(strip=True) if snippet_p else ""
            if title and href:
                results.append(SearchResult(title=title, url=href, snippet=snippet, source="bing", score=0.8))
        return results

    async def close(self):
        await self.client.aclose()


class QwantSearch:
    """Qwant search scraping via lite endpoint."""

    BASE_URL = "https://lite.qwant.com/"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
                "Accept-Language": "tr-TR,tr;q=0.9",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Qwant lite."""
        await self.limiter.acquire("qwant.com", 1.5)
        params = {"q": query, "lang": "tr", "count": str(max_results)}
        try:
            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Qwant error: {e}", source="qwant", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SearchResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SearchResult] = []
        for item in soup.find_all("div", class_="result")[:max_results]:
            a = item.find("a", class_="result--url")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet_tag = item.find("span", class_="result--desc")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and href:
                results.append(SearchResult(title=title, url=href, snippet=snippet, source="qwant", score=0.75))
        return results

    async def close(self):
        await self.client.aclose()


class EcosiaSearch:
    """Ecosia search scraping."""

    BASE_URL = "https://www.ecosia.org/search"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Accept": "text/html",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Ecosia."""
        await self.limiter.acquire("ecosia.org", 1.5)
        params = {"q": query, "language": "turkish"}
        try:
            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Ecosia error: {e}", source="ecosia", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SearchResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SearchResult] = []
        for article in soup.find_all("article", class_="result")[:max_results]:
            a = article.find("a")
            if not a:
                continue
            title_tag = article.find("h2") or article.find("span", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)
            href = a.get("href", "")
            if href.startswith("/"):
                href = urllib.parse.urljoin("https://www.ecosia.org", href)
            snippet_tag = article.find("p", class_="result-snippet") or article.find("span", class_="snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and href:
                results.append(SearchResult(title=title, url=href, snippet=snippet, source="ecosia", score=0.7))
        return results

    async def close(self):
        await self.client.aclose()


class GoogleProgrammableSearch:
    """Google Custom/Programmable Search — free 100/day with API key."""

    API_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key
        self.cx = cx
        self.client = httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"})
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search via Google Programmable Search API."""
        if not self.api_key or not self.cx:
            return [SearchResult(title="", url="", snippet="Google PSE: no API key or CX configured", source="google_pse", score=0.0)]
        await self.limiter.acquire("googleapis.com", 1.0)
        params: Dict[str, Any] = {"key": self.api_key, "cx": self.cx, "q": query, "num": min(max_results, 10), "hl": "tr"}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_json(data, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Google PSE error: {e}", source="google_pse", score=0.0)]

    def _parse_json(self, data: Dict, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        for item in data.get("items", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="google_pse",
                    score=0.95,
                    published_at=item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class BraveSearchAPI:
    """Brave Search API — free tier (2000/month), API key optional."""

    API_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "X-Subscription-Token": api_key or ""},
        )
        self.limiter = RateLimiter(default_delay=0.5)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search via Brave Search API."""
        if not self.api_key:
            return [SearchResult(title="", url="", snippet="Brave: no API key configured", source="brave", score=0.0)]
        await self.limiter.acquire("search.brave.com", 0.5)
        params: Dict[str, Any] = {"q": query, "count": min(max_results, 20), "offset": 0, "spellcheck": 1}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_json(data, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Brave error: {e}", source="brave", score=0.0)]

    def _parse_json(self, data: Dict, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        for item in data.get("web", {}).get("results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="brave",
                    score=0.92,
                    published_at=item.get("age"),
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class SerpAPISearch:
    """SerpAPI — free 100/month, API key optional."""

    API_URL = "https://serpapi.com/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"})
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search via SerpAPI."""
        if not self.api_key:
            return [SearchResult(title="", url="", snippet="SerpAPI: no API key configured", source="serpapi", score=0.0)]
        await self.limiter.acquire("serpapi.com", 1.0)
        params: Dict[str, Any] = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": min(max_results, 100),
            "hl": "tr",
            "gl": "tr",
        }
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_json(data, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"SerpAPI error: {e}", source="serpapi", score=0.0)]

    def _parse_json(self, data: Dict, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serpapi",
                    score=0.93,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class SearchAPIIO:
    """SearchAPI.io — free tier available, API key optional."""

    API_URL = "https://www.searchapi.io/api/v1/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"})
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search via SearchAPI.io."""
        if not self.api_key:
            return [SearchResult(title="", url="", snippet="SearchAPI.io: no API key configured", source="searchapi", score=0.0)]
        await self.limiter.acquire("searchapi.io", 1.0)
        params: Dict[str, Any] = {"engine": "google", "q": query, "api_key": self.api_key, "num": min(max_results, 100), "hl": "tr"}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_json(data, max_results)
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"SearchAPI.io error: {e}", source="searchapi", score=0.0)]

    def _parse_json(self, data: Dict, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="searchapi",
                    score=0.9,
                    raw=item,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class WolframAlphaShort:
    """Wolfram Alpha Short Answers — free tier, API key optional."""

    API_URL = "https://api.wolframalpha.com/v1/result"
    SPOKEN_URL = "https://api.wolframalpha.com/v1/spoken"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0, headers={"Accept": "text/plain,*/*"})
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Query Wolfram Alpha for short answers."""
        if not self.api_key:
            return [SearchResult(title="", url="", snippet="Wolfram: no API key configured", source="wolfram", score=0.0)]
        await self.limiter.acquire("wolframalpha.com", 1.0)
        params: Dict[str, Any] = {"i": query, "appid": self.api_key, "units": "metric"}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            if resp.status_code == 200:
                answer = resp.text.strip()
                if answer and answer != "No short answer available":
                    return [
                        SearchResult(
                            title=f"Wolfram: {query[:40]}",
                            url=f"https://www.wolframalpha.com/input?i={urllib.parse.quote(query)}",
                            snippet=answer,
                            source="wolfram",
                            score=0.95,
                        )
                    ]
            spoken_resp = await self.client.get(self.SPOKEN_URL, params=params)
            if spoken_resp.status_code == 200:
                spoken = spoken_resp.text.strip()
                if spoken and spoken != "No spoken result available":
                    return [
                        SearchResult(
                            title=f"Wolfram (spoken): {query[:40]}",
                            url=f"https://www.wolframalpha.com/input?i={urllib.parse.quote(query)}",
                            snippet=spoken,
                            source="wolfram",
                            score=0.88,
                        )
                    ]
            return []
        except Exception as e:
            return [SearchResult(title="", url="", snippet=f"Wolfram error: {e}", source="wolfram", score=0.0)]

    async def close(self):
        await self.client.aclose()


class FreeSearchV2:
    """Aggregator that runs all free search sources and combines results."""

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        brave_api_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
        searchapi_key: Optional[str] = None,
        wolfram_key: Optional[str] = None,
        searxng_instance: Optional[str] = None,
    ):
        self.duckduckgo = DuckDuckGoSearch()
        self.searxng = SearXNGSearch(instance_url=searxng_instance)
        self.bing = BingPublicSearch()
        self.google_pse = GoogleProgrammableSearch(api_key=google_api_key, cx=google_cx)
        self.brave = BraveSearchAPI(api_key=brave_api_key)
        self.serpapi = SerpAPISearch(api_key=serpapi_key)
        self.searchapi = SearchAPIIO(api_key=searchapi_key)
        self.wolfram = WolframAlphaShort(api_key=wolfram_key)
        self.qwant = QwantSearch()
        self.ecosia = EcosiaSearch()

    async def search_all(
        self, query: str, max_results: int = 10, sources: Optional[List[str]] = None
    ) -> Dict[str, List[SearchResult]]:
        """Run all (or selected) sources concurrently."""
        all_sources = {
            "duckduckgo": self.duckduckgo.search,
            "searxng": self.searxng.search,
            "bing": self.bing.search,
            "google_pse": self.google_pse.search,
            "brave": self.brave.search,
            "serpapi": self.serpapi.search,
            "searchapi": self.searchapi.search,
            "wolfram": self.wolfram.search,
            "qwant": self.qwant.search,
            "ecosia": self.ecosia.search,
        }
        active = {k: v for k, v in all_sources.items() if sources is None or k in sources}
        tasks = {name: asyncio.create_task(func(query, max_results)) for name, func in active.items()}
        results: Dict[str, List[SearchResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=35.0)
            except asyncio.TimeoutError:
                results[name] = [SearchResult(title="", url="", snippet="Timeout", source=name, score=0.0)]
            except Exception as e:
                results[name] = [SearchResult(title="", url="", snippet=f"Error: {e}", source=name, score=0.0)]
        return results

    async def combined_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search all sources and merge/deduplicate."""
        raw = await self.search_all(query, max_results)
        merged: List[SearchResult] = []
        for src, items in raw.items():
            for item in items:
                if item.title or item.snippet:
                    merged.append(item)
        return self._deduplicate(merged, max_results)

    @staticmethod
    def _deduplicate(results: List[SearchResult], max_results: int) -> List[SearchResult]:
        seen: set = set()
        out: List[SearchResult] = []
        for r in results:
            key = hashlib.md5(f"{r.title.lower().strip()}|{r.url.lower().strip()}".encode()).hexdigest()[:16]
            if key not in seen:
                seen.add(key)
                out.append(r)
                if len(out) >= max_results:
                    break
        return out

    async def close(self):
        await asyncio.gather(
            self.duckduckgo.close(),
            self.searxng.close(),
            self.bing.close(),
            self.google_pse.close(),
            self.brave.close(),
            self.serpapi.close(),
            self.searchapi.close(),
            self.wolfram.close(),
            self.qwant.close(),
            self.ecosia.close(),
            return_exceptions=True,
        )


# ── Quick test helper ─────────────────────────────────────────────────────────
async def _demo():
    engine = FreeSearchV2()
    try:
        results = await engine.search_all("python asyncio tutorial", max_results=5, sources=["duckduckgo", "searxng", "bing"])
        for src, items in results.items():
            print(f"\n=== {src} ===")
            for it in items[:3]:
                print(f"  {it.title[:60]} | {it.url[:60]}")
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(_demo())
