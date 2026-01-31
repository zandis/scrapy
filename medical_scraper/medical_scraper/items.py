"""Items for medical content scraping."""

from __future__ import annotations

import scrapy


class MedicalContentItem(scrapy.Item):
    """Item representing scraped medical content."""

    # Page identification
    url = scrapy.Field()
    title = scrapy.Field()
    source = scrapy.Field()  # 'md_cafe' or 'msdmanuals'

    # Content
    content = scrapy.Field()
    html_content = scrapy.Field()

    # Metadata
    category = scrapy.Field()
    subcategory = scrapy.Field()
    breadcrumbs = scrapy.Field()
    last_updated = scrapy.Field()

    # File info
    filename = scrapy.Field()
    scraped_at = scrapy.Field()
