"""Middlewares for medical content scraping."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from scrapy.downloadermiddlewares.retry import RetryMiddleware as BaseRetryMiddleware

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.http import Response
    from scrapy.spiders import Spider


USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class RandomUserAgentMiddleware:
    """Middleware to rotate user agents randomly."""

    def process_request(self, request: Request, spider: Spider) -> None:
        request.headers["User-Agent"] = random.choice(USER_AGENTS)


class RetryMiddleware(BaseRetryMiddleware):
    """Extended retry middleware with better handling for blocked requests."""

    def process_response(
        self, request: Request, response: Response, spider: Spider
    ) -> Request | Response:
        if response.status == 403:
            # Log and retry with different user agent
            spider.logger.warning(
                f"Got 403 for {request.url}, retrying with different UA"
            )
            request.headers["User-Agent"] = random.choice(USER_AGENTS)
            return self._retry(request, "403 Forbidden", spider) or response

        return super().process_response(request, response, spider)
