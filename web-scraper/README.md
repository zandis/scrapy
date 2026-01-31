# Web Scraper

A simple web scraper with a UI that can be deployed on Vercel. Enter any website URL and download all its content.

## Features

- Clean web interface
- Configurable crawl depth (1-3 levels)
- Configurable max pages (10-100)
- Downloads content as ZIP with:
  - HTML files
  - Plain text files
  - JSON metadata
- Works on Vercel's free tier

## Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/scrapy/tree/main/web-scraper)

Or manually:

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Set the root directory to `web-scraper`
5. Deploy!

## Local Development

```bash
cd web-scraper
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Usage

1. Enter a website URL (e.g., `https://example.com`)
2. Select crawl depth (how many levels of links to follow)
3. Select max pages to scrape
4. Click "Start Scraping"
5. Download the ZIP file with all content

## Output Structure

```
scraped-content.zip
├── index.md          # List of all scraped pages
├── html/             # Raw HTML content
│   ├── page-1.html
│   └── page-2.html
├── text/             # Plain text content
│   ├── page-1.txt
│   └── page-2.txt
└── json/             # Metadata
    ├── page-1.json
    └── page-2.json
```

## Limitations

- Vercel free tier: 10 second timeout per request
- Vercel Pro: 60 second timeout
- Some sites may block automated requests
- JavaScript-rendered content may not be captured

## Tech Stack

- Next.js 14
- Cheerio (HTML parsing)
- JSZip (ZIP generation)
