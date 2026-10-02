// pages/api/ine.js
// Fetches live data from INE (Instituto Nacional de Estadística):
// - IRAV: Índice de Referencia para la Actualización de Arrendamientos de Vivienda
// - IPVA: Índice de Precios de Vivienda en Alquiler (by province)

// Fallback data (last known values as of March 2026)
const FALLBACK = {
  irav: {
    value: 2.32,
    period: 'Diciembre 2025',
    source: 'INE (fallback)',
  },
  ipva: {
    // Annual rental price evolution by province (% change, latest available)
    'Madrid':    { change: 8.5,  period: '2024' },
    'Barcelona': { change: 7.2,  period: '2024' },
    'Valencia':  { change: 10.1, period: '2024' },
    'Málaga':    { change: 11.3, period: '2024' },
    'España':    { change: 8.1,  period: '2024' },
  },
};

// INE series codes
// IRAV monthly series: https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IRAV?nult=1
// IPVA by province table: 59058
const INE_BASE = 'https://servicios.ine.es/wstempus/js/ES';

async function fetchIRAV() {
  try {
    const res = await fetch(`${INE_BASE}/DATOS_SERIE/IRAV?nult=1`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (!data?.Data?.[0]) return null;
    const latest = data.Data[0];
    return {
      value: latest.Valor,
      period: `${latest.T3_Periodo || ''} ${latest.Anyo || ''}`.trim(),
      source: 'INE live',
    };
  } catch {
    return null;
  }
}

async function fetchIPVA() {
  try {
    // Table 59058 = IPVA provincial indices, nult=1 = last available period
    const res = await fetch(`${INE_BASE}/DATOS_TABLA/59058?nult=1`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) return null;

    const result = {};
    const provinceMap = {
      '28': 'Madrid',
      '08': 'Barcelona',
      '46': 'Valencia',
      '29': 'Málaga',
    };

    for (const serie of data) {
      const name = serie.Nombre || '';
      const value = serie.Data?.[0]?.Valor;
      if (!value) continue;
      const period = `${serie.Data?.[0]?.T3_Periodo || ''} ${serie.Data?.[0]?.Anyo || ''}`.trim();

      for (const [code, city] of Object.entries(provinceMap)) {
        if (name.includes(code) || name.toLowerCase().includes(city.toLowerCase())) {
          result[city] = { change: value, period };
        }
      }
    }

    return Object.keys(result).length > 0 ? result : null;
  } catch {
    return null;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).end();

  // Fetch both in parallel
  const [iravRaw, ipvaRaw] = await Promise.all([fetchIRAV(), fetchIPVA()]);

  const irav = iravRaw || FALLBACK.irav;
  const ipva = ipvaRaw || FALLBACK.ipva;

  // Cache for 24h (INE updates monthly)
  res.setHeader('Cache-Control', 's-maxage=86400, stale-while-revalidate');

  return res.status(200).json({
    irav,
    ipva,
    fetched_at: new Date().toISOString(),
    live: !!(iravRaw || ipvaRaw),
  });
}
