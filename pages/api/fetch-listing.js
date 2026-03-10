// pages/api/fetch-listing.js
// Fetches an Idealista listing page via ScraperAPI (handles anti-bot protection)

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { url } = req.body;
  if (!url || !url.includes('idealista.com')) {
    return res.status(400).json({ error: 'Invalid URL — must be an Idealista listing' });
  }

  const SCRAPER_API_KEY = process.env.SCRAPER_API_KEY;
  if (!SCRAPER_API_KEY) return res.status(500).json({ error: 'ScraperAPI key not configured' });

  try {
    const scraperUrl = `http://api.scraperapi.com?api_key=${SCRAPER_API_KEY}&url=${encodeURIComponent(url)}&country_code=es&render=false`;

    const response = await fetch(scraperUrl, {
      signal: AbortSignal.timeout(25000), // 25s timeout
    });

    if (!response.ok) {
      return res.status(502).json({ error: `ScraperAPI error: ${response.status}` });
    }

    const html = await response.text();

    if (html.length < 500) {
      return res.status(502).json({ error: 'Empty response from Idealista' });
    }

    // Extract just the relevant text content to save tokens
    // Remove scripts, styles, nav, footer
    const cleaned = html
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<nav[\s\S]*?<\/nav>/gi, '')
      .replace(/<footer[\s\S]*?<\/footer>/gi, '')
      .replace(/<header[\s\S]*?<\/header>/gi, '')
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 8000); // Cap at 8000 chars — plenty for Claude

    return res.status(200).json({ content: cleaned, url });
  } catch (err) {
    if (err.name === 'TimeoutError') {
      return res.status(504).json({ error: 'Timeout — Idealista took too long to respond' });
    }
    return res.status(500).json({ error: err.message });
  }
}
