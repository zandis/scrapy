# Medical Content Scraper

A Scrapy-based application to scrape medical content from:
- **md.cafe** - Medical information portal
- **MSD Manuals Professional** - Professional medical reference

## Project Structure

```
medical_scraper/
├── scrapy.cfg                 # Scrapy configuration
├── output/                    # Scraped content output
│   ├── md_cafe/              # Content from md.cafe
│   │   ├── html/             # Raw HTML files
│   │   ├── text/             # Plain text content
│   │   └── json/             # Metadata JSON files
│   └── msdmanuals/           # Content from MSD Manuals
│       ├── html/
│       ├── text/
│       └── json/
└── medical_scraper/
    ├── __init__.py
    ├── items.py              # Item definitions
    ├── middlewares.py        # Custom middlewares (User-Agent rotation, retry)
    ├── pipelines.py          # Content saving pipeline
    ├── settings.py           # Scrapy settings
    └── spiders/
        ├── __init__.py
        ├── mdcafe_spider.py      # Spider for md.cafe
        └── msdmanuals_spider.py  # Spider for MSD Manuals Professional
```

## Installation

```bash
# From the repository root
pip install -e .

# Or install dependencies directly
pip install scrapy
```

## Usage

### Run Individual Spiders

```bash
cd medical_scraper

# Scrape md.cafe
scrapy crawl mdcafe

# Scrape MSD Manuals Professional
scrapy crawl msdmanuals
```

### Run with Output Logging

```bash
# With verbose output
scrapy crawl mdcafe -L DEBUG

# Save logs to file
scrapy crawl msdmanuals --logfile=scrape.log
```

### Export to Additional Formats

```bash
# Export items to JSON Lines
scrapy crawl mdcafe -o items.jsonl

# Export to CSV
scrapy crawl msdmanuals -o items.csv
```

## Configuration

Key settings in `settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `DOWNLOAD_DELAY` | 2 | Seconds between requests |
| `CONCURRENT_REQUESTS` | 4 | Maximum concurrent requests |
| `ROBOTSTXT_OBEY` | True | Respect robots.txt |
| `DEPTH_LIMIT` | 5 | Maximum crawl depth |
| `AUTOTHROTTLE_ENABLED` | True | Auto-adjust request rate |

## Output

Each scraped page generates three files:

1. **HTML** (`output/<source>/html/<filename>.html`): Raw HTML content
2. **Text** (`output/<source>/text/<filename>.txt`): Cleaned plain text with metadata
3. **JSON** (`output/<source>/json/<filename>.json`): Structured metadata

### JSON Metadata Structure

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "source": "md_cafe",
  "category": "Category Name",
  "subcategory": "Subcategory",
  "breadcrumbs": ["Category", "Subcategory", "Topic"],
  "last_updated": "2024-01-15",
  "scraped_at": "2024-01-20T10:30:00Z",
  "filename": "page-title_12345678"
}
```

## Features

- **User-Agent Rotation**: Rotates through realistic browser user agents
- **Auto-Throttling**: Automatically adjusts request rate based on server response
- **HTTP Caching**: Caches responses to avoid redundant requests
- **Retry Logic**: Retries failed requests with exponential backoff
- **Robots.txt Compliance**: Respects website crawling rules
- **Duplicate Filtering**: Avoids scraping the same URL twice

## Ethical Considerations

This scraper is configured to be respectful:
- Obeys robots.txt directives
- Uses reasonable delays between requests
- Identifies itself with a realistic user agent
- Auto-throttles based on server load

Always ensure you have permission to scrape target websites and comply with their Terms of Service.

## Troubleshooting

### 403 Forbidden Errors

The sites may block automated requests. Try:
- Increasing `DOWNLOAD_DELAY`
- Reducing `CONCURRENT_REQUESTS`
- Adding more delay between requests

### No Content Extracted

Check the spider logs for:
- Redirects to login pages
- JavaScript-rendered content (may need Splash/Playwright)
- Changed page structure (update CSS selectors)

## License

See repository LICENSE file.
