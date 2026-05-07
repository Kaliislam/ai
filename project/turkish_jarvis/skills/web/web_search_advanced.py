"""
Web Search Advanced Skill

Provides multi-engine web search, page content extraction,
and result summarization for the Turkish Jarvis assistant.

Engines supported:
  - DuckDuckGo (HTML scraping, no API key)
  - Brave Search (optional API key)
  - Google Scholar (scraping)
  - arXiv (API)
  - Wikipedia (API)
  - Turkish news sites (Hürriyet, CNN Türk, BBC Türkçe, Webrazzi)
"""

from __future__ import annotations

import re
import json
import asyncio
import hashlib
from typing import Any
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Optional content-extraction libs
try:
    from readability import Document as ReadabilityDocument
    _HAS_READABILITY = True
except Exception:
    _HAS_READABILITY = False

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except Exception:
    _HAS_TRAFILATURA = False


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
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


class WebSearchSkill:
    """
    Unified web-search skill with multiple backends.
    """

    # ------------------------------------------------------------------
    # init
    # ------------------------------------------------------------------
    def __init__(
        self,
        brave_api_key: str | None = None,
        timeout: float = 30.0,
        max_concurrent: int = 5,
    ) -> None:
        self.brave_api_key = brave_api_key
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # httpx client lifecycle
    # ------------------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                http2=True,
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
    # DuckDuckGo (HTML scraping)
    # ------------------------------------------------------------------
    async def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10,
        region: str = "tr-tr",
    ) -> list[dict[str, Any]]:
        """
        Search DuckDuckGo via HTML scraping. No API key required.
        """
        client = await self._get_client()
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "kl": region}

        try:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return [{"error": f"DuckDuckGo request failed: {exc}"}]

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict[str, Any]] = []

        for link in soup.select(".result"):
            title_tag = link.select_one(".result__a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            # DuckDuckGo uses external redirects — unwrap if needed
            if href.startswith("//"):
                href = "https:" + href
            snippet_tag = link.select_one(".result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append(
                {
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "source": "duckduckgo",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(results) >= max_results:
                break

        return results

    # ------------------------------------------------------------------
    # Brave Search (API)
    # ------------------------------------------------------------------
    async def search_brave(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search Brave Search API. Requires ``brave_api_key`` at init.
        """
        if not self.brave_api_key:
            return [{"error": "Brave API key not configured."}]

        client = await self._get_client()
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {
            "q": query,
            "count": min(max_results, 20),
            "offset": 0,
            "search_lang": "tr",
        }
        headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json",
        }

        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return [{"error": f"Brave Search request failed: {exc}"}]

        data = resp.json()
        results: list[dict[str, Any]] = []

        for item in data.get("web", {}).get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                    "source": "brave",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(results) >= max_results:
                break

        return results

    # ------------------------------------------------------------------
    # Google Scholar (HTML scraping)
    # ------------------------------------------------------------------
    async def search_google_scholar(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search Google Scholar via HTML scraping.
        """
        client = await self._get_client()
        encoded = quote_plus(query)
        url = f"https://scholar.google.com/scholar?q={encoded}&hl=tr"

        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return [{"error": f"Google Scholar request failed: {exc}"}]

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict[str, Any]] = []

        for entry in soup.select(".gs_ri"):
            title_tag = entry.select_one(".gs_rt a")
            if not title_tag:
                title_tag = entry.select_one(".gs_rt")
            title = title_tag.get_text(strip=True) if title_tag else ""
            href = title_tag.get("href", "") if title_tag else ""

            author_tag = entry.select_one(".gs_a")
            authors = author_tag.get_text(strip=True) if author_tag else ""

            snippet_tag = entry.select_one(".gs_rs")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append(
                {
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "authors": authors,
                    "source": "google_scholar",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(results) >= max_results:
                break

        return results

    # ------------------------------------------------------------------
    # arXiv (API)
    # ------------------------------------------------------------------
    async def search_arxiv(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search arXiv via the public API.
        """
        client = await self._get_client()
        encoded = quote_plus(query)
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{encoded}&start=0&max_results={max_results}"
        )

        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return [{"error": f"arXiv request failed: {exc}"}]

        soup = BeautifulSoup(resp.text, "xml")
        results: list[dict[str, Any]] = []

        for entry in soup.find_all("entry"):
            title = entry.find("title")
            title_text = title.get_text(strip=True) if title else ""
            summary = entry.find("summary")
            snippet = summary.get_text(strip=True) if summary else ""
            link = entry.find("link", title="pdf")
            pdf_url = link.get("href") if link else ""
            if not pdf_url:
                for lnk in entry.find_all("link"):
                    if lnk.get("rel") == "alternate":
                        pdf_url = lnk.get("href", "")
                        break

            authors = [a.get_text(strip=True) for a in entry.find_all("name")]

            results.append(
                {
                    "title": title_text,
                    "url": pdf_url,
                    "snippet": snippet,
                    "authors": authors,
                    "source": "arxiv",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(results) >= max_results:
                break

        return results

    # ------------------------------------------------------------------
    # Wikipedia (API)
    # ------------------------------------------------------------------
    async def search_wikipedia(
        self,
        query: str,
        lang: str = "tr",
    ) -> list[dict[str, Any]]:
        """
        Search Wikipedia via the MediaWiki API.
        Returns page extracts + URLs.
        """
        client = await self._get_client()
        search_url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={quote_plus(query)}"
            f"&srlimit=5&format=json&origin=*"
        )

        try:
            resp = await client.get(search_url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return [{"error": f"Wikipedia search failed: {exc}"}]

        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return []

        # Batch fetch extracts
        titles = "|".join(quote_plus(r["title"]) for r in search_results)
        extract_url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=query&prop=extracts&explaintext"
            f"&exsentences=3&titles={titles}&format=json&origin=*"
        )

        try:
            resp = await client.get(extract_url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return [{"error": f"Wikipedia extract fetch failed: {exc}"}]

        pages = data.get("query", {}).get("pages", {})
        results: list[dict[str, Any]] = []

        for page_id, page_info in pages.items():
            title = page_info.get("title", "")
            extract = page_info.get("extract", "")
            url = f"https://{lang}.wikipedia.org/wiki/{quote_plus(title)}"
            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": extract,
                    "source": "wikipedia",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        return results

    # ------------------------------------------------------------------
    # Turkish news sites
    # ------------------------------------------------------------------
    async def search_news(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Aggregate search results from supported Turkish news portals.
        Currently supports: Hürriyet, CNN Türk, BBC Türkçe, Webrazzi.
        """
        sites = [
            {
                "name": "hurriyet",
                "search_url": "https://www.hurriyet.com.tr/arama/#/?q={query}&s=0",
                "result_selector": ".search-result-item",
                "title_selector": "h2 a, h3 a, .title a",
                "snippet_selector": ".search-item-content, .description, p",
                "url_attr": "href",
                "base_url": "https://www.hurriyet.com.tr",
            },
            {
                "name": "cnnturk",
                "search_url": "https://www.cnnturk.com/arama/?q={query}",
                "result_selector": ".search-item, .card",
                "title_selector": "h2 a, h3 a, .title a",
                "snippet_selector": ".summary, .description, p",
                "url_attr": "href",
                "base_url": "https://www.cnnturk.com",
            },
            {
                "name": "bbc_turkce",
                "search_url": "https://www.bbc.com/turkce/search?q={query}",
                "result_selector": "[data-testid='card'], .lx-stream-post, article",
                "title_selector": "h3 a, h2 a, a[data-testid='card-headline']",
                "snippet_selector": "p, .lx-stream-post__summary, [data-testid='card-description']",
                "url_attr": "href",
                "base_url": "https://www.bbc.com",
            },
            {
                "name": "webrazzi",
                "search_url": "https://webrazzi.com/?s={query}",
                "result_selector": "article, .post-item",
                "title_selector": "h2 a, .entry-title a",
                "snippet_selector": ".entry-summary, .post-excerpt, p",
                "url_attr": "href",
                "base_url": "https://webrazzi.com",
            },
        ]

        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = [
            self._scrape_news_site(semaphore, site, query)
            for site in sites
        ]
        nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[dict[str, Any]] = []
        for group in nested:
            if isinstance(group, list):
                all_results.extend(group)

        # Deduplicate by URL
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for r in all_results:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                deduped.append(r)

        # Sort by presence of snippet then truncate
        deduped.sort(key=lambda x: bool(x.get("snippet")), reverse=True)
        return deduped[:max_results]

    async def _scrape_news_site(
        self,
        semaphore: asyncio.Semaphore,
        site: dict[str, str],
        query: str,
    ) -> list[dict[str, Any]]:
        async with semaphore:
            client = await self._get_client()
            url = site["search_url"].format(query=quote_plus(query))
            results: list[dict[str, Any]] = []

            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError:
                return results

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(site["result_selector"])

            for item in items[:5]:  # max 5 per site
                title_tag = item.select_one(site["title_selector"])
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get(site["url_attr"], "")
                if href.startswith("/"):
                    href = urljoin(site["base_url"], href)
                elif not href.startswith("http"):
                    href = urljoin(site["base_url"], href)

                snippet_tag = item.select_one(site["snippet_selector"])
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                # Clean snippet
                snippet = re.sub(r"\s+", " ", snippet)

                results.append(
                    {
                        "title": title,
                        "url": href,
                        "snippet": snippet,
                        "source": site["name"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            return results

    # ------------------------------------------------------------------
    # Page content extraction
    # ------------------------------------------------------------------
    async def get_page_content(
        self,
        url: str,
        prefer_readability: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch a page and extract readable article content.
        Tries ``readability-lxml`` then ``trafilatura``, falls back to raw text.
        """
        client = await self._get_client()
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": f"Failed to fetch {url}: {exc}"}

        html = resp.text
        title = ""
        content = ""
        method = "fallback"

        if _HAS_READABILITY and prefer_readability:
            try:
                doc = ReadabilityDocument(html)
                title = doc.short_title()
                summary = doc.summary()
                soup = BeautifulSoup(summary, "html.parser")
                content = soup.get_text(separator="\n", strip=True)
                method = "readability"
            except Exception:
                pass

        if not content and _HAS_TRAFILATURA:
            try:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
                if extracted:
                    content = extracted
                    method = "trafilatura"
            except Exception:
                pass

        if not content:
            soup = BeautifulSoup(html, "html.parser")
            # Remove script/style
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()
            title = soup.title.get_text(strip=True) if soup.title else ""
            content = soup.get_text(separator="\n", strip=True)
            method = "fallback"

        # Truncate overly long text
        if len(content) > 50_000:
            content = content[:50_000] + "\n...[truncated]"

        return {
            "url": url,
            "title": title,
            "content": content,
            "method": method,
            "length": len(content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Summarization (simple heuristic; can be swapped for LLM call)
    # ------------------------------------------------------------------
    def summarize_results(
        self,
        results: list[dict[str, Any]],
        max_chars: int = 500,
    ) -> str:
        """
        Produce a concise Turkish summary of search results.
        """
        if not results:
            return "Sonuç bulunamadı."

        lines: list[str] = []
        total = 0
        for r in results:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            source = r.get("source", "")
            piece = f"• {title}"
            if snippet:
                piece += f": {snippet}"
            if source:
                piece += f" (Kaynak: {source})"
            piece += "\n"
            if total + len(piece) > max_chars:
                break
            lines.append(piece)
            total += len(piece)

        summary = "".join(lines)
        return summary.strip()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    async def search_all(
        self,
        query: str,
        engines: list[str] | None = None,
        max_results: int = 10,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Run the same query across multiple engines and return combined results.
        """
        if engines is None:
            engines = ["duckduckgo", "news"]

        tasks: dict[str, asyncio.Task] = {}
        if "duckduckgo" in engines:
            tasks["duckduckgo"] = asyncio.create_task(
                self.search_duckduckgo(query, max_results)
            )
        if "brave" in engines:
            tasks["brave"] = asyncio.create_task(
                self.search_brave(query, max_results)
            )
        if "google_scholar" in engines:
            tasks["google_scholar"] = asyncio.create_task(
                self.search_google_scholar(query, max_results)
            )
        if "arxiv" in engines:
            tasks["arxiv"] = asyncio.create_task(
                self.search_arxiv(query, max_results)
            )
        if "wikipedia" in engines:
            tasks["wikipedia"] = asyncio.create_task(
                self.search_wikipedia(query)
            )
        if "news" in engines:
            tasks["news"] = asyncio.create_task(
                self.search_news(query, max_results)
            )

        out: dict[str, list[dict[str, Any]]] = {}
        for name, task in tasks.items():
            try:
                out[name] = await task
            except Exception as exc:
                out[name] = [{"error": str(exc)}]

        return out
