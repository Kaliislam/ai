"""Search aggregator — combines all sources, deduplicates, ranks, summarizes."""

import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

import httpx

from turkish_jarvis.skills.web.free_search_v2 import FreeSearchV2, SearchResult as WebSearchResult
from turkish_jarvis.skills.web.social_scraper import SocialScraperAggregator, SocialResult
from turkish_jarvis.skills.web.academic_search import AcademicSearchAggregator, AcademicResult
from turkish_jarvis.skills.web.news_api import NewsAggregator, NewsResult


@dataclass
class UnifiedResult:
    """Fully unified result from any source."""

    title: str
    url: str
    snippet: str
    source: str
    category: str  # web | social | academic | news
    score: float = 0.0
    published_at: Optional[str] = None
    author: Optional[str] = None
    upvotes: Optional[int] = None
    comments: Optional[int] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    image_url: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class SearchAggregator:
    """Master aggregator: runs web, social, academic, news in parallel."""

    # Default scoring weights per category
    WEIGHTS = {
        "web": 1.0,
        "social": 0.85,
        "academic": 1.05,
        "news": 0.95,
    }

    def __init__(
        self,
        # Web keys
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        brave_api_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
        searchapi_key: Optional[str] = None,
        wolfram_key: Optional[str] = None,
        searxng_instance: Optional[str] = None,
        # Academic keys
        crossref_mailto: Optional[str] = None,
        core_api_key: Optional[str] = None,
        pubmed_key: Optional[str] = None,
        # News keys
        newsapi_key: Optional[str] = None,
        gnews_key: Optional[str] = None,
        currents_key: Optional[str] = None,
        mediastack_key: Optional[str] = None,
    ):
        self.web = FreeSearchV2(
            google_api_key=google_api_key,
            google_cx=google_cx,
            brave_api_key=brave_api_key,
            serpapi_key=serpapi_key,
            searchapi_key=searchapi_key,
            wolfram_key=wolfram_key,
            searxng_instance=searxng_instance,
        )
        self.social = SocialScraperAggregator()
        self.academic = AcademicSearchAggregator(
            crossref_mailto=crossref_mailto,
            core_api_key=core_api_key,
            pubmed_key=pubmed_key,
        )
        self.news = NewsAggregator(
            newsapi_key=newsapi_key,
            gnews_key=gnews_key,
            currents_key=currents_key,
            mediastack_key=mediastack_key,
        )
        self._closed = False

    async def multi_source_search(
        self,
        query: str,
        max_results: int = 20,
        categories: Optional[List[str]] = None,
        web_sources: Optional[List[str]] = None,
    ) -> Dict[str, List[UnifiedResult]]:
        """Search across all enabled categories and sources.

        Args:
            query: Search query string.
            max_results: Per-category max results.
            categories: Which categories to include (default all).
            web_sources: Specific web sources to use (default all).

        Returns:
            Dict keyed by category -> list of UnifiedResult.
        """
        cats = categories or ["web", "social", "academic", "news"]
        tasks: Dict[str, asyncio.Task] = {}

        if "web" in cats:
            tasks["web"] = asyncio.create_task(self._search_web(query, max_results, web_sources))
        if "social" in cats:
            tasks["social"] = asyncio.create_task(self._search_social(query, max_results))
        if "academic" in cats:
            tasks["academic"] = asyncio.create_task(self._search_academic(query, max_results))
        if "news" in cats:
            tasks["news"] = asyncio.create_task(self._search_news(query, max_results))

        results: Dict[str, List[UnifiedResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=45.0)
            except asyncio.TimeoutError:
                results[name] = [UnifiedResult(title="", url="", snippet="Timeout", source=name, category=name, score=0.0)]
            except Exception as e:
                results[name] = [UnifiedResult(title="", url="", snippet=f"Error: {e}", source=name, category=name, score=0.0)]
        return results

    async def _search_web(self, query: str, max_results: int, sources: Optional[List[str]]) -> List[UnifiedResult]:
        raw = await self.web.search_all(query, max_results, sources=sources)
        unified: List[UnifiedResult] = []
        for src_name, items in raw.items():
            for it in items:
                unified.append(
                    UnifiedResult(
                        title=it.title,
                        url=it.url,
                        snippet=it.snippet,
                        source=it.source,
                        category="web",
                        score=it.score * self.WEIGHTS["web"],
                        published_at=it.published_at,
                        raw=it.raw,
                    )
                )
        return unified

    async def _search_social(self, query: str, max_results: int) -> List[UnifiedResult]:
        raw = await self.social.search_all(query, max_results)
        unified: List[UnifiedResult] = []
        for src_name, items in raw.items():
            for it in items:
                unified.append(
                    UnifiedResult(
                        title=it.title,
                        url=it.url,
                        snippet=it.snippet,
                        source=it.source,
                        category="social",
                        score=it.score * self.WEIGHTS["social"],
                        author=it.author,
                        upvotes=it.upvotes,
                        comments=it.comments,
                        published_at=it.published_at,
                        raw=it.raw,
                    )
                )
        return unified

    async def _search_academic(self, query: str, max_results: int) -> List[UnifiedResult]:
        raw = await self.academic.search_all(query, max_results)
        unified: List[UnifiedResult] = []
        for src_name, items in raw.items():
            for it in items:
                unified.append(
                    UnifiedResult(
                        title=it.title,
                        url=it.url,
                        snippet=it.snippet,
                        source=it.source,
                        category="academic",
                        score=it.score * self.WEIGHTS["academic"],
                        author=it.authors[0] if it.authors else None,
                        published_at=it.published_at,
                        doi=it.doi,
                        year=it.year,
                        raw=it.raw,
                    )
                )
        return unified

    async def _search_news(self, query: str, max_results: int) -> List[UnifiedResult]:
        raw = await self.news.search_all(query, max_results)
        unified: List[UnifiedResult] = []
        for src_name, items in raw.items():
            for it in items:
                unified.append(
                    UnifiedResult(
                        title=it.title,
                        url=it.url,
                        snippet=it.snippet,
                        source=it.source,
                        category="news",
                        score=it.score * self.WEIGHTS["news"],
                        author=it.author,
                        published_at=it.published_at,
                        image_url=it.image_url,
                        raw=it.raw,
                    )
                )
        return unified

    # ── Deduplication ─────────────────────────────────────────────────────────

    @staticmethod
    def deduplicate_results(results: List[UnifiedResult]) -> List[UnifiedResult]:
        """Remove duplicate results across sources using title+url hash."""
        seen: set = set()
        out: List[UnifiedResult] = []
        for r in results:
            key_str = f"{r.title.lower().strip()[:80]}|{r.url.lower().strip()[:120]}"
            key = hashlib.md5(key_str.encode()).hexdigest()[:16]
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out

    @staticmethod
    def deduplicate_by_domain(results: List[UnifiedResult], max_per_domain: int = 3) -> List[UnifiedResult]:
        """Cap results per domain to avoid dominance by one site."""
        domain_counts: Dict[str, int] = {}
        out: List[UnifiedResult] = []
        for r in results:
            domain = re.sub(r"^https?://", "", r.url.lower()).split("/")[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if domain_counts[domain] <= max_per_domain:
                out.append(r)
        return out

    # ── Ranking ───────────────────────────────────────────────────────────────

    @staticmethod
    def rank_by_relevance(
        results: List[UnifiedResult],
        query: Optional[str] = None,
        boost_recent: bool = True,
    ) -> List[UnifiedResult]:
        """Rank results by composite relevance score.

        Scoring factors:
            - Base source score
            - Title/snippet keyword match (if query provided)
            - Recency boost (if boost_recent=True)
        """
        scored: List[tuple] = []
        query_words = set(re.findall(r"\w+", query.lower())) if query else set()

        for r in results:
            s = r.score
            # Keyword match boost
            if query_words:
                text = f"{r.title} {r.snippet}".lower()
                matches = sum(1 for w in query_words if w in text)
                s += 0.05 * matches
            # Recency boost (simple year-based)
            if boost_recent and r.year:
                current_year = time.localtime().tm_year
                age = max(0, current_year - r.year)
                s += max(0, 0.1 - 0.02 * age)
            scored.append((s, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    @staticmethod
    def rank_by_popularity(results: List[UnifiedResult]) -> List[UnifiedResult]:
        """Rank by upvotes/comments (best for social)."""
        scored: List[tuple] = []
        for r in results:
            s = r.score
            if r.upvotes:
                s += min(r.upvotes / 100.0, 2.0)
            if r.comments:
                s += min(r.comments / 50.0, 1.0)
            scored.append((s, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    # ── Combined helpers ──────────────────────────────────────────────────────

    async def get_combined_results(
        self,
        query: str,
        max_results: int = 20,
        categories: Optional[List[str]] = None,
    ) -> List[UnifiedResult]:
        """Full pipeline: search all, deduplicate, rank."""
        by_cat = await self.multi_source_search(query, max_results=max_results, categories=categories)
        merged: List[UnifiedResult] = []
        for cat, items in by_cat.items():
            merged.extend(items)
        deduped = self.deduplicate_results(merged)
        ranked = self.rank_by_relevance(deduped, query=query)
        return ranked[:max_results]

    async def get_combined_summary(
        self,
        query: str,
        max_results: int = 15,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get combined results plus a simple text summary."""
        results = await self.get_combined_results(query, max_results=max_results, categories=categories)
        by_source: Dict[str, List[UnifiedResult]] = {}
        for r in results:
            by_source.setdefault(r.source, []).append(r)

        summary_lines = [f"'{query}' için {len(results)} sonuç bulundu.", ""]
        for src, items in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            summary_lines.append(f"  • {src}: {len(items)} sonuç")
            for it in items[:3]:
                summary_lines.append(f"    - {it.title[:70]} ({it.category})")
            summary_lines.append("")

        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "by_source": {k: len(v) for k, v in by_source.items()},
            "summary_text": "\n".join(summary_lines),
        }

    # ── Category-specific helpers ─────────────────────────────────────────────

    async def web_search(self, query: str, max_results: int = 10) -> List[UnifiedResult]:
        """Web-only search with dedup + rank."""
        by_cat = await self.multi_source_search(query, max_results=max_results, categories=["web"])
        return self.rank_by_relevance(
            self.deduplicate_results(by_cat.get("web", [])), query=query
        )[:max_results]

    async def social_search(self, query: str, max_results: int = 10) -> List[UnifiedResult]:
        """Social-only search with dedup + rank."""
        by_cat = await self.multi_source_search(query, max_results=max_results, categories=["social"])
        return self.rank_by_popularity(
            self.deduplicate_results(by_cat.get("social", []))
        )[:max_results]

    async def academic_search(self, query: str, max_results: int = 10) -> List[UnifiedResult]:
        """Academic-only search with dedup + rank."""
        by_cat = await self.multi_source_search(query, max_results=max_results, categories=["academic"])
        return self.rank_by_relevance(
            self.deduplicate_results(by_cat.get("academic", [])), query=query
        )[:max_results]

    async def news_search(self, query: str, max_results: int = 10) -> List[UnifiedResult]:
        """News-only search with dedup + rank."""
        by_cat = await self.multi_source_search(query, max_results=max_results, categories=["news"])
        return self.rank_by_relevance(
            self.deduplicate_results(by_cat.get("news", [])), query=query
        )[:max_results]

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def close(self):
        if self._closed:
            return
        await asyncio.gather(
            self.web.close(),
            self.social.close(),
            self.academic.close(),
            self.news.close(),
            return_exceptions=True,
        )
        self._closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ── Quick test helper ─────────────────────────────────────────────────────────
async def _demo():
    async with SearchAggregator() as agg:
        summary = await agg.get_combined_summary("python programming", max_results=10, categories=["web", "social"])
        print(summary["summary_text"])


if __name__ == "__main__":
    asyncio.run(_demo())
