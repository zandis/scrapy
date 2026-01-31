"""Pipelines for saving scraped medical content."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrapy import Spider

    from medical_scraper.items import MedicalContentItem


class ContentSavePipeline:
    """Pipeline to save scraped content to separate folders based on source."""

    def __init__(self) -> None:
        self.output_dirs: dict[str, Path] = {}

    def open_spider(self, spider: Spider) -> None:
        """Set up output directories when spider opens."""
        base_dir = Path(spider.settings.get("OUTPUT_DIR", "output"))

        self.output_dirs = {
            "md_cafe": base_dir / "md_cafe",
            "msdmanuals": base_dir / "msdmanuals",
        }

        # Create directories if they don't exist
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / "html").mkdir(exist_ok=True)
            (dir_path / "text").mkdir(exist_ok=True)
            (dir_path / "json").mkdir(exist_ok=True)

    def process_item(
        self, item: MedicalContentItem, spider: Spider
    ) -> MedicalContentItem:
        """Save item content to appropriate folder."""
        source = item.get("source", "unknown")
        output_dir = self.output_dirs.get(source)

        if not output_dir:
            spider.logger.warning(f"Unknown source: {source}, skipping save")
            return item

        # Generate safe filename
        filename = self._generate_filename(item)
        item["filename"] = filename
        item["scraped_at"] = datetime.now(timezone.utc).isoformat()

        # Save HTML content
        if item.get("html_content"):
            html_path = output_dir / "html" / f"{filename}.html"
            html_path.write_text(item["html_content"], encoding="utf-8")
            spider.logger.info(f"Saved HTML: {html_path}")

        # Save text content
        if item.get("content"):
            text_path = output_dir / "text" / f"{filename}.txt"
            text_content = self._format_text_content(item)
            text_path.write_text(text_content, encoding="utf-8")
            spider.logger.info(f"Saved text: {text_path}")

        # Save JSON metadata
        json_path = output_dir / "json" / f"{filename}.json"
        json_data = {
            "url": item.get("url"),
            "title": item.get("title"),
            "source": source,
            "category": item.get("category"),
            "subcategory": item.get("subcategory"),
            "breadcrumbs": item.get("breadcrumbs"),
            "last_updated": item.get("last_updated"),
            "scraped_at": item.get("scraped_at"),
            "filename": filename,
        }
        json_path.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        return item

    def _generate_filename(self, item: MedicalContentItem) -> str:
        """Generate a safe filename from item title and URL."""
        title = item.get("title", "untitled")
        # Clean the title for use as filename
        filename = re.sub(r"[^\w\s-]", "", title)
        filename = re.sub(r"[-\s]+", "-", filename).strip("-")
        filename = filename[:100]  # Limit length

        # Add hash of URL for uniqueness
        url = item.get("url", "")
        url_hash = str(hash(url))[-8:]

        return f"{filename}_{url_hash}" if filename else f"page_{url_hash}"

    def _format_text_content(self, item: MedicalContentItem) -> str:
        """Format item as readable text content."""
        lines = []

        if item.get("title"):
            lines.append(f"Title: {item['title']}")
            lines.append("=" * 80)

        if item.get("url"):
            lines.append(f"Source URL: {item['url']}")

        if item.get("category"):
            lines.append(f"Category: {item['category']}")

        if item.get("subcategory"):
            lines.append(f"Subcategory: {item['subcategory']}")

        if item.get("breadcrumbs"):
            lines.append(f"Path: {' > '.join(item['breadcrumbs'])}")

        if item.get("last_updated"):
            lines.append(f"Last Updated: {item['last_updated']}")

        lines.append("")
        lines.append("-" * 80)
        lines.append("")

        if item.get("content"):
            lines.append(item["content"])

        return "\n".join(lines)
