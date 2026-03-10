import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SECRET_KEY
);

function getIP(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) return forwarded.split(',')[0].trim();
  return req.socket?.remoteAddress || 'unknown';
}

// Fetch live INE data (IRAV + IPVA)
async function fetchINEData(baseUrl) {
  try {
    const res = await fetch(`${baseUrl}/api/ine`, {
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// Build INE data block for the prompt
function buildINEBlock(ine) {
  if (!ine) return '';

  let block = `\n=== LIVE INE DATA (fetched ${new Date().toLocaleDateString('es-ES')}) ===\n`;

  // IRAV
  block += `\nIRAV (Índice de Referencia de Arrendamientos de Vivienda):`;
  block += `\n• Current rate: ${ine.irav.value}% (${ine.irav.period})`;
  block += `\n• This is the LEGAL MAXIMUM annual rent increase for contracts signed after May 25, 2023.`;
  block += `\n• Always mention this rate in the verdict when relevant to the investment.`;

  // IPVA
  if (ine.ipva && Object.keys(ine.ipva).length > 0) {
    block += `\n\nIPVA (Índice de Precios de Vivienda en Alquiler) — Annual rental price evolution:`;
    for (const [city, data] of Object.entries(ine.ipva)) {
      block += `\n• ${city}: ${data.change > 0 ? '+' : ''}${data.change}% (${data.period})`;
    }
    block += `\n• Use these official figures to contextualize rent evolution in your analysis.`;
  }

  block += `\n• Source: INE (Instituto Nacional de Estadística) — ${ine.live ? 'live data' : 'fallback values'}`;

  return block;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { content, images, lang, email } = req.body;
  if (!email) return res.status(401).json({ error: 'email_required' });
  if (!content && (!images || images.length === 0)) return res.status(400).json({ error: 'No content or image provided' });
  if (content && content.length < 50 && (!images || images.length === 0)) return res.status(400).json({ error: 'Content too short' });

  const normalizedEmail = email.toLowerCase().trim();
  const ip = getIP(req);

  // ── Check email quota ─────────────────────────────────
  const { data: user, error: userError } = await supabase
    .from('users')
    .select('analyses_count, is_subscribed')
    .eq('email', normalizedEmail)
    .single();

  if (userError || !user) return res.status(401).json({ error: 'email_required' });

  if (!user.is_subscribed) {
    if (user.analyses_count >= 2) return res.status(403).json({ error: 'quota_exceeded' });

    // Check IP quota
    const { data: ipData } = await supabase
      .from('ip_usage')
      .select('analyses_count')
      .eq('ip', ip)
      .single();

    if (ipData && ipData.analyses_count >= 2) return res.status(403).json({ error: 'quota_exceeded' });
  }

  // ── Fetch live INE data ───────────────────────────────
  const host = req.headers.host;
  const protocol = process.env.NODE_ENV === 'production' ? 'https' : 'http';
  const baseUrl = `${protocol}://${host}`;
  const ineData = await fetchINEData(baseUrl);
  const ineBlock = buildINEBlock(ineData);

  // ── Build prompt ──────────────────────────────────────
  const langNames = { en: 'English', fr: 'French', es: 'Spanish' };
  const langName = langNames[lang] || 'French';

  const systemPrompt = `You are an expert in rental property investment in Spain.
The user will give you either raw HTML or copied text from a Spanish real estate listing (Idealista, Fotocasa, etc.).

Extract all relevant information and return ONLY a valid JSON object. No text before or after, no backticks, no markdown. Just raw JSON.

IMPORTANT: All text fields must be written in ${langName}.

Expected JSON structure:
{
  "titre": "short title (e.g. 2bd/2ba · Eixample Barcelona · 75m²)",
  "adresse": "address or neighborhood from listing",
  "quartier": "standardized neighborhood name",
  "ville": "city name (Madrid / Barcelona / Valencia / Málaga / other)",
  "prix": number,
  "surface": number,
  "chambres": number,
  "salles_de_bain": number,
  "annee_construction": number or null,
  "classe_energetique": "A/B/C/D/E/F/G" or null,
  "garage": boolean,
  "trastero": boolean,
  "piscine": boolean,
  "ascenseur": boolean,
  "neuf": boolean,
  "etat": "neuf" | "bon_etat" | "a_renover",
  "loyer_estime_min": number,
  "loyer_estime_max": number,
  "loyer_estime_median": number,
  "justification_loyer": "short explanation in ${langName} of the rent estimate with specific market references for this city and neighborhood",
  "charges_copro_estimees": number,
  "ibi_annuel_estime": number,
  "irav": number,
  "irav_period": "string",
  "ipva_city_change": number or null,
  "points_positifs": ["list", "of", "strengths"],
  "points_negatifs": ["list", "of", "weaknesses"],
  "verdict": "short summary in ${langName} on the rental investment interest — must mention the IRAV rate and what it means for this investment",
  "score_quartier": number (1-10),
  "note_globale": number (1-10)
}

=== SPAIN RENTAL MARKET REFERENCE DATA 2025-2026 (unfurnished long-term) ===

MADRID:
- Vallecas / Villaverde: 10-13 €/m²/mo → high yield, working-class, growing demand
- Carabanchel / Usera / Latina: 12-15 €/m²/mo → strong yield, gentrifying
- Tetuán / Cuatro Caminos / Hortaleza: 14-17 €/m²/mo → good yield, well connected
- Sanchinarro / Las Tablas / Valdebebas: 14-18 €/m²/mo → modern residential, families
- Chamberí / Moncloa / Retiro: 18-24 €/m²/mo → premium central, low yield
- Salamanca / Jerónimos / Centro: 22-30 €/m²/mo → luxury, very low yield

BARCELONA:
- Nou Barris / Sant Andreu / Horta: 13-16 €/m²/mo → best yield in BCN
- Sant Martí / Poblenou / Clot: 16-20 €/m²/mo → good yield, tech hub, growing
- Sants / Les Corts / Sarrià (outer): 17-21 €/m²/mo → solid residential
- Gràcia / Eixample Dret: 20-25 €/m²/mo → high demand, compressed yield
- Eixample Esquerra / Sant Gervasi: 22-27 €/m²/mo → premium, low yield
- Ciutat Vella / Barceloneta: 20-28 €/m²/mo → tourist pressure, regulation risk
NOTE Barcelona: Rent control applies in many areas (Ley de Contenció) — flag this as a risk

VALENCIA:
- Benimaclet / Rascanya / Campanar: 10-13 €/m²/mo → excellent yield, student demand
- Patraix / Jesús / Quatre Carreres: 10-13 €/m²/mo → affordable, solid yield
- Extramurs / Poblats Marítims: 12-15 €/m²/mo → rising, sea proximity
- Russafa / El Carmen / Eixample: 13-17 €/m²/mo → trendy, expat demand
- Pla del Real / Algirós: 14-17 €/m²/mo → university area, reliable tenants
NOTE Valencia: One of best yield/price ratios in Spain right now

MÁLAGA / COSTA DEL SOL:
- Málaga City outskirts (Churriana, Campanillas): 10-13 €/m²/mo → high yield
- Málaga City (Centro, Soho, Lagunillas): 13-17 €/m²/mo → strong demand, expats
- Torremolinos / Benalmádena: 12-15 €/m²/mo → tourist/residential mix
- Marbella (outskirts): 13-16 €/m²/mo → good yield away from Golden Mile
- Marbella (Golden Mile / Puerto Banús): 16-25 €/m²/mo → luxury, low yield
- Estepona / Nerja: 12-15 €/m²/mo → growing, good value
NOTE Málaga: Strong expat demand (UK, French, Dutch). Short-term rental pressure on long-term supply.

UNIVERSAL ADJUSTMENTS:
- Gated community with pool + gym + concierge: +10-15%
- Included garage: +100-150€/mo
- New build (< 5 years): +5-10%
- Poor energy rating (E/F/G): −3-5% (future renovation risk)
- Top floor with terrace: +8-12%
- Ground floor: −5-10%

SCORING GUIDANCE:
- note_globale 8-10: Gross yield > 6%, good neighborhood, no major risks
- note_globale 6-7: Gross yield 4.5-6%, decent location, manageable risks
- note_globale 4-5: Gross yield 3.5-4.5%, some concerns
- note_globale 1-3: Gross yield < 3.5% or major structural risk (regulation, renovation)
${ineBlock}`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1400,
        system: systemPrompt,
        messages: [{ role: 'user', content: (images && images.length > 0) ? [
          ...images.map(img => ({ type: 'image', source: { type: 'base64', media_type: img.mediaType, data: img.base64 } })),
          { type: 'text', text: 'Analyze these Spanish real estate listing screenshots and return the JSON analysis.' }
        ] : content }],
      }),
    });

    const data = await response.json();
    if (!response.ok) return res.status(500).json({ error: 'Claude API error', detail: data });

    const raw = data.content?.[0]?.text || '';
    const parsed = JSON.parse(raw.replace(/```json|```/g, '').trim());

    // Inject INE data if Claude didn't fill it
    if (ineData?.irav && !parsed.irav) {
      parsed.irav = ineData.irav.value;
      parsed.irav_period = ineData.irav.period;
    }
    if (ineData?.ipva && parsed.ville && !parsed.ipva_city_change) {
      parsed.ipva_city_change = ineData.ipva[parsed.ville]?.change || null;
    }

    // ── Increment email count ──────────────────────────
    await supabase
      .from('users')
      .update({ analyses_count: user.analyses_count + 1 })
      .eq('email', normalizedEmail);

    // ── Increment IP count ─────────────────────────────
    const { data: ipData } = await supabase
      .from('ip_usage')
      .select('analyses_count')
      .eq('ip', ip)
      .single();

    if (ipData) {
      await supabase
        .from('ip_usage')
        .update({ analyses_count: ipData.analyses_count + 1, updated_at: new Date().toISOString() })
        .eq('ip', ip);
    } else {
      await supabase.from('ip_usage').insert({ ip, analyses_count: 1 });
    }

    return res.status(200).json(parsed);
  } catch (err) {
    return res.status(500).json({ error: 'Analysis failed', detail: err.message });
  }
}
