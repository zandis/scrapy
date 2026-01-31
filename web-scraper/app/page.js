'use client';

import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(50);
  const [status, setStatus] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  const handleScrape = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setStatus('Starting scrape...');
    setResults(null);
    setProgress({ current: 0, total: 0 });

    try {
      const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, depth, maxPages }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Scraping failed');
      }

      const data = await response.json();
      setResults(data);
      setStatus(`Scraped ${data.pages.length} pages successfully!`);
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!results) return;

    setStatus('Preparing download...');

    try {
      const response = await fetch('/api/scrape/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pages: results.pages }),
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${results.domain}-scraped.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      setStatus('Download complete!');
    } catch (error) {
      setStatus(`Download error: ${error.message}`);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ color: '#333', marginBottom: '10px' }}>Web Scraper</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        Enter a website URL to scrape all its content
      </p>

      <form onSubmit={handleScrape} style={{
        background: 'white',
        padding: '30px',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
            Website URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '6px',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
              Crawl Depth
            </label>
            <select
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #ddd',
                borderRadius: '6px'
              }}
            >
              <option value={1}>1 level</option>
              <option value={2}>2 levels</option>
              <option value={3}>3 levels</option>
            </select>
          </div>

          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
              Max Pages
            </label>
            <select
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #ddd',
                borderRadius: '6px'
              }}
            >
              <option value={10}>10 pages</option>
              <option value={25}>25 pages</option>
              <option value={50}>50 pages</option>
              <option value={100}>100 pages</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            fontSize: '16px',
            fontWeight: '600',
            color: 'white',
            backgroundColor: loading ? '#999' : '#0070f3',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Scraping...' : 'Start Scraping'}
        </button>
      </form>

      {status && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          background: status.includes('Error') ? '#fee' : '#e8f5e9',
          borderRadius: '6px',
          color: status.includes('Error') ? '#c00' : '#2e7d32'
        }}>
          {status}
        </div>
      )}

      {results && results.pages.length > 0 && (
        <div style={{
          marginTop: '20px',
          background: 'white',
          padding: '20px',
          borderRadius: '10px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0 }}>Scraped Pages ({results.pages.length})</h3>
            <button
              onClick={handleDownload}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'white',
                backgroundColor: '#28a745',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              Download ZIP
            </button>
          </div>

          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {results.pages.map((page, i) => (
              <div key={i} style={{
                padding: '10px',
                borderBottom: '1px solid #eee',
                fontSize: '14px'
              }}>
                <strong>{page.title || 'Untitled'}</strong>
                <div style={{ color: '#666', fontSize: '12px' }}>{page.url}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
