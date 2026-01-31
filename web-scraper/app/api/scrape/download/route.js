import JSZip from 'jszip';

export async function POST(request) {
  try {
    const { pages } = await request.json();

    if (!pages || pages.length === 0) {
      return Response.json({ error: 'No pages to download' }, { status: 400 });
    }

    const zip = new JSZip();

    // Create folders
    const htmlFolder = zip.folder('html');
    const textFolder = zip.folder('text');
    const jsonFolder = zip.folder('json');

    pages.forEach((page, index) => {
      const filename = sanitizeFilename(page.title || `page-${index + 1}`);

      // Save HTML
      if (page.html) {
        const fullHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(page.title)}</title>
  <meta name="source-url" content="${escapeHtml(page.url)}">
</head>
<body>
${page.html}
</body>
</html>`;
        htmlFolder.file(`${filename}.html`, fullHtml);
      }

      // Save text content
      if (page.content) {
        const textContent = `Title: ${page.title}
URL: ${page.url}
${'='.repeat(80)}

${page.content}
`;
        textFolder.file(`${filename}.txt`, textContent);
      }

      // Save JSON metadata
      const jsonData = {
        url: page.url,
        title: page.title,
        contentLength: page.content?.length || 0,
        scrapedAt: new Date().toISOString(),
      };
      jsonFolder.file(`${filename}.json`, JSON.stringify(jsonData, null, 2));
    });

    // Generate index
    const indexContent = `# Scraped Content Index

Total Pages: ${pages.length}
Scraped At: ${new Date().toISOString()}

## Pages

${pages.map((p, i) => `${i + 1}. [${p.title}](${p.url})`).join('\n')}
`;
    zip.file('index.md', indexContent);

    const zipBuffer = await zip.generateAsync({ type: 'arraybuffer' });

    return new Response(zipBuffer, {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="scraped-content.zip"',
      },
    });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
}

function sanitizeFilename(name) {
  return name
    .replace(/[^a-zA-Z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .substring(0, 50)
    .toLowerCase() || 'untitled';
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
