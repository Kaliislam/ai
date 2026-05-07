"""Browser automation module using Playwright.

Provides a sandboxed browser client that can navigate, extract content,
perform searches, click elements, and take screenshots.
Content is returned in an accessibility-tree-like format for LLM consumption.

Requires:
    playwright (and its browsers)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PageSnapshot:
    """Snapshot of a web page for LLM consumption."""

    url: str
    title: str
    text_content: str
    links: List[Dict[str, str]]
    forms: List[Dict[str, Any]]
    accessibility_tree: str


# ---------------------------------------------------------------------------
# Browser Client
# ---------------------------------------------------------------------------


class BrowserClient:
    """Async browser automation client backed by Playwright.

    Usage:
        browser = BrowserClient(headless=True)
        await browser.start()
        snap = await browser.navigate("https://example.com")
        await browser.click("button#submit")
        png = await browser.screenshot()
        await browser.stop()
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        user_agent: Optional[str] = None,
        timeout: float = 30.0,
        sandbox: bool = True,
    ) -> None:
        self.headless = headless
        self.browser_type = browser_type
        self.user_agent = user_agent
        self.timeout = timeout
        self.sandbox = sandbox
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Launch the browser instance."""
        try:
            from playwright.async_api import async_playwright  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("playwright is required for BrowserClient") from exc

        self._playwright = await async_playwright().start()
        browser_cls = getattr(self._playwright, self.browser_type, None)
        if browser_cls is None:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")

        args: List[str] = []
        if not self.sandbox:
            args.append("--no-sandbox")
        args.extend(["--disable-dev-shm-usage", "--disable-gpu"])

        self._browser = await browser_cls.launch(
            headless=self.headless,
            args=args,
        )
        self._context = await self._browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1280, "height": 720},
        )
        self._page = await self._context.new_page()
        logger.info("Browser started: %s (headless=%s)", self.browser_type, self.headless)

    async def stop(self) -> None:
        """Close the browser."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser stopped")

    # ------------------------------------------------------------------
    # Navigation & content
    # ------------------------------------------------------------------

    async def navigate(self, url: str, wait_until: str = "networkidle") -> PageSnapshot:
        """Navigate to a URL and return a snapshot."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        await self._page.goto(url, wait_until=wait_until, timeout=int(self.timeout * 1000))
        return await self.get_content()

    async def get_content(self) -> PageSnapshot:
        """Extract page content as an accessibility-friendly snapshot."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        title = await self._page.title()
        url = self._page.url

        # Accessibility tree via Playwright's snapshot
        snapshot_text = await self._page.accessibility.snapshot()
        tree_str = json.dumps(snapshot_text, ensure_ascii=False, indent=2)

        # Visible text
        text_content = await self._page.evaluate(
            """() => document.body.innerText.substring(0, 8000)"""
        )

        # Links
        links = await self._page.eval_on_selector_all(
            "a[href]",
            """elements => elements.map(e => ({
                text: e.innerText.trim().substring(0, 80),
                href: e.href,
            }))""",
        )

        # Forms
        forms = await self._page.eval_on_selector_all(
            "form",
            """forms => forms.map(f => {
                const inputs = Array.from(f.querySelectorAll('input, textarea, select'))
                    .map(i => ({
                        type: i.type || i.tagName.toLowerCase(),
                        name: i.name,
                        id: i.id,
                    }));
                return { action: f.action, method: f.method, inputs };
            })""",
        )

        return PageSnapshot(
            url=url,
            title=title,
            text_content=text_content or "",
            links=links or [],
            forms=forms or [],
            accessibility_tree=tree_str,
        )

    async def search(self, query: str, engine: str = "duckduckgo") -> PageSnapshot:
        """Perform a web search and land on the results page.

        Supported engines: duckduckgo, bing (limited)
        """
        if engine == "duckduckgo":
            url = f"https://duckduckgo.com/html/?q={self._quote(query)}"
        elif engine == "bing":
            url = f"https://www.bing.com/search?q={self._quote(query)}"
        else:
            raise ValueError(f"Unsupported search engine: {engine}")
        return await self.navigate(url)

    @staticmethod
    def _quote(text: str) -> str:
        from urllib.parse import quote_plus
        return quote_plus(text)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    async def click(self, selector: str) -> None:
        """Click an element by CSS selector."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        await self._page.click(selector, timeout=int(self.timeout * 1000))

    async def fill(self, selector: str, value: str) -> None:
        """Fill an input field."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        await self._page.fill(selector, value)

    async def press(self, key: str) -> None:
        """Press a keyboard key."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        await self._page.keyboard.press(key)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        if direction == "down":
            await self._page.evaluate(f"window.scrollBy(0, {amount})")
        elif direction == "up":
            await self._page.evaluate(f"window.scrollBy(0, -{amount})")

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    async def screenshot(self, full_page: bool = False) -> bytes:
        """Take a screenshot and return PNG bytes."""
        if self._page is None:
            raise RuntimeError("Browser not started")
        return await self._page.screenshot(full_page=full_page, type="png")

    async def screenshot_base64(self, full_page: bool = False) -> str:
        """Take a screenshot and return base64-encoded PNG."""
        png = await self.screenshot(full_page=full_page)
        return base64.b64encode(png).decode("ascii")

    # ------------------------------------------------------------------
    # Sandbox execution (subprocess wrapper)
    # ------------------------------------------------------------------

    @classmethod
    async def run_in_sandbox(
        cls,
        script: str,
        timeout: float = 60.0,
        headless: bool = True,
    ) -> Dict[str, Any]:
        """Run a browser script in a separate subprocess with a timeout.

        This is useful for isolating untrusted page interactions.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            script_path = f.name

        cmd = [
            sys.executable if "sys" in globals() else "python",
            script_path,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                stdout, stderr = await proc.communicate()
                return {"ok": False, "error": "timeout", "stdout": "", "stderr": stderr.decode("utf-8", errors="replace")}
            return {
                "ok": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    def snapshot_to_llm_prompt(self, snapshot: PageSnapshot) -> str:
        """Convert a page snapshot into a compact LLM-readable string."""
        lines = [
            f"URL: {snapshot.url}",
            f"Title: {snapshot.title}",
            "",
            "--- Text Content ---",
            snapshot.text_content[:4000],
            "",
            "--- Links ---",
        ]
        for link in snapshot.links[:20]:
            lines.append(f"- [{link.get('text', '')}] ({link.get('href', '')})")
        lines.append("")
        lines.append("--- Accessibility Tree ---")
        lines.append(snapshot.accessibility_tree[:3000])
        return "\n".join(lines)

    async def __aenter__(self) -> "BrowserClient":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any],
        exc_val: Optional[Any],
        exc_tb: Optional[Any],
    ) -> None:
        await self.stop()
