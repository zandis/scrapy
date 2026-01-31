"""Spider for scraping MSD Manuals with Playwright for JavaScript rendering."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import scrapy

from medical_scraper.items import MedicalContentItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapy.http import Response


class MsdManualsPlaywrightSpider(scrapy.Spider):
    """Spider to crawl MSD Manuals Professional using Playwright.

    This spider uses scrapy-playwright for JavaScript rendering.
    Install with: pip install scrapy-playwright && playwright install chromium
    """

    name = "msdmanuals_pw"
    allowed_domains = ["msdmanuals.com"]
    start_urls = ["https://www.msdmanuals.com/professional"]

    custom_settings = {
        "DOWNLOAD_DELAY": 4,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEPTH_LIMIT": 4,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 45000,
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
        """Parse the main professional page."""
        self.logger.info(f"Parsing main page: {response.url}")

        # Find all professional section links
        links = response.css('a[href*="/professional/"]::attr(href)').getall()

        for link in links:
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_section,
                    errback=self.handle_error,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            {"method": "wait_for_load_state", "args": ["networkidle"]},
                        ],
                        "depth": 1,
                    },
                )

    def parse_section(
        self, response: Response
    ) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse section pages."""
        self.logger.info(f"Parsing section: {response.url}")
        depth = response.meta.get("depth", 1)

        # Extract content if this is a content page
        if self._has_content(response):
            yield from self._extract_item(response)

        # Follow topic links
        if depth < 4:
            links = response.css('a[href*="/professional/"]::attr(href)').getall()
            for link in links[:20]:  # Limit links per page
                full_url = urljoin(response.url, link)
                if self._should_follow(full_url):
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_section,
                        errback=self.handle_error,
                        meta={
                            "playwright": True,
                            "playwright_page_methods": [
                                {"method": "wait_for_load_state", "args": ["networkidle"]},
                            ],
                            "depth": depth + 1,
                        },
                    )

    def _extract_item(self, response: Response) -> Iterator[MedicalContentItem]:
        """Extract content item."""
        content = self._extract_content(response)
        if len(content) < 200:
            return

        item = MedicalContentItem()
        item["url"] = response.url
        item["source"] = "msdmanuals"
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
            response.css("h1.topic-title::text").get()
            or response.css("h1::text").get()
            or response.css('meta[property="og:title"]::attr(content)').get()
            or response.css("title::text").get()
            or ""
        )
        title = title.strip()
        # Remove site name suffix
        title = re.sub(r"\s*[-|]\s*MSD.*$", "", title, flags=re.I)
        return title

    def _extract_breadcrumbs(self, response: Response) -> list[str]:
        """Extract breadcrumbs."""
        for selector in [".breadcrumb a::text", ".breadcrumbs a::text", '[class*="breadcrumb"] a::text']:
            crumbs = response.css(selector).getall()
            if crumbs:
                crumbs = [c.strip() for c in crumbs if c.strip()]
                # Filter out common items
                return [c for c in crumbs if c.lower() not in ("home", "professional", "msd manual")]
        return []

    def _extract_content(self, response: Response) -> str:
        """Extract main content."""
        for selector in [".topic-content", ".article-content", "article", ".content-body"]:
            elem = response.css(selector)
            if elem:
                parts = elem.css("p::text, p *::text, li::text, h2::text, h3::text").getall()
                text = " ".join(p.strip() for p in parts if p.strip())
                if len(text) > 200:
                    return re.sub(r"\s+", " ", text).strip()
        return ""

    def _extract_html_content(self, response: Response) -> str:
        """Extract HTML content."""
        for selector in [".topic-content", ".article-content", "article"]:
            content = response.css(selector).get()
            if content:
                return content
        return response.css("body").get() or ""

    def _extract_date(self, response: Response) -> str | None:
        """Extract review/modified date."""
        selectors = [
            ".last-reviewed::text",
            'meta[property="article:modified_time"]::attr(content)',
            "time::attr(datetime)",
        ]
        for selector in selectors:
            date = response.css(selector).get()
            if date:
                return date.strip()
        return None

    def _should_follow(self, url: str) -> bool:
        """Check if URL should be followed."""
        parsed = urlparse(url)

        if parsed.netloc and "msdmanuals.com" not in parsed.netloc:
            return False

        if "/professional" not in url.lower():
            return False

        skip_ext = {".pdf", ".jpg", ".png", ".gif", ".css", ".js"}
        if any(parsed.path.lower().endswith(ext) for ext in skip_ext):
            return False

        skip_patterns = [r"/login", r"/search", r"/quiz", r"/video", r"#", r"\?"]
        return not any(re.search(p, url, re.I) for p in skip_patterns)

    def _has_content(self, response: Response) -> bool:
        """Check if page has medical content."""
        has_article = bool(response.css("article, .topic-content, .article-content").get())
        has_text = len(self._extract_content(response)) > 300
        return has_article or has_text

    def handle_error(self, failure: Any) -> None:
        """Handle errors."""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
