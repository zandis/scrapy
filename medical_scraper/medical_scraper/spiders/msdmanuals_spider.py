"""Spider for scraping MSD Manuals professional medical content."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import scrapy

from medical_scraper.items import MedicalContentItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    from scrapy.http import Response


class MsdManualsSpider(scrapy.Spider):
    """Spider to crawl and scrape content from MSD Manuals Professional."""

    name = "msdmanuals"
    allowed_domains = ["msdmanuals.com"]
    start_urls = ["https://www.msdmanuals.com/professional"]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,  # More conservative for this site
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEPTH_LIMIT": 4,
    }

    def parse(self, response: Response) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse the main professional page and follow category links."""
        self.logger.info(f"Parsing main page: {response.url}")

        # Find all section/category links
        category_links = response.css(
            'a[href*="/professional/"]::attr(href)'
        ).getall()

        # Also get links from navigation
        nav_links = response.css(
            "nav a::attr(href), .navigation a::attr(href)"
        ).getall()

        # Get topic links
        topic_links = response.css(
            '.topic a::attr(href), .section a::attr(href), [class*="category"] a::attr(href)'
        ).getall()

        all_links = set(category_links + nav_links + topic_links)

        for link in all_links:
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_section,
                    errback=self.handle_error,
                    meta={"depth": 1},
                )

    def parse_section(
        self, response: Response
    ) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse section/category pages."""
        self.logger.info(f"Parsing section: {response.url}")
        current_depth = response.meta.get("depth", 1)

        # Check if this is a content page
        if self._is_content_page(response):
            yield from self._extract_item(response)

        # Follow links to topics and subsections
        topic_links = response.css('a[href*="/professional/"]::attr(href)').getall()

        for link in topic_links:
            full_url = urljoin(response.url, link)
            if self._should_follow(full_url):
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_topic,
                    errback=self.handle_error,
                    meta={"depth": current_depth + 1},
                )

    def parse_topic(
        self, response: Response
    ) -> Iterator[scrapy.Request | MedicalContentItem]:
        """Parse individual topic pages."""
        self.logger.info(f"Parsing topic: {response.url}")

        # Extract content from this page
        yield from self._extract_item(response)

        # Follow links to related topics (limited depth)
        current_depth = response.meta.get("depth", 1)
        if current_depth < 4:
            related_links = response.css(
                '.related a::attr(href), .see-also a::attr(href), a[href*="/professional/"]::attr(href)'
            ).getall()

            for link in related_links[:10]:  # Limit related links
                full_url = urljoin(response.url, link)
                if self._should_follow(full_url):
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_topic,
                        errback=self.handle_error,
                        meta={"depth": current_depth + 1},
                    )

    def _extract_item(
        self, response: Response
    ) -> Iterator[MedicalContentItem]:
        """Extract content item from response."""
        # Skip non-content pages
        if not self._is_content_page(response):
            return

        item = MedicalContentItem()
        item["url"] = response.url
        item["source"] = "msdmanuals"

        # Extract title
        item["title"] = self._extract_title(response)

        # Extract breadcrumbs
        item["breadcrumbs"] = self._extract_breadcrumbs(response)
        if item["breadcrumbs"]:
            item["category"] = item["breadcrumbs"][0] if item["breadcrumbs"] else None
            item["subcategory"] = (
                item["breadcrumbs"][1] if len(item["breadcrumbs"]) > 1 else None
            )

        # Extract content
        item["content"] = self._extract_content(response)
        item["html_content"] = self._extract_html_content(response)

        # Extract metadata
        item["last_updated"] = self._extract_date(response)

        # Only yield if we have meaningful content
        if item["content"] and len(item["content"]) > 200:
            yield item

    def _extract_title(self, response: Response) -> str:
        """Extract page title."""
        # MSD Manuals specific selectors
        title = (
            response.css("h1.topic-title::text").get()
            or response.css("h1::text").get()
            or response.css(".page-title::text").get()
            or response.css('meta[property="og:title"]::attr(content)').get()
            or response.css("title::text").get()
            or ""
        )
        # Clean up title
        title = title.strip()
        # Remove site name suffix if present
        title = re.sub(r"\s*[-|]\s*MSD.*$", "", title, flags=re.IGNORECASE)
        return title

    def _extract_breadcrumbs(self, response: Response) -> list[str]:
        """Extract breadcrumb navigation."""
        breadcrumbs = []

        # MSD Manuals breadcrumb selectors
        crumb_selectors = [
            ".breadcrumb a::text",
            ".breadcrumbs a::text",
            'nav[aria-label="breadcrumb"] a::text',
            ".crumb a::text",
            '[class*="breadcrumb"] a::text',
        ]

        for selector in crumb_selectors:
            crumbs = response.css(selector).getall()
            if crumbs:
                breadcrumbs = [c.strip() for c in crumbs if c.strip()]
                # Filter out "Home" and similar
                breadcrumbs = [
                    c
                    for c in breadcrumbs
                    if c.lower() not in ("home", "professional", "msd manual")
                ]
                break

        return breadcrumbs

    def _extract_content(self, response: Response) -> str:
        """Extract main text content."""
        # MSD Manuals specific content selectors
        content_selectors = [
            ".topic-content",
            ".article-content",
            "article",
            ".content-body",
            "main .content",
            "#topic-content",
        ]

        for selector in content_selectors:
            content_elem = response.css(selector)
            if content_elem:
                # Extract text, excluding scripts and styles
                text_parts = content_elem.css(
                    "p::text, p *::text, li::text, li *::text, h2::text, h3::text, h4::text"
                ).getall()
                text = " ".join(part.strip() for part in text_parts if part.strip())
                if len(text) > 200:
                    return self._clean_text(text)

        # Fallback
        text_parts = response.css(
            "main p::text, main p *::text, article p::text, article p *::text"
        ).getall()
        text = " ".join(part.strip() for part in text_parts if part.strip())
        return self._clean_text(text)

    def _extract_html_content(self, response: Response) -> str:
        """Extract HTML content of main article."""
        content_selectors = [
            ".topic-content",
            ".article-content",
            "article",
            "main",
        ]

        for selector in content_selectors:
            content = response.css(selector).get()
            if content:
                return content

        return response.css("body").get() or ""

    def _extract_date(self, response: Response) -> str | None:
        """Extract last reviewed or modified date."""
        # MSD Manuals often has review dates
        date_selectors = [
            ".last-reviewed::text",
            ".review-date::text",
            ".modified-date::text",
            'meta[name="last-modified"]::attr(content)',
            'meta[property="article:modified_time"]::attr(content)',
            "time::attr(datetime)",
        ]

        for selector in date_selectors:
            date = response.css(selector).get()
            if date:
                return date.strip()

        # Try to find date in text
        date_pattern = response.css("*::text").re_first(
            r"(?:Last\s+(?:reviewed|modified|updated))[:\s]*(\w+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})"
        )
        if date_pattern:
            return date_pattern

        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove common boilerplate
        boilerplate = [
            r"©\s*\d{4}.*?Inc\.",
            r"Cookie\s+(?:Policy|Settings)",
            r"Privacy\s+Policy",
            r"Terms\s+of\s+(?:Use|Service)",
        ]
        for pattern in boilerplate:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text.strip()

    def _should_follow(self, url: str) -> bool:
        """Determine if a URL should be followed."""
        parsed = urlparse(url)

        # Only follow links on allowed domains
        if parsed.netloc and "msdmanuals.com" not in parsed.netloc:
            return False

        # Must be professional section
        if "/professional" not in url.lower():
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
            r"/search",
            r"/quiz",
            r"/video",
            r"/multimedia",
            r"#",
            r"\?",
        ]
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in skip_patterns):
            return False

        return True

    def _is_content_page(self, response: Response) -> bool:
        """Check if page has substantial medical content."""
        # Check for content indicators
        has_article = bool(
            response.css("article, .topic-content, .article-content").get()
        )
        has_substantial_text = len(self._extract_content(response)) > 300

        return has_article or has_substantial_text

    def handle_error(self, failure: Any) -> None:
        """Handle request errors."""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")
