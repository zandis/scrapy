# Medical Content Scraper

A Scrapy-based application to scrape medical content from:
- **md.cafe** - Medical information portal
- **MSD Manuals Professional** - Professional medical reference

## Project Structure

```
medical_scraper/
├── scrapy.cfg                  # Scrapy configuration
├── run_scraper.py              # Convenience run script
├── requirements.txt            # Python dependencies
├── output/                     # Scraped content output
│   ├── md_cafe/               # Content from md.cafe
│   │   ├── html/              # Raw HTML files
│   │   ├── text/              # Plain text content
│   │   └── json/              # Metadata JSON files
│   └── msdmanuals/            # Content from MSD Manuals
│       ├── html/
│       ├── text/
│       └── json/
└── medical_scraper/
    ├── __init__.py
    ├── items.py               # Item definitions
    ├── middlewares.py         # Custom middlewares
    ├── pipelines.py           # Content saving pipeline
    ├── settings.py            # Scrapy settings
    └── spiders/
        ├── __init__.py
        ├── mdcafe_spider.py           # Standard spider for md.cafe
        ├── mdcafe_playwright_spider.py # Playwright spider for md.cafe
        ├── msdmanuals_spider.py        # Standard spider for MSD Manuals
        ├── msdmanuals_playwright_spider.py # Playwright spider for MSD Manuals
        └── test_spider.py              # Test spider for verification
```

## Installation

```bash
cd medical_scraper

# Install basic dependencies
pip install -r requirements.txt

# For JavaScript-heavy sites, also install Playwright
pip install scrapy-playwright
playwright install chromium
```

## Quick Start

```bash
cd medical_scraper

# Test the pipeline works (generates sample data)
python run_scraper.py --test

# Scrape md.cafe
python run_scraper.py --site mdcafe

# Scrape MSD Manuals Professional
python run_scraper.py --site msdmanuals

# Scrape both sites
python run_scraper.py --site all

# Use Playwright for JavaScript rendering
python run_scraper.py --site mdcafe --playwright

# Verbose mode
python run_scraper.py --site msdmanuals --verbose
```

## Available Spiders

| Spider | Command | Description |
|--------|---------|-------------|
| `test` | `scrapy crawl test` | Test spider - generates sample items to verify pipeline |
| `mdcafe` | `scrapy crawl mdcafe` | Standard spider for md.cafe |
| `mdcafe_pw` | `scrapy crawl mdcafe_pw` | Playwright spider for md.cafe (JS support) |
| `msdmanuals` | `scrapy crawl msdmanuals` | Standard spider for MSD Manuals |
| `msdmanuals_pw` | `scrapy crawl msdmanuals_pw` | Playwright spider for MSD Manuals (JS support) |

## Configuration

Key settings in `settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `DOWNLOAD_DELAY` | 2-4 | Seconds between requests |
| `CONCURRENT_REQUESTS` | 4 | Maximum concurrent requests |
| `ROBOTSTXT_OBEY` | True | Respect robots.txt |
| `DEPTH_LIMIT` | 5 | Maximum crawl depth |
| `AUTOTHROTTLE_ENABLED` | True | Auto-adjust request rate |
| `HTTPCACHE_ENABLED` | True | Cache responses (24h) |

## Output

Each scraped page generates three files in separate folders:

### Directory Structure
```
output/
├── md_cafe/
│   ├── html/       # Raw HTML content
│   ├── text/       # Cleaned plain text with metadata header
│   └── json/       # Structured metadata
└── msdmanuals/
    ├── html/
    ├── text/
    └── json/
```

### Text File Format
```
Title: Heart Failure - Diagnosis and Treatment
================================================================================
Source URL: https://md.cafe/cardiology/heart-failure
Category: Cardiology
Subcategory: Heart Conditions
Path: Cardiology > Heart Conditions > Heart Failure
Last Updated: 2024-01-15

--------------------------------------------------------------------------------

Heart failure is a chronic condition where the heart doesn't pump blood...
```

### JSON Metadata
```json
{
  "url": "https://md.cafe/cardiology/heart-failure",
  "title": "Heart Failure - Diagnosis and Treatment",
  "source": "md_cafe",
  "category": "Cardiology",
  "subcategory": "Heart Conditions",
  "breadcrumbs": ["Cardiology", "Heart Conditions", "Heart Failure"],
  "last_updated": "2024-01-15",
  "scraped_at": "2024-01-20T10:30:00Z",
  "filename": "Heart-Failure-Diagnosis-and-Treatment_84664295"
}
```

## Features

- **User-Agent Rotation**: Rotates through 9 realistic browser user agents
- **Auto-Throttling**: Adjusts request rate based on server response time
- **HTTP Caching**: 24-hour cache to avoid redundant requests
- **Retry Logic**: Automatic retries with backoff on failures
- **Robots.txt Compliance**: Respects crawling rules
- **Duplicate Filtering**: Avoids scraping the same URL twice
- **Playwright Support**: Optional JavaScript rendering for dynamic sites
- **Three Output Formats**: HTML, plain text, and JSON metadata

## Troubleshooting

### 403 Forbidden Errors

If sites block requests:

1. **Use Playwright spiders** for better browser emulation:
   ```bash
   python run_scraper.py --site mdcafe --playwright
   ```

2. **Increase delays** in `settings.py`:
   ```python
   DOWNLOAD_DELAY = 5
   CONCURRENT_REQUESTS = 1
   ```

3. **Check robots.txt** - the site may explicitly forbid scraping

### Proxy/Network Issues

If you're behind a corporate proxy that blocks certain sites:
- Run the scraper from a network without restrictions
- Use a VPN if permitted
- The test spider (`--test`) works without network access

### No Content Extracted

- Check spider logs for redirect/login page detection
- Verify the site structure hasn't changed
- Try Playwright spiders for JavaScript-rendered content

## Ethical Usage

This scraper is configured responsibly:
- Obeys robots.txt directives
- Uses 2-4 second delays between requests
- Auto-throttles based on server load
- Identifies with realistic user agents

**Always ensure you have permission to scrape target websites and comply with their Terms of Service.**

## License

See repository LICENSE file.
