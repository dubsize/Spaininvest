# URL à soumettre — Google Search Console et Bing Webmaster Tools

Mise en ligne de la grille v2 : 22 octobre 2026 (déploiement Netlify `6ad9a96b305d06f8ec31b5fd`).

## 1. Le plus important : le sitemap

Soumettre **une seule URL** dans les deux outils, elle contient toutes les pages et leurs équivalents de langue (hreflang) :

```
https://memoriamadrid.com/sitemap.xml
```

- **Google Search Console** : ajouter la propriété *Domaine* `memoriamadrid.com` (vérification par enregistrement DNS TXT chez votre registrar), puis *Sitemaps* → coller l'URL ci-dessus.
- **Bing Webmaster Tools** : *Importer depuis Google Search Console* (le plus rapide), ou ajouter le site et soumettre le même sitemap. Bing alimente aussi DuckDuckGo et ChatGPT Search.

## 2. Pages à demander en indexation prioritaire

Dans Search Console, *Inspection de l'URL* → *Demander l'indexation* (quota d'une dizaine par jour) :

1. https://memoriamadrid.com/
2. https://memoriamadrid.com/services/
3. https://memoriamadrid.com/entreprises/
4. https://memoriamadrid.com/proprietaires/
5. https://memoriamadrid.com/en/
6. https://memoriamadrid.com/en/corporate/
7. https://memoriamadrid.com/he/
8. https://memoriamadrid.com/guides/cita-previa-nie-certificat-ue-madrid
9. https://memoriamadrid.com/guides/louer-madrid-expatrie
10. https://memoriamadrid.com/en/guides/renting-in-madrid-as-an-expat

## 3. Liste complète (31 URL du sitemap)

### Français (12)

- https://memoriamadrid.com/
- https://memoriamadrid.com/entreprises/
- https://memoriamadrid.com/guides/
- https://memoriamadrid.com/guides/certificat-numerique-clave
- https://memoriamadrid.com/guides/cita-previa-nie-certificat-ue-madrid
- https://memoriamadrid.com/guides/electricite-gaz-eau-madrid
- https://memoriamadrid.com/guides/empadronamiento-madrid
- https://memoriamadrid.com/guides/louer-madrid-expatrie
- https://memoriamadrid.com/guides/nie-avant-le-depart
- https://memoriamadrid.com/guides/scolariser-madrid-hors-campagne
- https://memoriamadrid.com/proprietaires/
- https://memoriamadrid.com/services/

### English (12)

- https://memoriamadrid.com/en/
- https://memoriamadrid.com/en/corporate/
- https://memoriamadrid.com/en/guides/
- https://memoriamadrid.com/en/guides/cita-previa-nie-eu-certificate-madrid
- https://memoriamadrid.com/en/guides/digital-certificate-clave
- https://memoriamadrid.com/en/guides/electricity-gas-water-madrid
- https://memoriamadrid.com/en/guides/empadronamiento-madrid
- https://memoriamadrid.com/en/guides/nie-before-you-move
- https://memoriamadrid.com/en/guides/renting-in-madrid-as-an-expat
- https://memoriamadrid.com/en/guides/school-enrolment-madrid-mid-year
- https://memoriamadrid.com/en/landlords/
- https://memoriamadrid.com/en/services/

### עברית (7)

- https://memoriamadrid.com/he/
- https://memoriamadrid.com/he/corporate/
- https://memoriamadrid.com/he/guides/
- https://memoriamadrid.com/he/guides/empadronamiento-madrid
- https://memoriamadrid.com/he/guides/nie-before-you-move
- https://memoriamadrid.com/he/landlords/
- https://memoriamadrid.com/he/services/

Non soumises volontairement : pages légales (en `noindex`), pages 404, fiche fournisseur `/docs/memoria-capability-statement` (en `noindex`, destinée aux formulaires des RMC).
