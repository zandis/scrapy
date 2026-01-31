#!/usr/bin/env python3
"""Run script for medical content scrapers."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run medical content scrapers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run test spider to verify pipeline
  python run_scraper.py --test

  # Scrape md.cafe (standard)
  python run_scraper.py --site mdcafe

  # Scrape MSD Manuals (standard)
  python run_scraper.py --site msdmanuals

  # Scrape with Playwright (for JS-heavy sites)
  python run_scraper.py --site mdcafe --playwright

  # Scrape both sites
  python run_scraper.py --site all

  # Run with verbose logging
  python run_scraper.py --site mdcafe --verbose
        """,
    )

    parser.add_argument(
        "--site",
        choices=["mdcafe", "msdmanuals", "all"],
        help="Site to scrape",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test spider to verify pipeline works",
    )
    parser.add_argument(
        "--playwright",
        action="store_true",
        help="Use Playwright spiders for JavaScript rendering",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory (default: output)",
    )

    args = parser.parse_args()

    if not args.site and not args.test:
        parser.print_help()
        return 1

    # Change to script directory
    script_dir = Path(__file__).parent

    log_level = "DEBUG" if args.verbose else "INFO"

    def run_spider(spider_name: str) -> int:
        """Run a spider with scrapy crawl."""
        cmd = [
            sys.executable,
            "-m",
            "scrapy",
            "crawl",
            spider_name,
            "-s",
            f"LOG_LEVEL={log_level}",
            "-s",
            f"OUTPUT_DIR={args.output}",
        ]
        print(f"\n{'='*60}")
        print(f"Running spider: {spider_name}")
        print(f"{'='*60}\n")
        result = subprocess.run(cmd, cwd=script_dir)
        return result.returncode

    if args.test:
        return run_spider("test")

    spiders = []

    if args.site in ("mdcafe", "all"):
        spiders.append("mdcafe_pw" if args.playwright else "mdcafe")

    if args.site in ("msdmanuals", "all"):
        spiders.append("msdmanuals_pw" if args.playwright else "msdmanuals")

    exit_code = 0
    for spider in spiders:
        code = run_spider(spider)
        if code != 0:
            exit_code = code

    print(f"\n{'='*60}")
    print(f"Scraping complete. Output saved to: {args.output}/")
    print(f"{'='*60}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
