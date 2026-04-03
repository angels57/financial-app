"""Scraper module for fetching data from external websites."""

import re
from contextlib import suppress

from playwright.sync_api import sync_playwright

from core.logging import get_app_logger

logger = get_app_logger("GuruFocusScraper")

RETRY_ERRORS = (ConnectionError, TimeoutError, OSError)


class GuruFocusScraper:
    """Scrapes financial data from GuruFocus."""

    def __init__(self, headless: bool = True):
        """
        Initialize the scraper.

        Args:
            headless: Whether to run the browser in headless mode.
        """
        self.headless = headless

    def get_fair_value(self, ticker: str) -> float | None:
        """
        Scrape the GF Value (Fair Value) for a given ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            The fair value as a float, or None if not found or error.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                url = f"https://gurufocus.com/stock/{ticker}/valuation"
                page.goto(url, timeout=30000)

                locator = page.locator('a[href*="/term/gf-value/"]').first

                with suppress(Exception):
                    locator.wait_for(timeout=10000)

                if locator.count() > 0:
                    text = locator.inner_text()
                    match = re.search(r"\$\s*([\d,.]+)", text)
                    if match:
                        return float(match.group(1).replace(",", ""))

                return None

        except RETRY_ERRORS as e:
            logger.warning(f"get_fair_value failed for {ticker}: {e}")
            return None
