// pages/api/market-data.js
// Fetches live macro data from Banco de España + INE APIs

// Fallback data (last known values March 2026)
const FALLBACK = {
  euribor: { value: 2.45, period: 'Février 2026', trend: 'down' },
  mortgage_rate: { value: 2.81, period: 'Janvier 2026', trend: 'down' },
  ipv: {
    nacional: { change: 8.1, period: 'T4 2025' },
    madrid:    { change: 9.2, period: 'T4 2025' },
    barcelona: { change: 7.8, period: 'T4 2025' },
    valencia:  { change: 11.3, period: 'T4 2025' },
    malaga:    { change: 12.1, period: 'T4 2025' },
  }
};

// BdE series codes
// BE_EURIBOR_12M = Euribor 12 months (mortgage reference)
// IPV = Índice de Precios de Vivienda (INE, quarterly)
const BDE_BASE = 'https://app.bde.es/bierest/resources/srdatosapp/favoritas';
const INE_BASE = 'https://servicios.ine.es/wstempus/js/ES';

async function fetchEuribor() {
  try {
    // BdE series for Euribor 12 months
    const res = await fetch(
      `${BDE_BASE}?idioma=es&series=BE_EURIBOR_12M`,
      { signal: AbortSignal.timeout(5000) }
    );
    if (!res.ok) return null;
    const data = await res.json();
    const serie = data?.[0];
    if (!serie?.dato) return null;
    return {
      value: parseFloat(serie.dato).toFixed(2),
      period: serie.fecha || '',
      trend: serie.tendencia === 'B' ? 'down' : serie.tendencia === 'A' ? 'up' : 'stable',
    };
  } catch { return null; }
}

async function fetchMortgageRate() {
  try {
    // INE: Tipo de interés medio hipotecas sobre viviendas (table 24460)
    const res = await fetch(
      `${INE_BASE}/DATOS_TABLA/24460?nult=1`,
      { signal: AbortSignal.timeout(5000) }
    );
    if (!res.ok) return null;
    const data = await res.json();
    if (!Array.isArray(data) || !data[0]?.Data?.[0]) return null;
    const d = data[0].Data[0];
    return {
      value: parseFloat(d.Valor).toFixed(2),
      period: `${d.T3_Periodo || ''} ${d.Anyo || ''}`.trim(),
      trend: 'stable',
    };
  } catch { return null; }
}

async function fetchIPV() {
  try {
    // INE IPV table 25171 = Índice de Precios de Vivienda by CCAA
    const res = await fetch(
      `${INE_BASE}/DATOS_TABLA/25171?nult=1`,
      { signal: AbortSignal.timeout(5000) }
    );
    if (!res.ok) return null;
    const data = await res.json();
    if (!Array.isArray(data)) return null;

    const result = { ...FALLBACK.ipv };
    const cityMap = {
      'Nacional': 'nacional',
      'Madrid': 'madrid',
      'Barcelona': 'barcelona',
      'Valencia': 'valencia',
      'Málaga': 'malaga',
      'Malaga': 'malaga',
    };

    for (const serie of data) {
      const name = serie.Nombre || '';
      const val = serie.Data?.[0]?.Valor;
      const period = `${serie.Data?.[0]?.T3_Periodo || ''} ${serie.Data?.[0]?.Anyo || ''}`.trim();
      if (!val) continue;
      for (const [keyword, key] of Object.entries(cityMap)) {
        if (name.includes(keyword)) {
          result[key] = { change: parseFloat(val).toFixed(1), period };
        }
      }
    }
    return result;
  } catch { return null; }
}

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).end();

  const [euriborRaw, mortgageRaw, ipvRaw] = await Promise.all([
    fetchEuribor(),
    fetchMortgageRate(),
    fetchIPV(),
  ]);

  const payload = {
    euribor: euriborRaw || FALLBACK.euribor,
    mortgage_rate: mortgageRaw || FALLBACK.mortgage_rate,
    ipv: ipvRaw || FALLBACK.ipv,
    fetched_at: new Date().toISOString(),
    live: !!(euriborRaw || mortgageRaw || ipvRaw),
  };

  // Cache 6h (data updates monthly/quarterly)
  res.setHeader('Cache-Control', 's-maxage=21600, stale-while-revalidate');
  return res.status(200).json(payload);
}
