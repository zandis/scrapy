import * as cheerio from 'cheerio';

export const maxDuration = 60; // Vercel Pro timeout

export async function POST(request) {
  try {
    const { url, depth = 2, maxPages = 50 } = await request.json();

    if (!url) {
      return Response.json({ error: 'URL is required' }, { status: 400 });
    }

    const baseUrl = new URL(url);
    const domain = baseUrl.hostname;
    const visited = new Set();
    const pages = [];
    const queue = [{ url: url, depth: 0 }];

    while (queue.length > 0 && pages.length < maxPages) {
      const { url: currentUrl, depth: currentDepth } = queue.shift();

      if (visited.has(currentUrl)) continue;
      if (currentDepth > depth) continue;

      visited.add(currentUrl);

      try {
        const pageData = await scrapePage(currentUrl, domain);
        if (pageData) {
          pages.push(pageData);

          // Add links to queue if not at max depth
          if (currentDepth < depth) {
            for (const link of pageData.links || []) {
              if (!visited.has(link) && pages.length + queue.length < maxPages) {
                queue.push({ url: link, depth: currentDepth + 1 });
              }
            }
          }
        }
      } catch (error) {
        console.error(`Error scraping ${currentUrl}:`, error.message);
      }
    }

    return Response.json({
      domain,
      pages: pages.map(p => ({
        url: p.url,
        title: p.title,
        content: p.content,
        html: p.html,
      })),
      totalPages: pages.length,
    });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

async function scrapePage(url, domain) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });

    clearTimeout(timeout);

    if (!response.ok) return null;

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('text/html')) return null;

    const html = await response.text();
    const $ = cheerio.load(html);

    // Remove unwanted elements
    $('script, style, nav, footer, header, aside, .sidebar, .menu, .nav, .advertisement, .ad').remove();

    // Extract title
    const title = $('title').text().trim() ||
                  $('h1').first().text().trim() ||
                  'Untitled';

    // Extract main content
    const mainContent = $('main, article, .content, .post, .entry, #content, #main')
      .first()
      .text()
      .trim();

    const bodyContent = $('body').text().trim();
    const content = mainContent || bodyContent;

    // Clean content
    const cleanContent = content
      .replace(/\s+/g, ' ')
      .replace(/\n\s*\n/g, '\n')
      .trim();

    // Extract links on same domain
    const links = [];
    $('a[href]').each((_, el) => {
      try {
        const href = $(el).attr('href');
        if (!href) return;

        const absoluteUrl = new URL(href, url).href;
        const linkDomain = new URL(absoluteUrl).hostname;

        if (linkDomain === domain && !absoluteUrl.includes('#')) {
          // Skip non-HTML resources
          const path = new URL(absoluteUrl).pathname.toLowerCase();
          const skipExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.zip', '.mp4', '.mp3'];
          if (!skipExtensions.some(ext => path.endsWith(ext))) {
            links.push(absoluteUrl.split('?')[0]); // Remove query params
          }
        }
      } catch {}
    });

    // Get clean HTML of main content
    const mainHtml = $('main, article, .content, #content').first().html() ||
                     $('body').html();

    return {
      url,
      title,
      content: cleanContent.substring(0, 50000), // Limit content size
      html: mainHtml?.substring(0, 100000),
      links: [...new Set(links)],
    };
  } catch (error) {
    clearTimeout(timeout);
    throw error;
  }
}
