// rentPrices.js — Loyers de référence par quartier (euros/m2/mois)
// Source : Idealista (informes de precios, moyennes par district) — mise a jour manuelle trimestrielle
// Derniere mise a jour : Juillet 2026 — donnees Idealista avril 2026 (Madrid, Malaga) et mai 2026 (Barcelona, Valencia)
// Methode : fourchette min/max = moyenne Idealista du district +/- ~10-12%
// Prochaine mise a jour recommandee : Octobre 2026

export const RENT_PRICES = {
  madrid: {
    _city_avg: [20, 25],
    _note: "Marche en forte hausse : 23,3 EUR/m2 en avril 2026, +8,6% sur 12 mois (Idealista). Les plus fortes hausses sont dans les districts populaires (Usera +16%).",
    "vallecas":              [17, 22, "Ouvrier, forte demande, jeune population, +15% sur un an"],
    "puente de vallecas":    [17, 22, "Ouvrier, rendement max Madrid, jeune population, hausse rapide"],
    "villa de vallecas":     [16, 20, "Residentiel neuf, familles, bonne demande"],
    "villaverde":            [15, 19, "Industriel/residentiel, rendement eleve, district le moins cher"],
    "usera":                 [18, 22, "Multiculturel, tres forte demande, +16% sur un an, rotation rapide"],
    "carabanchel":           [16, 20, "En gentrification, familles, bon rendement"],
    "latina":                [16, 20, "Ouvrier, bonne demande, communaute immigree"],
    "tetuan":                [21, 25, "Gentrification avancee, multiculturel, prix quasi centraux desormais"],
    "ciudad lineal":         [18, 22, "Classe moyenne, demande stable, bon rendement"],
    "san blas":              [15, 19, "Est ouvrier, jeune population croissante"],
    "san blas-canillejas":   [15, 19, "Est ouvrier, jeune population croissante"],
    "arganzuela":            [20, 24, "En hausse (Madrid Rio), mixte, bonne demande"],
    "moratalaz":             [15, 19, "Residentiel calme, pop agee, demande moderee"],
    "vicalvaro":             [15, 19, "Banlieue familiale, logements neufs, forte hausse recente"],
    "hortaleza":             [17, 21, "Moderne, familles, Sanchinarro/Las Tablas"],
    "sanchinarro":           [17, 21, "Moderne residentiel, familles, services"],
    "las tablas":            [17, 21, "Residentiel neuf, familles, bien connecte"],
    "valdebebas":            [17, 21, "Nouveau quartier, familles, bonne qualite"],
    "fuencarral":            [16, 20, "Nord residentiel, familles, croissance"],
    "fuencarral-el pardo":   [16, 20, "Nord residentiel, familles, croissance"],
    "barajas":               [15, 19, "Zone aeroport, travailleurs logistique/aviation"],
    "moncloa":               [20, 25, "Premium central, universitaire, forte demande"],
    "moncloa-aravaca":       [20, 25, "Premium, Complutense, etudiants/professionnels"],
    "chamberi":              [24, 29, "Premium central, forte demande, faible rendement"],
    "retiro":                [22, 26, "Premium residentiel, parc, locataires CSP+"],
    "salamanca":             [25, 31, "Luxe, executifs/expatries, rendement tres faible"],
    "jeronimos":             [24, 30, "Luxe, niche premium proche Retiro"],
    "centro":                [24, 30, "Historique, pression touristique, mixte"],
    "chamartin":             [21, 26, "Aise, ambassades, professionnels"],
    "palacio":               [24, 30, "Centre historique premium, Palacio Real"],
  },
  barcelona: {
    _city_avg: [19, 24],
    _note: "ATTENTION : loyers en BAISSE de -6,1% sur 12 mois (22,5 EUR/m2 en mai 2026, Idealista) — effet du controle des loyers catalan (zone tensionnee). Double risque investisseur : loyer plafonne ET marche en repli. Verifier l'indice de referencia avant tout calcul.",
    "nou barris":            [14, 18, "Ouvrier, meilleur rendement BCN, communaute immigree"],
    "sant andreu":           [16, 19, "En gentrification, bon rendement (estimation interpolee)"],
    "horta-guinardo":        [16, 20, "Residentiel familles, calme, rendement correct"],
    "horta guinardo":        [16, 20, "Residentiel familles, calme, rendement correct"],
    "sants":                 [17, 21, "Mixte ouvrier/universitaire, base locative solide"],
    "sants-montjuic":        [17, 21, "Mixte ouvrier/universitaire, base locative solide"],
    "sant marti":            [20, 24, "Poblenou tech hub, demande forte mais loyers encadres"],
    "poblenou":              [21, 25, "Tech hub, jeunes professionnels, encadrement actif"],
    "les corts":             [19, 23, "Aise, Camp Nou, professionnels, demande stable"],
    "gracia":                [21, 25, "Tendance, jeunes CSP+, ENCADREMENT loyers"],
    "eixample":              [23, 28, "Central prime, max demande, ENCADREMENT loyers"],
    "eixample dret":         [23, 28, "Central prime, ENCADREMENT loyers"],
    "eixample esquerra":     [22, 27, "Central, forte demande, ENCADREMENT loyers"],
    "sarria":                [19, 24, "Aise, colline, expatries/familles, faible rendement"],
    "sarria-sant gervasi":   [19, 24, "Aise, colline, expatries/familles, faible rendement"],
    "sant gervasi":          [19, 24, "Aise, colline, faible rendement"],
    "ciutat vella":          [22, 27, "Pression touristique, ENCADREMENT, risque eleve"],
    "barceloneta":           [22, 27, "Pression touristique max, risque reglementaire"],
    "el born":               [22, 27, "Touristique/bobo, forte pression, encadre"],
  },
  valencia: {
    _city_avg: [14, 18],
    _note: "Hausse moderee : 16,5 EUR/m2 en mai 2026, +5,1% sur 12 mois (Idealista). Reste un des meilleurs ratios rendement/prix des grandes villes, mais l'ecart avec Madrid se reduit.",
    "rascanya":              [13, 16, "Abordable, familles jeunes, communaute immigree (interpole)"],
    "patraix":               [12, 15, "District le moins cher de Valencia, familles, bon rendement"],
    "jesus":                 [13, 16, "Ouvrier, plus forte hausse recente de la ville (interpole)"],
    "quatre carreres":       [14, 17, "Mixte, familles, en rattrapage (interpole)"],
    "benimaclet":            [14, 17, "Etudiants/jeunes pro, excellent rendement (interpole)"],
    "campanar":              [14, 17, "Residentiel familles, bonne valeur (interpole)"],
    "poblats maritims":      [15, 18, "Proximite mer, renovation urbaine, forte hausse"],
    "algiros":               [15, 18, "Zone universitaire, demande etudiante fiable (interpole)"],
    "el carmen":             [18, 22, "Centre historique, pression touristique"],
    "ciutat vella":          [18, 22, "District le plus cher de Valencia, tourisme, forte demande"],
    "russafa":               [16, 19, "Tendance, expatries, jeunes pro (interpole)"],
    "extramurs":             [16, 19, "En gentrification, profil mixte (interpole)"],
    "eixample":              [17, 20, "Central premium, solide, moins de rendement"],
    "pla del real":          [16, 20, "Aise, universitaire, locataires fiables (interpole)"],
    "camins al grau":        [16, 19, "Forte pression, proche mer et centre, hausse rapide"],
  },
  malaga: {
    _city_avg: [14, 18],
    _note: "Hausse moderee : 16,3 EUR/m2 en avril 2026, +5,8% sur 12 mois (Idealista). Forte demande expat (UK, FR, NL). Chomage Andalousie eleve (~15%, EPA fin 2025) : integrer le risque d'impaye.",
    "campanillas":           [12, 15, "Banlieue industrielle, logisticiens, haut rendement"],
    "churriana":             [12, 15, "Proche aeroport, familles, bon rendement"],
    "palma-palmilla":        [11, 13, "Revenu bas, rendement max mais risque social eleve"],
    "palma palmilla":        [11, 13, "Revenu bas, rendement max mais risque social eleve"],
    "carretera de cadiz":    [15, 18, "Ouvrier ouest en forte hausse, metro, n'est plus la reserve abordable"],
    "puerto de la torre":    [13, 16, "Residentiel nord, familles, profil stable"],
    "ciudad jardin":         [12, 15, "Classe moyenne residentielle, forte hausse recente des prix de vente"],
    "cruz de humilladero":   [13, 16, "Fonctionnel, bien connecte, bon rapport qualite/prix"],
    "bailen-miraflores":     [14, 17, "Central abordable, en rattrapage"],
    "bailen miraflores":     [14, 17, "Central abordable, en rattrapage"],
    "teatinos":              [13, 16, "Universite + Parc Tech, etudiants/ingenieurs, prix vente en forte hausse"],
    "teatinos-universidad":  [13, 16, "Universite + Parc Tech, excellent potentiel"],
    "este":                  [15, 19, "Est residentiel premium, familles, demande solide"],
    "centro":                [15, 19, "Centre, expatries, effet Soho, forte demande"],
    "soho":                  [16, 20, "Gentrification maximale, expatries, artistes"],
    "lagunillas":            [14, 18, "En transition, montee des prix, jeune population"],
    "martiricos":            [19, 24, "Nouvelle zone premium (tours), plus forte hausse de Malaga"],
    "martiricos-la roca":    [19, 24, "Nouvelle zone premium (tours), plus forte hausse de Malaga"],
    "torremolinos":          [13, 17, "Touristique/residentiel, mix court/long terme (estimation)"],
    "benalmadena":           [13, 17, "Touristique/residentiel, bonne demande expat (estimation)"],
    "marbella":              [16, 22, "Premium resort, expatries, rendement variable (estimation)"],
    "puerto banus":          [20, 30, "Luxe, ultra-premium, rendement faible (estimation)"],
    "estepona":              [14, 18, "En croissance, bonne valeur, demande expat (estimation)"],
    "nerja":                 [13, 17, "Cotier, forte demande UK/FR, bon rendement (estimation)"],
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
}    "chamartin":             [20, 26, "Aise, ambassades, professionnels"],
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
