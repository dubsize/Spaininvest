// pages/api/fetch-listing.js
// Fetches an Idealista listing page via Scrape.do (fast, handles anti-bot)

export const config = {
  maxDuration: 10,
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { url } = req.body;
  if (!url || !url.includes('idealista.com')) {
    return res.status(400).json({ error: 'Invalid URL' });
  }

  const TOKEN = process.env.SCRAPE_DO_TOKEN;
  if (!TOKEN) return res.status(500).json({ error: 'Scrape.do token not configured' });

  try {
    const scraperUrl = `https://api.scrape.do?token=${TOKEN}&url=${encodeURIComponent(url)}&geoCode=es&render=false`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8500);

    const response = await fetch(scraperUrl, { signal: controller.signal });
    clearTimeout(timeout);

    if (!response.ok) throw new Error(`Scrape.do ${response.status}`);

    const html = await response.text();

    if (html.length < 500 || html.includes('datadome') || html.includes('captcha-delivery')) {
      return res.status(502).json({ error: 'Blocked by Idealista' });
    }

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
      .slice(0, 8000);

    return res.status(200).json({ content: cleaned, url });
  } catch (err) {
    if (err.name === 'AbortError') {
      return res.status(504).json({ error: 'Timeout' });
    }
    return res.status(500).json({ error: err.message });
  }
}
