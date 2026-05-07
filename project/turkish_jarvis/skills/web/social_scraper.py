"""Social media & community scraping — 6 free sources, no API keys needed."""

import asyncio
import html
import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import httpx
from bs4 import BeautifulSoup


@dataclass
class SocialResult:
    """Unified social/community result."""

    title: str
    url: str
    snippet: str
    source: str
    author: Optional[str] = None
    score: float = 0.0
    published_at: Optional[str] = None
    upvotes: Optional[int] = None
    comments: Optional[int] = None
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


class RedditScraper:
    """Reddit JSON endpoint scraping — no API key, ever!"""

    BASE_URL = "https://www.reddit.com"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search_subreddit(self, subreddit: str, query: str, max_results: int = 10) -> List[SocialResult]:
        """Search a subreddit via Reddit JSON (best approximation)."""
        await self.limiter.acquire("reddit.com", 1.5)
        # Reddit does not have a free search JSON, so we list hot posts and filter client-side
        url = f"{self.BASE_URL}/r/{subreddit}/hot.json?limit=50"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return self._filter_posts(data, query, max_results, subreddit)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"Reddit error: {e}", source="reddit", score=0.0)]

    async def get_subreddit_posts(self, subreddit: str, sort: str = "hot", max_results: int = 10) -> List[SocialResult]:
        """Get posts from a subreddit."""
        await self.limiter.acquire("reddit.com", 1.5)
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json?limit={max_results}"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_posts(data, max_results, subreddit)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"Reddit error: {e}", source="reddit", score=0.0)]

    def _filter_posts(self, data: Dict, query: str, max_results: int, subreddit: str) -> List[SocialResult]:
        results: List[SocialResult] = []
        q_lower = query.lower()
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            combined = f"{title} {selftext}".lower()
            if q_lower not in combined:
                continue
            sr = SocialResult(
                title=title,
                url=f"https://www.reddit.com{post.get('permalink', '')}",
                snippet=selftext[:300],
                source="reddit",
                author=post.get("author"),
                score=float(post.get("score", 0)),
                upvotes=post.get("ups"),
                comments=post.get("num_comments"),
                raw=post,
            )
            results.append(sr)
            if len(results) >= max_results:
                break
        return results

    def _parse_posts(self, data: Dict, max_results: int, subreddit: str) -> List[SocialResult]:
        results: List[SocialResult] = []
        for child in data.get("data", {}).get("children", [])[:max_results]:
            post = child.get("data", {})
            results.append(
                SocialResult(
                    title=post.get("title", ""),
                    url=f"https://www.reddit.com{post.get('permalink', '')}",
                    snippet=post.get("selftext", "")[:300],
                    source="reddit",
                    author=post.get("author"),
                    score=float(post.get("score", 0)),
                    upvotes=post.get("ups"),
                    comments=post.get("num_comments"),
                    raw=post,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class HackerNewsScraper:
    """HackerNews Algolia API — completely free, no key."""

    API_URL = "https://hn.algolia.com/api/v1/search"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "TurkishJARVIS/1.0"},
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SocialResult]:
        """Search HackerNews via Algolia."""
        await self.limiter.acquire("hn.algolia.com", 1.0)
        params: Dict[str, Any] = {"query": query, "tags": "story", "hitsPerPage": max_results}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"HN error: {e}", source="hackernews", score=0.0)]

    def _parse(self, data: Dict, max_results: int) -> List[SocialResult]:
        results: List[SocialResult] = []
        for hit in data.get("hits", [])[:max_results]:
            obj_id = hit.get("objectID", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}"
            results.append(
                SocialResult(
                    title=hit.get("title", ""),
                    url=url,
                    snippet=hit.get("story_text", "")[:300] or hit.get("title", ""),
                    source="hackernews",
                    author=hit.get("author"),
                    score=float(hit.get("points", 0)),
                    upvotes=hit.get("points"),
                    comments=hit.get("num_comments"),
                    published_at=hit.get("created_at"),
                    raw=hit,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class GitHubTrendingScraper:
    """GitHub trending page HTML scraping — no API key."""

    BASE_URL = "https://github.com/trending"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=2.0)

    async def trending(self, language: Optional[str] = None, since: str = "daily", max_results: int = 10) -> List[SocialResult]:
        """Scrape GitHub trending repositories."""
        await self.limiter.acquire("github.com", 2.0)
        url = self.BASE_URL
        if language:
            url += f"/{urllib.parse.quote(language)}"
        url += f"?since={since}"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"GitHub trending error: {e}", source="github_trending", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SocialResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SocialResult] = []
        for article in soup.find_all("article", class_="Box-row")[:max_results]:
            h2 = article.find("h2")
            if not h2:
                continue
            a = h2.find("a")
            if not a:
                continue
            repo_path = a.get("href", "").lstrip("/")
            title = a.get_text(strip=True).replace("\n", "").replace(" ", "")
            url = f"https://github.com/{repo_path}"
            desc_p = article.find("p", class_="col-9")
            snippet = desc_p.get_text(strip=True) if desc_p else ""
            lang_span = article.find("span", itemprop="programmingLanguage")
            lang = lang_span.get_text(strip=True) if lang_span else None
            stars_a = article.find("a", href=lambda x: x and "stargazers" in x)
            stars = 0
            if stars_a:
                stars_text = stars_a.get_text(strip=True).replace(",", "")
                try:
                    stars = int(stars_text)
                except ValueError:
                    pass
            results.append(
                SocialResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="github_trending",
                    author=repo_path.split("/")[0] if "/" in repo_path else None,
                    score=float(stars),
                    upvotes=stars,
                    raw={"language": lang},
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class StackOverflowScraper:
    """StackOverflow questions scraping via tagged pages."""

    BASE_URL = "https://stackoverflow.com/questions/tagged/"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search_tagged(self, tag: str, sort: str = "newest", max_results: int = 10) -> List[SocialResult]:
        """Get questions by tag."""
        await self.limiter.acquire("stackoverflow.com", 1.5)
        url = f"{self.BASE_URL}{urllib.parse.quote(tag)}"
        params = {"sort": sort, "pagesize": str(max_results)}
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"SO error: {e}", source="stackoverflow", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SocialResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SocialResult] = []
        for summary in soup.find_all("div", class_="s-post-summary")[:max_results]:
            title_a = summary.find("a", class_="s-link")
            if not title_a:
                continue
            title = title_a.get_text(strip=True)
            href = title_a.get("href", "")
            if href.startswith("/"):
                href = f"https://stackoverflow.com{href}"
            snippet_div = summary.find("div", class_="s-post-summary--content-excerpt")
            snippet = snippet_div.get_text(strip=True) if snippet_div else ""
            vote_div = summary.find("div", class_="s-post-summary--stats-item__emphasized")
            votes = 0
            if vote_div:
                vote_span = vote_div.find("span", class_="s-post-summary--stats-item-number")
                if vote_span:
                    try:
                        votes = int(vote_span.get_text(strip=True).replace("k", "000").replace("m", "000000"))
                    except ValueError:
                        pass
            ans_divs = summary.find_all("div", class_="s-post-summary--stats-item")
            answers = 0
            for d in ans_divs:
                if "answer" in (d.get("title", "") or d.get_text(strip=True).lower()):
                    num_span = d.find("span", class_="s-post-summary--stats-item-number")
                    if num_span:
                        try:
                            answers = int(num_span.get_text(strip=True))
                        except ValueError:
                            pass
            results.append(
                SocialResult(
                    title=title,
                    url=href,
                    snippet=snippet,
                    source="stackoverflow",
                    score=float(votes),
                    upvotes=votes,
                    comments=answers,
                )
            )
        return results

    async def close(self):
        await self.client.aclose()


class MediumScraper:
    """Medium tag page HTML scraping."""

    BASE_URL = "https://medium.com/tag/"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )
        self.limiter = RateLimiter(default_delay=1.5)

    async def search_tag(self, tag: str, max_results: int = 10) -> List[SocialResult]:
        """Get latest articles by tag."""
        await self.limiter.acquire("medium.com", 1.5)
        url = f"{self.BASE_URL}{urllib.parse.quote(tag)}"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return self._parse_html(resp.text, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"Medium error: {e}", source="medium", score=0.0)]

    def _parse_html(self, html_text: str, max_results: int) -> List[SocialResult]:
        soup = BeautifulSoup(html_text, "html.parser")
        results: List[SocialResult] = []
        # Medium serves a mix of JS-rendered and SSR content; grab article links
        for article in soup.find_all("article")[:max_results]:
            a = article.find("a")
            if not a:
                continue
            href = a.get("href", "")
            if href.startswith("/"):
                href = f"https://medium.com{href}"
            # Try to find title in nested h2/h1
            title_tag = article.find(["h1", "h2", "h3"])
            title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)
            snippet_p = article.find("p")
            snippet = snippet_p.get_text(strip=True)[:300] if snippet_p else ""
            author_a = article.find("a", href=re.compile(r"^/@"))
            author = author_a.get_text(strip=True) if author_a else None
            if title:
                results.append(
                    SocialResult(
                        title=title,
                        url=href,
                        snippet=snippet,
                        source="medium",
                        author=author,
                        score=0.7,
                    )
                )
        return results

    async def close(self):
        await self.client.aclose()


class DevToScraper:
    """Dev.to API — completely free, no key required."""

    API_URL = "https://dev.to/api/articles"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/vnd.forem.api-v1+json",
                "User-Agent": "TurkishJARVIS/1.0",
            },
        )
        self.limiter = RateLimiter(default_delay=1.0)

    async def search(self, query: str, max_results: int = 10) -> List[SocialResult]:
        """Search articles via Dev.to API (latest + client-side filter)."""
        await self.limiter.acquire("dev.to", 1.0)
        params: Dict[str, Any] = {"per_page": 50}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._filter(data, query, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"Dev.to error: {e}", source="devto", score=0.0)]

    async def latest_by_tag(self, tag: str, max_results: int = 10) -> List[SocialResult]:
        """Get latest articles by tag."""
        await self.limiter.acquire("dev.to", 1.0)
        params: Dict[str, Any] = {"tag": tag, "per_page": max_results}
        try:
            resp = await self.client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            return self._parse(data, max_results)
        except Exception as e:
            return [SocialResult(title="", url="", snippet=f"Dev.to error: {e}", source="devto", score=0.0)]

    def _filter(self, data: List[Dict], query: str, max_results: int) -> List[SocialResult]:
        results: List[SocialResult] = []
        q_lower = query.lower()
        for item in data:
            title = item.get("title", "")
            desc = item.get("description", "") or ""
            tags = " ".join(item.get("tag_list", []))
            combined = f"{title} {desc} {tags}".lower()
            if q_lower not in combined:
                continue
            results.append(self._to_result(item))
            if len(results) >= max_results:
                break
        return results

    def _parse(self, data: List[Dict], max_results: int) -> List[SocialResult]:
        return [self._to_result(item) for item in data[:max_results]]

    def _to_result(self, item: Dict) -> SocialResult:
        return SocialResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("description", "")[:300],
            source="devto",
            author=item.get("user", {}).get("username"),
            score=float(item.get("positive_reactions_count", 0)),
            upvotes=item.get("positive_reactions_count"),
            comments=item.get("comments_count"),
            published_at=item.get("published_at"),
            raw=item,
        )

    async def close(self):
        await self.client.aclose()


class SocialScraperAggregator:
    """Run all social/community scrapers and aggregate."""

    def __init__(self):
        self.reddit = RedditScraper()
        self.hackernews = HackerNewsScraper()
        self.github = GitHubTrendingScraper()
        self.stackoverflow = StackOverflowScraper()
        self.medium = MediumScraper()
        self.devto = DevToScraper()

    async def search_all(self, query: str, max_results: int = 10) -> Dict[str, List[SocialResult]]:
        """Search across all social sources."""
        tasks = {
            "reddit": asyncio.create_task(self.reddit.get_subreddit_posts("technology", max_results=max_results)),
            "hackernews": asyncio.create_task(self.hackernews.search(query, max_results)),
            "devto": asyncio.create_task(self.devto.search(query, max_results)),
        }
        results: Dict[str, List[SocialResult]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await asyncio.wait_for(asyncio.shield(task), timeout=35.0)
            except asyncio.TimeoutError:
                results[name] = [SocialResult(title="", url="", snippet="Timeout", source=name, score=0.0)]
            except Exception as e:
                results[name] = [SocialResult(title="", url="", snippet=f"Error: {e}", source=name, score=0.0)]
        return results

    async def trending_repos(self, language: Optional[str] = None, max_results: int = 10) -> List[SocialResult]:
        """Get trending GitHub repos."""
        return await self.github.trending(language=language, max_results=max_results)

    async def stackoverflow_questions(self, tag: str, max_results: int = 10) -> List[SocialResult]:
        """Get StackOverflow questions by tag."""
        return await self.stackoverflow.search_tagged(tag, max_results=max_results)

    async def medium_articles(self, tag: str, max_results: int = 10) -> List[SocialResult]:
        """Get Medium articles by tag."""
        return await self.medium.search_tag(tag, max_results=max_results)

    async def close(self):
        await asyncio.gather(
            self.reddit.close(),
            self.hackernews.close(),
            self.github.close(),
            self.stackoverflow.close(),
            self.medium.close(),
            self.devto.close(),
            return_exceptions=True,
        )


# ── Quick test helper ─────────────────────────────────────────────────────────
async def _demo():
    agg = SocialScraperAggregator()
    try:
        hn = await agg.hackernews.search("python", max_results=3)
        print("=== HackerNews ===")
        for it in hn:
            print(f"  {it.title[:60]} | {it.url[:60]}")
    finally:
        await agg.close()


if __name__ == "__main__":
    asyncio.run(_demo())
