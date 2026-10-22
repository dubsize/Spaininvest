# Checklist QA — grille tarifaire v2 et corrections (22 octobre 2026)

En ligne : déploiement Netlify `6ad9a96b305d06f8ec31b5fd`.
Version précédente (avant grille v2), pour revenir en arrière : `6ad9a2fbcbdfe3e596d45d63`.

| # | Contrôle | Résultat |
|---|---|---|
| 1 | **Trois langues** : 47 pages ouvertes en 390 px et 1280 px, aucune erreur JavaScript, aucun débordement horizontal | ✅ |
| 2 | **RTL** : pages `/he/` en `dir="rtl"` ; tableau des packs et catalogue vérifiés en capture mobile HE | ✅ |
| 3 | **Formulaires** : les 9 formulaires bloquent l'envoi vide et envoient tous leurs champs ; en production, Netlify détecte toujours `rdv`, `rdv-en`, `rdv-he`, `corporate`, `proprietaires` | ✅ |
| 4 | **Cohérence des prix** accueil ↔ catalogue, contrôlée automatiquement en FR, EN et HE : 590 / 890 / 1 190 / 1 490 / 1 790 / 2 490 / 2 890 / 290 / 490 € présents des deux côtés, aucun ancien prix (690, 990, certificat UE 250) restant | ✅ |
| 5 | Aucun « Sur devis » restant pour les particuliers dans les trois catalogues (seule l'immigration hors UE reste « coordination dès 490 € + avocat sur devis ») | ✅ |
| 6 | « TTC / incl. VAT / כולל מע״מ » à côté des prix particuliers ; « HT » sur les trois pages Entreprises | ✅ |
| 7 | Packs Essentiel / Logement / Complet : tableau sur les trois accueils et en tête des trois catalogues ; Pack Installation seul 890 / 1 190 € ; Pack Départ 490 € | ✅ |
| 8 | Page Propriétaires FR/EN/HE : commission ½ mois HT + TVA (min. 900 € HT), intervention 90 € TTC, état des lieux de sortie 250 € TTC, rappel loi 2023 | ✅ |
| 9 | E1 « à l'unité de 60 à 290 € » sur la carte et dans le bloc Installation | ✅ |
| 10 | E2 FAQ langues de l'accueil : FR, EN, HE, ES | ✅ |
| 11 | E3 « Famille 02 — Installation » | ✅ |
| 12 | E4 plus aucune mention « hébergées dans l'UE » (page Entreprises, FAQ entreprises, capability statement) | ✅ vérifié en ligne |
| 13 | E5 bandeau cookies retiré sur les 47 pages, mention d'information en pied de page, politique cookies FR/EN/HE mise à jour, `cookies.js` supprimé | ✅ vérifié en ligne |
| 14 | E6 `/docs/memoria-capability-statement` répond 200 en production (aucune règle `_redirects` nécessaire) | ✅ |
| 15 | E7 bouton WhatsApp : **toujours masqué**, le numéro n'a pas été fourni | ⚠️ en attente |
| 16 | Preuves (logos, témoignages, étude de cas) : toujours masquées, rien d'inventé | ⚠️ en attente de trois avis réels |
| 17 | Sitemap régénéré : 31 URL, toutes en 200 en production | ✅ |
| 18 | En-têtes de sécurité toujours présents en production | ✅ |
