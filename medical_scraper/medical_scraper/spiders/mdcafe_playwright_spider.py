"""Spider for scraping md.cafe with Playwright for JavaScript rendering."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import scrapy

from medical_scraper.items import MedicalContentItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapy.http import Response


class MdCafePlaywrightSpider(scrapy.Spider):
    """Spider to crawl md.cafe using Playwright for JavaScript rendering.

    This spider uses scrapy-playwright for sites that require JavaScript.
    Install with: pip install scrapy-playwright && playwright install chromium
    """

    name = "mdcafe_pw"
    allowed_domains = ["md.cafe"]
    start_urls = ["https://md.cafe/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    def start_requests(self) -> Iterator[scrapy.Request]:
        """Generate start requests with Playwright meta."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    "playwright": True,
                    "playwright_include_page": False,
                    "playwright_page_methods": [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                    ],
                },
            )

    def parse(self, response: Response) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse the main page and follow links."""
        self.logger.info(f"Parsing: {response.url}")

        # Extract navigation and content links
        all_links = set(response.css("a::attr(href)").getall())

        for link in all_links:
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_page,
                    errback=self.handle_error,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            {"method": "wait_for_load_state", "args": ["networkidle"]},
                        ],
                    },
                )

        # Parse current page if it has content
        if self._has_content(response):
            yield from self._extract_item(response)

    def parse_page(
        self, response: Response
    ) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse individual content pages."""
        self.logger.info(f"Parsing page: {response.url}")

        # Extract content
        yield from self._extract_item(response)

        # Follow more links
        for link in response.css("a::attr(href)").getall():
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_page,
                    errback=self.handle_error,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            {"method": "wait_for_load_state", "args": ["networkidle"]},
                        ],
                    },
                )

    def _extract_item(self, response: Response) -> Iterator[MedicalContentItem]:
        """Extract content item from response."""
        content = self._extract_content(response)
        if len(content) < 100:
            return

        item = MedicalContentItem()
        item["url"] = response.url
        item["source"] = "md_cafe"
        item["title"] = self._extract_title(response)
        item["breadcrumbs"] = self._extract_breadcrumbs(response)

        if item["breadcrumbs"]:
            item["category"] = item["breadcrumbs"][0]
            item["subcategory"] = item["breadcrumbs"][1] if len(item["breadcrumbs"]) > 1 else None

        item["content"] = content
        item["html_content"] = self._extract_html_content(response)
        item["last_updated"] = self._extract_date(response)

        yield item

    def _extract_title(self, response: Response) -> str:
        """Extract page title."""
        title = (
            response.css("h1::text").get()
            or response.css("title::text").get()
            or ""
        )
        return title.strip()

    def _extract_breadcrumbs(self, response: Response) -> list[str]:
        """Extract breadcrumb navigation."""
        for selector in [".breadcrumb a::text", ".breadcrumbs a::text", 'nav[aria-label="breadcrumb"] a::text']:
            crumbs = response.css(selector).getall()
            if crumbs:
                return [c.strip() for c in crumbs if c.strip()]
        return []

    def _extract_content(self, response: Response) -> str:
        """Extract main text content."""
        for selector in ["article", "main", ".content", "#content"]:
            elem = response.css(selector)
            if elem:
                parts = elem.css("*:not(script):not(style)::text").getall()
                text = " ".join(p.strip() for p in parts if p.strip())
                if len(text) > 100:
                    return re.sub(r"\s+", " ", text).strip()
        return ""

    def _extract_html_content(self, response: Response) -> str:
        """Extract HTML content."""
        for selector in ["article", "main", ".content"]:
            content = response.css(selector).get()
            if content:
                return content
        return response.css("body").get() or ""

    def _extract_date(self, response: Response) -> str | None:
        """Extract date."""
        for selector in ['meta[property="article:modified_time"]::attr(content)', "time::attr(datetime)"]:
            date = response.css(selector).get()
            if date:
                return date.strip()
        return None

    def _should_follow(self, url: str) -> bool:
        """Check if URL should be followed."""
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc not in self.allowed_domains:
            return False

        skip_ext = {".pdf", ".jpg", ".png", ".gif", ".css", ".js", ".zip"}
        if any(parsed.path.lower().endswith(ext) for ext in skip_ext):
            return False

        skip_patterns = [r"/login", r"/register", r"/search", r"#"]
        return not any(re.search(p, url, re.I) for p in skip_patterns)

    def _has_content(self, response: Response) -> bool:
        """Check if page has content."""
        return len(self._extract_content(response)) > 200

    def handle_error(self, failure: Any) -> None:
        """Handle errors."""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
