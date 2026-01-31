"""Spider for scraping md.cafe medical content."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import scrapy

from medical_scraper.items import MedicalContentItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapy.http import Response


class MdCafeSpider(scrapy.Spider):
    """Spider to crawl and scrape content from md.cafe."""

    name = "mdcafe"
    allowed_domains = ["md.cafe"]
    start_urls = ["https://md.cafe/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def parse(self, response: Response) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse the main page and follow links to content pages."""
        self.logger.info(f"Parsing: {response.url}")

        # Extract and follow navigation links
        nav_links = response.css("nav a::attr(href), .nav a::attr(href)").getall()
        menu_links = response.css(
            ".menu a::attr(href), .sidebar a::attr(href)"
        ).getall()
        content_links = response.css(
            "main a::attr(href), article a::attr(href), .content a::attr(href)"
        ).getall()

        all_links = set(nav_links + menu_links + content_links)

        for link in all_links:
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_page,
                    errback=self.handle_error,
                )

        # Also parse the current page if it has content
        if self._is_content_page(response):
            yield from self.parse_page(response)

    def parse_page(
        self, response: Response
    ) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse individual content pages."""
        self.logger.info(f"Parsing page: {response.url}")

        # Skip non-HTML responses
        content_type = response.headers.get("Content-Type", b"").decode()
        if "text/html" not in content_type and not response.css("html"):
            return

        # Extract content
        item = MedicalContentItem()
        item["url"] = response.url
        item["source"] = "md_cafe"

        # Extract title
        item["title"] = self._extract_title(response)

        # Extract breadcrumbs/category
        item["breadcrumbs"] = self._extract_breadcrumbs(response)
        if item["breadcrumbs"]:
            item["category"] = item["breadcrumbs"][0] if item["breadcrumbs"] else None
            item["subcategory"] = (
                item["breadcrumbs"][1] if len(item["breadcrumbs"]) > 1 else None
            )

        # Extract main content
        item["content"] = self._extract_content(response)
        item["html_content"] = self._extract_html_content(response)

        # Extract last updated date if available
        item["last_updated"] = self._extract_date(response)

        # Only yield if we have meaningful content
        if item["content"] and len(item["content"]) > 100:
            yield item

        # Follow links to other content pages
        for link in response.css("a::attr(href)").getall():
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_page,
                    errback=self.handle_error,
                )

    def _extract_title(self, response: Response) -> str:
        """Extract page title."""
        # Try various title selectors
        title = (
            response.css("h1::text").get()
            or response.css("article h1::text").get()
            or response.css(".title::text").get()
            or response.css("title::text").get()
            or ""
        )
        return title.strip()

    def _extract_breadcrumbs(self, response: Response) -> list[str]:
        """Extract breadcrumb navigation."""
        breadcrumbs = []

        # Try various breadcrumb selectors
        crumb_selectors = [
            ".breadcrumb a::text",
            ".breadcrumbs a::text",
            'nav[aria-label="breadcrumb"] a::text',
            ".crumbs a::text",
        ]

        for selector in crumb_selectors:
            crumbs = response.css(selector).getall()
            if crumbs:
                breadcrumbs = [c.strip() for c in crumbs if c.strip()]
                break

        return breadcrumbs

    def _extract_content(self, response: Response) -> str:
        """Extract main text content."""
        # Try to find main content area
        content_selectors = [
            "article",
            "main",
            ".content",
            ".article-content",
            ".post-content",
            ".entry-content",
            "#content",
        ]

        for selector in content_selectors:
            content_elem = response.css(selector)
            if content_elem:
                # Remove script and style elements
                text_parts = content_elem.css(
                    "*:not(script):not(style)::text"
                ).getall()
                text = " ".join(part.strip() for part in text_parts if part.strip())
                if len(text) > 100:
                    return self._clean_text(text)

        # Fallback to body content
        text_parts = response.css("body *:not(script):not(style)::text").getall()
        text = " ".join(part.strip() for part in text_parts if part.strip())
        return self._clean_text(text)

    def _extract_html_content(self, response: Response) -> str:
        """Extract HTML content of main article."""
        content_selectors = [
            "article",
            "main",
            ".content",
            ".article-content",
        ]

        for selector in content_selectors:
            content = response.css(selector).get()
            if content:
                return content

        return response.css("body").get() or ""

    def _extract_date(self, response: Response) -> str | None:
        """Extract last updated or published date."""
        date_selectors = [
            'meta[property="article:modified_time"]::attr(content)',
            'meta[property="article:published_time"]::attr(content)',
            "time::attr(datetime)",
            ".date::text",
            ".published::text",
            ".updated::text",
        ]

        for selector in date_selectors:
            date = response.css(selector).get()
            if date:
                return date.strip()

        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove common boilerplate phrases
        boilerplate = [
            r"Cookie\s+Policy",
            r"Privacy\s+Policy",
            r"Terms\s+of\s+Service",
            r"All\s+rights\s+reserved",
        ]
        for pattern in boilerplate:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text.strip()

    def _should_follow(self, url: str) -> bool:
        """Determine if a URL should be followed."""
        parsed = urlparse(url)

        # Only follow links on allowed domains
        if parsed.netloc and parsed.netloc not in self.allowed_domains:
            return False

        # Skip certain file types
        skip_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".css",
            ".js",
            ".zip",
            ".mp4",
            ".mp3",
        }
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip certain URL patterns
        skip_patterns = [
            r"/login",
            r"/register",
            r"/signup",
            r"/cart",
            r"/checkout",
            r"/search",
            r"/tag/",
            r"/author/",
            r"#",
        ]
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in skip_patterns):
            return False

        return True

    def _is_content_page(self, response: Response) -> bool:
        """Check if page has substantial content."""
        content = self._extract_content(response)
        return len(content) > 200

    def handle_error(self, failure: Any) -> None:
        """Handle request errors."""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
