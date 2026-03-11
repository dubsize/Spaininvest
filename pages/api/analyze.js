import { createClient } from '@supabase/supabase-js';
import { getRentData, RENT_MODIFIERS } from '../../lib/rentPrices';

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

// Build dynamic rent block for the prompt
function buildRentBlock(city, neighbourhood) {
  const rent = getRentData(city, neighbourhood);
  if (!rent) {
    return `\n=== RENT REFERENCE DATA ===\nCity/neighbourhood not in database. Use your general knowledge of Spanish rental market and apply conservative estimates.\n${RENT_MODIFIERS}`;
  }
  if (rent.found) {
    return `\n=== RENT REFERENCE DATA (${rent.district}) ===\nBase range: ${rent.min}–${rent.max} €/m²/month (unfurnished long-term)\nDistrict profile: ${rent.profile}\nCity context: ${rent.cityNote}\n${RENT_MODIFIERS}`;
  }
  return `\n=== RENT REFERENCE DATA (city average — district not found) ===\nCity average: ${rent.min}–${rent.max} €/m²/month\nCity context: ${rent.cityNote}\nNote: Exact district not found in database — use city average as base.\n${RENT_MODIFIERS}`;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { content, images, lang, email } = req.body;
  if (!email) return res.status(401).json({ error: 'email_required' });
  if (!content && (!images || images.length === 0)) return res.status(400).json({ error: 'No content or image provided' });
  if (content && content.length < 50 && (!images || images.length === 0)) return res.status(400).json({ error: 'Content too short' });

  const normalizedEmail = email.toLowerCase().trim();
  const ip = getIP(req);

  // ── Whitelisted IPs (unlimited access) ───────────────
  const WHITELISTED_IPS = ['2.138.252.170'];
  const isWhitelisted = WHITELISTED_IPS.includes(ip);

  // ── Check email quota ─────────────────────────────────
  const { data: user, error: userError } = await supabase
    .from('users')
    .select('analyses_count, is_subscribed')
    .eq('email', normalizedEmail)
    .single();

  if (userError || !user) return res.status(401).json({ error: 'email_required' });

  if (!user.is_subscribed && !isWhitelisted) {
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

  // ── Pre-detect city/neighbourhood from content for dynamic rent data ──
  const contentLower = (content || '').toLowerCase();
  const detectedCity =
    contentLower.includes('madrid') ? 'madrid' :
    contentLower.includes('barcelona') ? 'barcelona' :
    contentLower.includes('valencia') ? 'valencia' :
    contentLower.includes('malaga') || contentLower.includes('málaga') ? 'malaga' : null;

  // Try to extract neighbourhood from content (common patterns in Idealista listings)
  let detectedNeighbourhood = null;
  if (detectedCity) {
    const neighPatterns = [
      /(?:barrio|distrito|zona|neighbourhood|quartier|neighborhood)[:\s]+([a-záéíóúüñ\s-]{3,30})/i,
      /([a-záéíóúüñ\s-]{3,25}),\s*(?:madrid|barcelona|valencia|málaga|malaga)/i,
    ];
    for (const pattern of neighPatterns) {
      const m = (content || '').match(pattern);
      if (m) { detectedNeighbourhood = m[1].trim(); break; }
    }
  }

  const rentBlock = buildRentBlock(detectedCity, detectedNeighbourhood);

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
  "note_globale": number (1-10),
  "renta_district_persona": number or null (net annual income per person in €, from ADRH data above),
  "renta_district_hogar": number or null (net annual household income in €, from ADRH data above),
  "paro_region": number or null (unemployment % for the region from EPA data above),
  "district_profile": string or null (1-sentence tenant profile summary in ${langName}, e.g. "Quartier ouvrier avec forte demande locative jeune, revenu médian 28.500€/foyer")
}

SCORING GUIDANCE:
- note_globale 8-10: Gross yield > 6%, good neighborhood, no major risks
- note_globale 6-7: Gross yield 4.5-6%, decent location, manageable risks
- note_globale 4-5: Gross yield 3.5-4.5%, some concerns
- note_globale 1-3: Gross yield < 3.5% or major structural risk (regulation, renovation)
${rentBlock}

=== SOCIO-DEMOGRAPHIC DATA BY DISTRICT — INE ADRH 2023 + EPA T4 2025 ===
Use this data to enrich your analysis based on the property location. Match the neighborhood/district from the listing to the closest entry below.
Format: Renta neta media/persona (€/yr) | Renta neta media/hogar (€/yr) | % pop >65 | % pop <18 | Profile

UNEMPLOYMENT CONTEXT (EPA T4 2025):
- Comunidad de Madrid: 9.2% — well below national avg → lower tenant default risk
- Cataluña: 9.8% — below national avg
- Comunitat Valenciana: 11.4% — near national avg
- Andalucía: 15.2% — above national avg → factor into default risk for Málaga investments
- Spain national avg: 10.6%

MADRID (city avg: 18,142€/persona/yr):
- Salamanca: 30,200€ | 68,000€/hogar | 24%>65 | 12%<18 → Premium upper class, low yield zone
- Chamartín: 29,800€ | 64,000€/hogar | 25%>65 | 11%<18 → Affluent, embassies, professionals
- Chamberí: 25,400€ | 53,000€/hogar | 26%>65 | 12%<18 → Central premium, aging pop, high demand
- Moncloa-Aravaca: 24,100€ | 52,000€/hogar | 20%>65 | 16%<18 → University zone (Complutense), student demand
- Retiro: 23,800€ | 51,000€/hogar | 25%>65 | 13%<18 → Park premium, mature professional tenants
- Hortaleza: 19,800€ | 46,000€/hogar | 15%>65 | 19%<18 → Modern residential, Sanchinarro/Las Tablas, families
- Fuencarral-El Pardo: 19,200€ | 44,000€/hogar | 16%>65 | 18%<18 → Growing north suburbs, family profile
- Barajas: 18,600€ | 43,000€/hogar | 15%>65 | 19%<18 → Airport zone, logistics/aviation workers
- Arganzuela: 17,800€ | 40,000€/hogar | 17%>65 | 16%<18 → Gentrifying, Madrid Río effect, mixed profile
- Ciudad Lineal: 16,800€ | 38,000€/hogar | 20%>65 | 16%<18 → Middle class, solid rental demand, good yield
- San Blas-Canillejas: 15,900€ | 37,000€/hogar | 18%>65 | 17%<18 → Eastern working class, growing, young pop
- Moratalaz: 15,800€ | 37,000€/hogar | 24%>65 | 14%<18 → Quiet residential, older pop, lower young tenant demand
- Tetuán: 15,200€ | 35,000€/hogar | 16%>65 | 18%<18 → Gentrifying, multicultural, rising fast
- Vicálvaro: 14,800€ | 34,000€/hogar | 14%>65 | 20%<18 → Suburban families, newer housing stock
- Villa de Vallecas: 14,200€ | 33,000€/hogar | 13%>65 | 22%<18 → Young families, new developments, affordable
- Latina: 14,100€ | 33,000€/hogar | 20%>65 | 17%<18 → Working class, good yield, immigrant community
- Carabanchel: 13,600€ | 31,000€/hogar | 17%>65 | 19%<18 → High yield, gentrifying south, family demand
- Usera: 12,400€ | 28,000€/hogar | 15%>65 | 20%<18 → Multicultural (Asian/Latin), highest yield zone Madrid
- Vallecas/Puente de Vallecas: 11,800-12,100€ | 27,000-28,500€/hogar | 16%>65 | 20-21%<18 → 8%+ gross yield, affordable, working class, young population
- Villaverde: 11,200€ | 26,000€/hogar | 16%>65 | 21%<18 → Industrial/residential, high yield, lower demand profile

BARCELONA (city avg: 18,500€/persona/yr):
NOTE: Rent control (Ley de Contenció) applies in most of Barcelona — always flag as risk
- Sarrià-Sant Gervasi: 28,400€ | 62,000€/hogar | 22%>65 | 15%<18 → Affluent hillside, expats, families, low yield
- Les Corts: 22,800€ | 51,000€/hogar | 23%>65 | 14%<18 → Affluent, Camp Nou area, professionals
- Eixample: 21,200€ | 46,000€/hogar | 20%>65 | 13%<18 → Prime central, maximum demand, rent control risk
- Gràcia: 20,100€ | 43,000€/hogar | 19%>65 | 14%<18 → Trendy, young professionals, rent pressure
- Sant Martí (Poblenou): 17,600€ | 38,000€/hogar | 17%>65 | 15%<18 → Tech hub, rising fast, good yield window closing
- Sants-Montjuïc: 16,400€ | 36,000€/hogar | 18%>65 | 16%<18 → Mixed working class + university, solid rental base
- Horta-Guinardó: 16,200€ | 36,500€/hogar | 21%>65 | 15%<18 → Residential families, decent yield, quieter
- Sant Andreu: 16,800€ | 37,000€/hogar | 18%>65 | 17%<18 → Gentrifying, good yield, improving transport
- Nou Barris: 13,200€ | 29,000€/hogar | 19%>65 | 18%<18 → Highest yield in BCN, working class, immigrant community
- Ciutat Vella: 13,800€ | 28,000€/hogar | 13%>65 | 14%<18 → Airbnb/tourist pressure, rent control, avoid long-term

VALENCIA (city avg: 14,800€/persona/yr):
- Pla del Real: 22,400€ | 49,000€/hogar | 22%>65 | 14%<18 → Affluent university zone, reliable professional/student demand
- Eixample Valencia: 20,100€ | 44,000€/hogar | 23%>65 | 12%<18 → Central premium, solid demand, lower yield
- Extramurs: 17,200€ | 37,000€/hogar | 19%>65 | 15%<18 → Gentrifying central, good profile, rising
- Russafa: 16,800€ | 35,000€/hogar | 16%>65 | 15%<18 → Trendy, expats, young professionals, high demand
- Algirós: 16,400€ | 36,000€/hogar | 19%>65 | 16%<18 → University area, reliable student demand, good yield
- Campanar: 15,800€ | 34,000€/hogar | 18%>65 | 17%<18 → Residential families, good value
- Poblats Marítims: 14,800€ | 32,000€/hogar | 17%>65 | 17%<18 → Coastal proximity, rising expat demand
- Benimaclet: 14,600€ | 31,000€/hogar | 17%>65 | 17%<18 → Student/young professional mix, excellent yield
- El Carmen/Ciutat Vella: 14,200€ | 29,000€/hogar | 15%>65 | 14%<18 → Historic core, tourism pressure
- Quatre Carreres: 14,100€ | 31,000€/hogar | 16%>65 | 18%<18 → Affordable families, solid value
- Jesús: 13,400€ | 29,500€/hogar | 19%>65 | 18%<18 → Working class, solid yield, quieter
- Patraix: 13,800€ | 30,000€/hogar | 18%>65 | 18%<18 → Affordable, family profile, reliable
- Rascanya: 13,200€ | 29,000€/hogar | 16%>65 | 20%<18 → Affordable, high yield, young families, immigrant community

MÁLAGA (city avg: 12,900€/persona/yr — BELOW national avg 15,036€):
NOTE: 15.2% unemployment in Andalucía → higher tenant default risk than Madrid/Barcelona
- Centro/Soho: 14,200€ | 30,000€/hogar | 20%>65 | 14%<18 → Expat & tourist demand, rising fast, Soho gentrification
- Este: 13,800€ | 29,000€/hogar | 17%>65 | 17%<18 → Residential east, families, solid demand
- Ciudad Jardín: 13,200€ | 28,000€/hogar | 18%>65 | 17%<18 → Middle class residential, stable profile
- Teatinos-Universidad: 13,600€ | 28,000€/hogar | 11%>65 | 19%<18 → University + tech park (PTA), student & professional demand, excellent yield potential
- Puerto de la Torre: 12,400€ | 27,000€/hogar | 15%>65 | 20%<18 → Residential north, families
- Churriana: 12,200€ | 27,000€/hogar | 14%>65 | 20%<18 → Near airport, good yield, family profile
- Carretera de Cádiz: 11,800€ | 26,000€/hogar | 17%>65 | 19%<18 → Working class west, high yield, lower income profile
- Campanillas: 11,600€ | 26,000€/hogar | 13%>65 | 22%<18 → Industrial suburb, logistics workers, high yield
- Palma-Palmilla: 9,800€ | 22,000€/hogar | 17%>65 | 22%<18 → Lowest income in Málaga, highest yield but elevated social risk

HOW TO USE IN YOUR ANALYSIS:
1. Match property location to nearest district using fuzzy logic — ignore accents, case, hyphens (e.g. "tetuan-madrid" = Tetuán, "fuencarral-el-pardo" = Fuencarral-El Pardo, "chamberi" = Chamberí)
2. Include income/demographic context in justification_loyer
3. In points_positifs/negatifs: flag relevant demographics (young pop = strong rental demand; high >65% = lower mobility)
4. In verdict: include one line on district socio-economic profile (e.g. "District household income 31,000€/yr, working-class profile with strong young tenant demand")
5. Adjust score_quartier: districts above city avg income = +1, below = -1; high young pop (>18% <18y) = +1 for rental demand
6. For Málaga: always factor 15.2% regional unemployment into risk assessment

CRITICAL — STRICT ANTI-HALLUCINATION RULE FOR SOCIO DATA:
- ONLY populate renta_district_persona, renta_district_hogar, paro_region if you can confidently match the property location to one of the districts listed above.
- If the location is ambiguous, unknown, or outside the 53 listed districts (small town, suburb, other city): set renta_district_persona=null, renta_district_hogar=null, and set district_profile to a city-level fallback string like "Données socio-démo précises non disponibles pour ce secteur — moyennes régionales appliquées" (in the response language).
- NEVER invent or estimate income/unemployment figures. Use ONLY the exact values from the table above, or null.
- paro_region should always be set when the city is Madrid/Barcelona/Valencia/Málaga (use regional rate), null for other cities.
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
