"""Ruflo Browser Plugin Bridge.

Wraps the existing Playwright-based BrowserClient from
``turkish_jarvis.integrations.browser`` and adds Ruflo-style
high-level helpers: batch navigation, content extraction pipelines,
LLM-ready prompt builders, and a simple crawling mode.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloBrowser:
    """High-level browser bridge inspired by ruflo-browser.

    Usage
    -----
    browser = RufloBrowser()
    await browser.start()
    snap = await browser.visit("https://example.com")
    md = browser.snapshot_to_markdown(snap)
    await browser.stop()
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        timeout: float = 30.0,
    ) -> None:
        self.headless = headless
        self.browser_type = browser_type
        self.timeout = timeout
        self._client: Any = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the underlying Playwright browser."""
        from turkish_jarvis.integrations.browser import BrowserClient

        self._client = BrowserClient(
            headless=self.headless,
            browser_type=self.browser_type,
            timeout=self.timeout,
        )
        await self._client.start()
        logger.info("[ruflo-browser] started")

    async def stop(self) -> None:
        """Stop the browser."""
        if self._client:
            await self._client.stop()
            self._client = None
            logger.info("[ruflo-browser] stopped")

    # ------------------------------------------------------------------
    # Core navigation
    # ------------------------------------------------------------------

    async def visit(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL and return a serializable snapshot dict."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        snap = await self._client.navigate(url)
        return {
            "url": snap.url,
            "title": snap.title,
            "text_content": snap.text_content,
            "links": snap.links[:30],
            "forms": snap.forms[:10],
            "accessibility_tree": snap.accessibility_tree[:2000],
        }

    async def search(self, query: str, engine: str = "duckduckgo") -> Dict[str, Any]:
        """Run a web search and return the results page snapshot."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        snap = await self._client.search(query, engine=engine)
        return {
            "url": snap.url,
            "title": snap.title,
            "text_content": snap.text_content,
            "links": snap.links[:30],
        }

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    async def click(self, selector: str) -> None:
        """Click an element by CSS selector."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        await self._client.click(selector)

    async def fill(self, selector: str, value: str) -> None:
        """Fill a form input."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        await self._client.fill(selector, value)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        await self._client.scroll(direction, amount)

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    async def screenshot(self, full_page: bool = False) -> bytes:
        """Take a PNG screenshot."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        return await self._client.screenshot(full_page=full_page)

    async def screenshot_base64(self, full_page: bool = False) -> str:
        """Take a screenshot and return a base64 string."""
        if self._client is None:
            raise RuntimeError("Browser not started")
        return await self._client.screenshot_base64(full_page=full_page)

    # ------------------------------------------------------------------
    # Ruflo-style helpers
    # ------------------------------------------------------------------

    def snapshot_to_markdown(self, snapshot: Dict[str, Any]) -> str:
        """Convert a snapshot dict into a compact markdown prompt for LLMs."""
        lines = [
            f"# {snapshot.get('title', 'No title')}",
            f"URL: {snapshot.get('url', '')}",
            "",
            "## Text Content",
            snapshot.get("text_content", "")[:4000],
            "",
            "## Links",
        ]
        for link in snapshot.get("links", [])[:20]:
            text = link.get("text", "")
            href = link.get("href", "")
            lines.append(f"- [{text}]({href})")
        return "\n".join(lines)

    async def batch_visit(
        self, urls: List[str], delay_sec: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Visit multiple URLs sequentially with a delay between each."""
        results: List[Dict[str, Any]] = []
        for url in urls:
            try:
                snap = await self.visit(url)
                results.append({"url": url, "ok": True, "snapshot": snap})
            except Exception as exc:
                results.append({"url": url, "ok": False, "error": str(exc)})
            if delay_sec:
                await asyncio.sleep(delay_sec)
        return results

    async def crawl(
        self, start_url: str, max_depth: int = 1, same_domain: bool = True
    ) -> List[Dict[str, Any]]:
        """Simple breadth-first crawler (depth-limited).

        Returns a list of page snapshots.
        """
        from urllib.parse import urlparse

        visited: set[str] = set()
        results: List[Dict[str, Any]] = []
        frontier: List[tuple[str, int]] = [(start_url, 0)]
        base_domain = urlparse(start_url).netloc

        while frontier:
            url, depth = frontier.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            try:
                snap = await self.visit(url)
                results.append({"url": url, "depth": depth, "snapshot": snap})
                if depth < max_depth:
                    for link in snap.get("links", []):
                        href = link.get("href", "")
                        if not href.startswith("http"):
                            continue
                        if same_domain and urlparse(href).netloc != base_domain:
                            continue
                        if href not in visited:
                            frontier.append((href, depth + 1))
            except Exception as exc:
                results.append({"url": url, "depth": depth, "error": str(exc)})
        return results

    async def extract_table(self, selector: str = "table") -> List[List[str]]:
        """Extract all rows from the first matching table as a 2-D list."""
        if self._client is None or self._client._page is None:
            raise RuntimeError("Browser not started")
        rows = await self._client._page.eval_on_selector_all(
            f"{selector} tr",
            """rows => rows.map(r =>
                Array.from(r.querySelectorAll('td, th')).map(c => c.innerText.trim())
            )""",
        )
        return rows or []

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "RufloBrowser":
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.stop()
