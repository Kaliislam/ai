"""Ücretsiz internet arama — API key gerektirmeyen yöntemler.

Stratejiler:
  1. SearXNG self-hosted (opsiyonel, en hızlı)
  2. DuckDuckGo HTML scraping (ücretsiz, rate-limited)
  3. Bing public search (fallback, limited)

Kullanım:
    engine = FreeSearchEngine()
    results = await engine.search("Python asyncio")
    for r in results:
        print(r.title, r.url)
    await engine.close()
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("jarvis.free_search")

# ────────────────────────────── Data Model ──────────────────────────────

@dataclass
class SearchResult:
    """Tek bir arama sonucu."""

    title: str
    url: str
    snippet: str
    source: str  # "DuckDuckGo", "SearXNG", "Bing"
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict'e dönüştür."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "fetched_at": self.fetched_at,
        }

    def __repr__(self) -> str:
        return f"SearchResult({self.source}: {self.title[:40]!r})"


# ────────────────────────────── Engine ──────────────────────────────

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class FreeSearchEngine:
    """API key'siz internet arama motoru.

    Args:
        searxng_url: Self-hosted SearXNG instance URL (ör: http://localhost:8080).
        ddg_rate_limit: DuckDuckGo istekleri arası minimum saniye (default: 1.0).
        client: Dışarıdan verilebilecek httpx.AsyncClient instance.
    """

    def __init__(
        self,
        searxng_url: Optional[str] = None,
        ddg_rate_limit: float = 1.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.searxng_url = searxng_url.rstrip("/") if searxng_url else None
        self.last_ddg_request = 0.0
        self.ddg_rate_limit = max(ddg_rate_limit, 0.5)
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialized httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    # ── Public API ─────────────────────────────────────────────────

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """En iyi ücretsiz yöntemi kullanarak ara.

        Sıralama:
          1. SearXNG (self-hosted varsa)
          2. DuckDuckGo HTML scraping
          3. Bing public search

        Returns:
            Boş liste dönebilir (tüm yöntemler başarısız olursa).
        """
        if not query or not query.strip():
            logger.warning("Boş arama sorgusu reddedildi.")
            return []

        # 1. SearXNG dene
        if self.searxng_url:
            try:
                results = await self._search_searxng(query, max_results)
                if results:
                    logger.info("SearXNG %d sonuç döndürdü.", len(results))
                    return results
            except Exception as exc:
                logger.warning("SearXNG başarısız: %s", exc)

        # 2. DuckDuckGo HTML scraping
        try:
            results = await self._search_duckduckgo(query, max_results)
            if results:
                logger.info("DuckDuckGo %d sonuç döndürdü.", len(results))
                return results
        except Exception as exc:
            logger.warning("DuckDuckGo başarısız: %s", exc)

        # 3. Bing fallback
        try:
            results = await self._search_bing(query, max_results)
            if results:
                logger.info("Bing %d sonuç döndürdü.", len(results))
                return results
        except Exception as exc:
            logger.warning("Bing başarısız: %s", exc)

        logger.error("Tüm ücretsiz arama yöntemleri başarısız oldu: %r", query)
        return []

    async def get_page_text(self, url: str, max_chars: int = 5000) -> str:
        """Sayfa içeriğini çek ve düz metne dönüştür.

        Script, style, nav, footer etiketleri kaldırılır.

        Args:
            url: Çekilecek sayfa URL'si.
            max_chars: Döndürülecek maksimum karakter sayısı.

        Returns:
            Sayfa metni veya boş string (hata durumunda).
        """
        try:
            resp = await self.client.get(url, timeout=15.0, headers=DEFAULT_HEADERS)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Sayfa çekme hatası (%s): %s", url, exc)
            return ""

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:
            logger.warning("HTML parse hatası (%s): %s", url, exc)
            return ""

        # Gereksiz etiketleri kaldır
        for tag_name in ("script", "style", "nav", "footer", "header", "aside", "noscript"):
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Article / main / body içeriğine öncelik ver
        main = soup.find("main") or soup.find("article") or soup.find("div", role="main")
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Fazla boşlukları temizle
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        return text[:max_chars]

    async def summarize_search(self, query: str, results: list[SearchResult]) -> str:
        """Arama sonuçlarını kısa bir özet metne dönüştür.

        LLM entegrasyonu için hazır format.
        """
        if not results:
            return f'"{query}" için hiç sonuç bulunamadı.'

        lines = [f'"{query}" için {len(results)} sonuç bulundu:\n']
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.source}] {r.title}")
            lines.append(f"   URL: {r.url}")
            if r.snippet:
                snippet = r.snippet.replace("\n", " ")
                lines.append(f"   Özet: {snippet[:200]}")
            lines.append("")

        return "\n".join(lines)

    async def close(self) -> None:
        """HTTP client'i kapat."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── Private Search Methods ───────────────────────────────────────

    async def _search_duckduckgo(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """DuckDuckGo HTML arama (https://html.duckduckgo.com/html/)."""
        # Rate limiting
        elapsed = time.time() - self.last_ddg_request
        if elapsed < self.ddg_rate_limit:
            await asyncio.sleep(self.ddg_rate_limit - elapsed + random.uniform(0.1, 0.3))

        url = "https://html.duckduckgo.com/html/"
        params: dict[str, Any] = {"q": query, "kl": "tr-tr", "dc": "1"}

        resp = await self.client.post(url, data=params, headers=DEFAULT_HEADERS)
        resp.raise_for_status()
        self.last_ddg_request = time.time()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[SearchResult] = []

        for result in soup.select(".result"):
            title_elem = result.select_one(".result__a")
            snippet_elem = result.select_one(".result__snippet")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            # DDG redirect URL'lerini decode et
            if href.startswith("/"):
                href = f"https://duckduckgo.com{href}"
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            if title and href:
                results.append(
                    SearchResult(
                        title=title,
                        url=href,
                        snippet=snippet,
                        source="DuckDuckGo",
                    )
                )

        if not results:
            # Alternatif selector dene
            for result in soup.select(".web-result"):
                title_elem = result.select_one(".result__title a")
                snippet_elem = result.select_one(".result__snippet")
                if title_elem:
                    results.append(
                        SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=title_elem.get("href", ""),
                            snippet=snippet_elem.get_text(strip=True) if snippet_elem else "",
                            source="DuckDuckGo",
                        )
                    )

        return results[:max_results]

    async def _search_searxng(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """SearXNG self-hosted instance üzerinden arama."""
        if not self.searxng_url:
            raise ValueError("SearXNG URL tanımlanmamış.")

        url = f"{self.searxng_url}/search"
        params: dict[str, Any] = {
            "q": query,
            "format": "json",
            "language": "tr-TR",
            "safesearch": "0",
            "pageno": "1",
        }

        resp = await self.client.get(url, params=params, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()

        raw_results: list[dict[str, Any]] = data.get("results", [])
        results: list[SearchResult] = []

        for r in raw_results[:max_results]:
            title = r.get("title", "").strip()
            result_url = r.get("url", "").strip()
            content = r.get("content", "").strip()
            if title and result_url:
                results.append(
                    SearchResult(
                        title=title,
                        url=result_url,
                        snippet=content,
                        source="SearXNG",
                    )
                )

        return results

    async def _search_bing(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Bing public search (API key gerektirmez, ama rate-limited)."""
        url = "https://www.bing.com/search"
        params: dict[str, Any] = {"q": query, "setlang": "tr", "count": str(max_results)}
        headers = {
            **DEFAULT_HEADERS,
            "Referer": "https://www.bing.com/",
        }

        resp = await self.client.get(url, params=params, headers=headers, timeout=20.0)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[SearchResult] = []

        # Bing sonuç seçörleri (değişebilir)
        selectors = [
            ("li.b_algo", "h2 a", ".b_caption p"),
            (".b_algo", "h2 a", "p"),
            ("li.b_algo", "a", ".b_caption p"),
        ]

        for container_sel, title_sel, snippet_sel in selectors:
            for li in soup.select(container_sel):
                title_elem = li.select_one(title_sel)
                snippet_elem = li.select_one(snippet_sel)
                if title_elem:
                    href = title_elem.get("href", "")
                    # Bing relative URL düzeltmesi
                    if href.startswith("/"):
                        href = f"https://www.bing.com{href}"
                    results.append(
                        SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=href,
                            snippet=snippet_elem.get_text(strip=True) if snippet_elem else "",
                            source="Bing",
                        )
                    )
            if results:
                break  # Selector çalıştı, devam etme

        # Alternatif: b_title etiketli linkler
        if not results:
            for a in soup.select(".b_title a"):
                href = a.get("href", "")
                if href.startswith("/"):
                    href = f"https://www.bing.com{href}"
                parent = a.find_parent("li") or a.find_parent("div")
                snippet = ""
                if parent:
                    snippet_p = parent.select_one("p")
                    if snippet_p:
                        snippet = snippet_p.get_text(strip=True)
                results.append(
                    SearchResult(
                        title=a.get_text(strip=True),
                        url=href,
                        snippet=snippet,
                        source="Bing",
                    )
                )

        return results[:max_results]


# ────────────────────────────── Convenience ──────────────────────────────

async def free_search(
    query: str,
    max_results: int = 10,
    searxng_url: Optional[str] = None,
    fetch_pages: bool = False,
    max_page_chars: int = 3000,
) -> dict[str, Any]:
    """Tek fonksiyonluk ücretsiz arama.

    Args:
        query: Aranacak metin.
        max_results: Maksimum sonuç sayısı.
        searxng_url: Opsiyonel SearXNG URL.
        fetch_pages: True ise her sonucun sayfa içeriğini de çek.
        max_page_chars: Sayfa içeriğinden alınacak max karakter.

    Returns:
        {"query": ..., "results": [...], "pages": {...}} şeklinde dict.
    """
    engine = FreeSearchEngine(searxng_url=searxng_url)
    try:
        results = await engine.search(query, max_results=max_results)
        output: dict[str, Any] = {
            "query": query,
            "results": [r.to_dict() for r in results],
            "pages": {},
        }

        if fetch_pages:
            for r in results:
                text = await engine.get_page_text(r.url, max_chars=max_page_chars)
                if text:
                    output["pages"][r.url] = text

        return output
    finally:
        await engine.close()


# ────────────────────────────── SearXNG Kurulum Notları ──────────────────────────────
"""
SearXNG Docker ile kurulum (opsiyonel ama önerilir):

    git clone https://github.com/searxng/searxng-docker.git
    cd searxng-docker
    docker compose up -d
    # http://localhost:8080

Daha sonra:
    engine = FreeSearchEngine(searxng_url="http://localhost:8080")
"""
