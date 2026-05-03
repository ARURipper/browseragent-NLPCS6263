"""Playwright-based browser wrapper for the BrowserAgent.

Supports scrolling, clicking, typing, tab switching, and page state extraction.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Optional

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class BrowserStep:
    """One step in a browsing trajectory."""

    action: str
    action_args: dict
    url: str
    page_text: str
    screenshot_b64: Optional[str] = None


@dataclass
class BrowserSession:
    """Manages a live Playwright browser session."""

    start_url: str = "https://en.wikipedia.org"
    headless: bool = True
    _browser: object = field(default=None, init=False, repr=False)
    _page: object = field(default=None, init=False, repr=False)
    _playwright: object = field(default=None, init=False, repr=False)

    def start(self) -> None:
        """Launch Playwright and open a new page."""
        from playwright.sync_api import sync_playwright  # type: ignore

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = self._browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        self._page = context.new_page()
        self._page.goto(self.start_url, timeout=30000)
        logger.info("Browser session started, url=%s", self.start_url)

    def close(self) -> None:
        """Close the browser and Playwright cleanly."""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Browser session closed")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def goto(self, url: str) -> str:
        """Navigate to a URL and return visible text."""
        self._page.goto(url, timeout=30000)
        logger.info("goto url=%s", url)
        return self._extract_text()

    def click(self, selector: str) -> str:
        """Click an element by CSS selector."""
        self._page.click(selector, timeout=5000)
        self._page.wait_for_load_state("networkidle", timeout=10000)
        logger.info("click selector=%s", selector)
        return self._extract_text()

    def type_text(self, selector: str, text: str) -> str:
        """Click a field and type text, then press Enter."""
        self._page.fill(selector, text)
        self._page.press(selector, "Enter")
        self._page.wait_for_load_state("networkidle", timeout=10000)
        logger.info("type_text selector=%s text=%s", selector, text[:40])
        return self._extract_text()

    def scroll(self, direction: str = "down", amount: int = 500) -> str:
        """Scroll the page up or down by amount pixels."""
        delta = amount if direction == "down" else -amount
        self._page.evaluate(f"window.scrollBy(0, {delta})")
        logger.info("scroll direction=%s amount=%d", direction, amount)
        return self._extract_text()

    def search_wikipedia(self, query: str) -> str:
        """Navigate to Wikipedia search results for query."""
        encoded = query.replace(" ", "+")
        url = f"https://en.wikipedia.org/w/index.php?search={encoded}"
        return self.goto(url)

    def current_url(self) -> str:
        return self._page.url

    def screenshot_base64(self) -> str:
        """Capture a screenshot and return as base64 PNG."""
        data: bytes = self._page.screenshot(type="png")
        return base64.b64encode(data).decode()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _extract_text(self) -> str:
        """Extract visible text from the current page (truncated to 8000 chars)."""
        try:
            text: str = self._page.inner_text("body")
        except Exception:
            text = self._page.content()
            text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:8000]
