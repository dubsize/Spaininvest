export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { content, lang } = req.body;
  if (!content || content.length < 50) return res.status(400).json({ error: 'Content too short' });

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
  "points_positifs": ["list", "of", "strengths"],
  "points_negatifs": ["list", "of", "weaknesses"],
  "verdict": "short summary in ${langName} on the rental investment interest",
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
- note_globale 1-3: Gross yield < 3.5% or major structural risk (regulation, renovation)`;

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
        max_tokens: 1200,
        system: systemPrompt,
        messages: [{ role: 'user', content }],
      }),
    });

    const data = await response.json();
    if (!response.ok) return res.status(500).json({ error: 'Claude API error', detail: data });

    const raw = data.content?.[0]?.text || '';
    const parsed = JSON.parse(raw.replace(/```json|```/g, '').trim());
    return res.status(200).json(parsed);
  } catch (err) {
    return res.status(500).json({ error: 'Analysis failed', detail: err.message });
  }
}
