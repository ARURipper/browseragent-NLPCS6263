"""Playwright-based headless Chrome session for web browsing."""

import base64
import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)


class BrowserSession:
    """Manages a Playwright browser session for web browsing."""

    def __init__(self, headless: bool = True):
        """
        Initialize browser session.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    def start(self) -> None:
        """Start the browser session."""
        logger.info("Starting browser session")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._page = self._browser.new_page()
        logger.info("Browser session started")

    def close(self) -> None:
        """Close the browser session."""
        logger.info("Closing browser session")
        if self._page:
            self._page.close()
            self._page = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.info("Browser session closed")

    def _ensure_started(self) -> None:
        """Ensure browser is started."""
        if self._page is None:
            raise RuntimeError("Browser session not started. Call start() first.")

    def _get_page_text(self) -> str:
        """Extract visible text from current page."""
        self._ensure_started()
        try:
            # Wait for page to be reasonably loaded
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            # Get text content from body
            text = self._page.inner_text("body")
            return text
        except Exception as e:
            logger.warning(f"Error extracting page text: {e}")
            return ""

    def goto(self, url: str) -> str:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            The page text content
        """
        self._ensure_started()
        logger.info(f"Navigating to: {url}")
        try:
            self._page.goto(url, timeout=30000)
            return self._get_page_text()
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return f"Error loading page: {e}"

    def scroll(self, direction: str) -> str:
        """
        Scroll the page.
        
        Args:
            direction: "up" or "down"
            
        Returns:
            The page text content after scrolling
        """
        self._ensure_started()
        logger.info(f"Scrolling {direction}")
        try:
            if direction == "down":
                self._page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                self._page.evaluate("window.scrollBy(0, -window.innerHeight)")
            else:
                logger.warning(f"Unknown scroll direction: {direction}")
            return self._get_page_text()
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return f"Error scrolling: {e}"

    def search_wikipedia(self, query: str) -> str:
        """
        Search Wikipedia for a query.
        
        Args:
            query: The search query
            
        Returns:
            The search results page text
        """
        self._ensure_started()
        logger.info(f"Searching Wikipedia for: {query}")
        search_url = f"https://en.wikipedia.org/w/index.php?search={query.replace(' ', '+')}"
        return self.goto(search_url)

    def current_url(self) -> str:
        """
        Get the current page URL.
        
        Returns:
            The current URL
        """
        self._ensure_started()
        return self._page.url

    def screenshot_base64(self) -> str:
        """
        Take a screenshot of the current page.
        
        Returns:
            Base64-encoded PNG screenshot
        """
        self._ensure_started()
        try:
            screenshot_bytes = self._page.screenshot()
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""
