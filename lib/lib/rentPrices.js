// rentPrices.js — Loyers de référence par quartier (euros/m2/mois)
// Source : Idealista / Fotocasa — mise a jour manuelle trimestrielle
// Derniere mise a jour : Mars 2026

export const RENT_PRICES = {
  madrid: {
    _city_avg: [14, 18],
    _note: "Marche sous forte pression locative. +8.2% sur 12 mois (INE T4 2025).",
    "vallecas":              [10, 13, "Ouvrier, forte demande, jeune population"],
    "puente de vallecas":    [10, 13, "Ouvrier, rendement max Madrid, jeune population"],
    "villa de vallecas":     [11, 14, "Residentiel neuf, familles, bonne demande"],
    "villaverde":            [10, 12, "Industriel/residentiel, rendement eleve"],
    "usera":                 [12, 15, "Multiculturel, tres forte demande, rotation rapide"],
    "carabanchel":           [12, 15, "En gentrification, familles, bon rendement"],
    "latina":                [12, 15, "Ouvrier, bonne demande, communaute immigree"],
    "tetuan":                [14, 17, "En gentrification, multiculturel, montee des prix"],
    "ciudad lineal":         [14, 17, "Classe moyenne, demande stable, bon rendement"],
    "san blas":              [13, 16, "Est ouvrier, jeune population croissante"],
    "san blas-canillejas":   [13, 16, "Est ouvrier, jeune population croissante"],
    "arganzuela":            [16, 20, "En hausse (Madrid Rio), mixte, bonne demande"],
    "moratalaz":             [13, 16, "Residentiel calme, pop agee, demande moderee"],
    "vicalvaro":             [13, 16, "Banlieue familiale, logements neufs"],
    "hortaleza":             [14, 18, "Moderne, familles, Sanchinarro/Las Tablas"],
    "sanchinarro":           [14, 18, "Moderne residentiel, familles, services"],
    "las tablas":            [14, 17, "Residentiel neuf, familles, bien connecte"],
    "valdebebas":            [14, 17, "Nouveau quartier, familles, bonne qualite"],
    "fuencarral":            [16, 20, "Nord residentiel, familles, croissance"],
    "fuencarral-el pardo":   [16, 20, "Nord residentiel, familles, croissance"],
    "barajas":               [14, 17, "Zone aeroport, travailleurs logistique/aviation"],
    "moncloa":               [18, 24, "Premium central, universitaire, forte demande"],
    "moncloa-aravaca":       [18, 24, "Premium, Complutense, etudiants/professionnels"],
    "chamberi":              [18, 24, "Premium central, forte demande, faible rendement"],
    "retiro":                [19, 25, "Premium residentiel, parc, locataires CSP+"],
    "salamanca":             [22, 30, "Luxe, executifs/expatries, rendement tres faible"],
    "jeronimos":             [22, 30, "Luxe, centre historique, niche premium"],
    "centro":                [20, 28, "Historique, pression touristique, mixte"],
    "chamartin":             [20, 26, "Aise, ambassades, professionnels"],
    "palacio":               [20, 28, "Centre historique premium, Palacio Real"],
  },
  barcelona: {
    _city_avg: [16, 22],
    _note: "Encadrement des loyers actif (Ley de Contencio). +7.8% sur 12 mois (INE T4 2025). Risque reglementaire eleve.",
    "nou barris":            [13, 16, "Ouvrier, meilleur rendement BCN, communaute immigree"],
    "sant andreu":           [15, 19, "En gentrification, bon rendement"],
    "horta-guinardo":        [15, 18, "Residentiel familles, calme, rendement correct"],
    "horta guinardo":        [15, 18, "Residentiel familles, calme, rendement correct"],
    "sants":                 [16, 20, "Mixte ouvrier/universitaire, base locative solide"],
    "sants-montjuic":        [16, 20, "Mixte ouvrier/universitaire, base locative solide"],
    "sant marti":            [16, 21, "Poblenou tech hub, montee rapide, bon rendement"],
    "poblenou":              [17, 22, "Tech hub, jeunes professionnels, forte hausse"],
    "les corts":             [18, 23, "Aise, Camp Nou, professionnels, demande stable"],
    "gracia":                [19, 25, "Tendance, jeunes CSP+, forte pression, encadre"],
    "eixample":              [20, 27, "Central prime, max demande, ENCADREMENT loyers"],
    "eixample dret":         [20, 27, "Central prime, ENCADREMENT loyers"],
    "eixample esquerra":     [19, 25, "Central, forte demande, ENCADREMENT loyers"],
    "sarria":                [22, 30, "Aise, colline, expatries/familles, faible rendement"],
    "sarria-sant gervasi":   [22, 30, "Aise, colline, expatries/familles, faible rendement"],
    "sant gervasi":          [22, 30, "Aise, colline, faible rendement"],
    "ciutat vella":          [18, 26, "Pression touristique, ENCADREMENT, risque eleve"],
    "barceloneta":           [18, 26, "Pression touristique max, risque reglementaire"],
    "el born":               [19, 26, "Touristique/bobo, forte pression, encadre"],
  },
  valencia: {
    _city_avg: [12, 16],
    _note: "Meilleur ratio rendement/prix d'Espagne actuellement. +14.1% sur 12 mois (INE 2025).",
    "rascanya":              [10, 13, "Abordable, familles jeunes, communaute immigree"],
    "patraix":               [10, 13, "Abordable, familles, bon rendement"],
    "jesus":                 [10, 13, "Ouvrier, stable, bon rendement"],
    "quatre carreres":       [11, 14, "Mixte, familles, abordable"],
    "benimaclet":            [11, 14, "Etudiants/jeunes pro, excellent rendement"],
    "campanar":              [12, 15, "Residentiel familles, bonne valeur"],
    "poblats maritims":      [12, 16, "Proximite mer, hausse expat, demande croissante"],
    "algiros":               [13, 16, "Zone universitaire, demande etudiante fiable"],
    "el carmen":             [13, 16, "Centre historique, pression touristique"],
    "ciutat vella":          [13, 16, "Historique, tourisme, bonne demande"],
    "russafa":               [13, 17, "Tendance, expatries, jeunes pro, hausse rapide"],
    "extramurs":             [14, 17, "En gentrification, profil mixte"],
    "eixample":              [15, 19, "Central premium, solide, moins de rendement"],
    "pla del real":          [16, 20, "Aise, universitaire, locataires fiables"],
  },
  malaga: {
    _city_avg: [12, 16],
    _note: "Forte demande expat (UK, FR, NL). Chomage Andalousie 15.2% (EPA T4 2025).",
    "campanillas":           [10, 13, "Banlieue industrielle, logisticiens, haut rendement"],
    "churriana":             [10, 13, "Proche aeroport, familles, bon rendement"],
    "palma-palmilla":        [9,  12, "Revenu bas, rendement max mais risque social eleve"],
    "palma palmilla":        [9,  12, "Revenu bas, rendement max mais risque social eleve"],
    "carretera de cadiz":    [11, 14, "Ouvrier ouest, haut rendement, profil modeste"],
    "puerto de la torre":    [11, 14, "Residentiel nord, familles, profil stable"],
    "ciudad jardin":         [12, 15, "Classe moyenne residentielle, stable"],
    "teatinos":              [12, 16, "Universite + Parc Tech, etudiants/ingenieurs"],
    "teatinos-universidad":  [12, 16, "Universite + Parc Tech, excellent potentiel"],
    "este":                  [13, 16, "Est residentiel, familles, demande solide"],
    "centro":                [13, 17, "Centre, expatries, effet Soho, forte hausse"],
    "soho":                  [14, 18, "Gentrification maximale, expatries, artistes"],
    "lagunillas":            [12, 16, "En transition, montee des prix, jeune population"],
    "torremolinos":          [12, 15, "Touristique/residentiel, mix court/long terme"],
    "benalmadena":           [12, 15, "Touristique/residentiel, bonne demande expat"],
    "marbella":              [14, 20, "Premium resort, expatries, rendement variable"],
    "puerto banus":          [18, 28, "Luxe, ultra-premium, rendement faible"],
    "estepona":              [12, 16, "En croissance, bonne valeur, demande expat"],
    "nerja":                 [12, 16, "Cotier, forte demande UK/FR, bon rendement"],
  },
};

export const RENT_MODIFIERS = `UNIVERSAL RENT ADJUSTMENTS (apply on top of base range):
- Gated community with pool + gym + concierge: +10-15%
- Included garage: +100-150 euros/mo
- New build (less than 5 years): +5-10%
- Poor energy rating (E/F/G): -3-5%
- Top floor with terrace: +8-12%
- Ground floor: -5-10%
- Fully renovated (last 5 years): +5-8%
- Needs renovation: -10-15%`;

function normalize(str) {
  return (str || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[-\u2013\u2014]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function getRentData(city, neighbourhood) {
  const cityKey = normalize(city);
  const cityEntry = Object.entries(RENT_PRICES).find(([k]) =>
    cityKey.includes(normalize(k)) || normalize(k).includes(cityKey)
  );
  if (!cityEntry) return null;
  const [, cityData] = cityEntry;

  const neighKey = normalize(neighbourhood);
  let match = null;

  // 1. Exact
  match = Object.entries(cityData).find(([k]) => !k.startsWith("_") && normalize(k) === neighKey);
  // 2. Partial
  if (!match) match = Object.entries(cityData).find(([k]) =>
    !k.startsWith("_") && (neighKey.includes(normalize(k)) || normalize(k).includes(neighKey))
  );

  if (match) {
    const [name, [min, max, profile]] = match;
    return { found: true, district: name, min, max, profile, cityNote: cityData._note };
  }

  const [avgMin, avgMax] = cityData._city_avg || [12, 18];
  return { found: false, district: null, min: avgMin, max: avgMax, profile: null, cityNote: cityData._note };
}
