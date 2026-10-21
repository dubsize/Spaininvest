# Checklist QA — refonte Mémoria (21 octobre 2026)

Tests faits sur une copie locale du dossier `memoria/`, servie en HTTP et parcourue dans Chromium
(Playwright), et par le script `memoria-tools/qa.py`. Ce qui ne peut être vérifié qu'une fois le site
sur Netlify est marqué « après déploiement ».

| # | Contrôle | Résultat |
|---|---|---|
| 1 | **Trois langues naviguées** : 47 pages ouvertes en 390 px et 1280 px, aucune erreur JavaScript | ✅ |
| 2 | Sélecteur de langue FR / EN / עב sur chaque page, pointant vers la page équivalente quand elle existe (sinon vers l'accueil de la langue) | ✅ |
| 3 | **RTL** : toutes les pages `/he/` ont `lang="he" dir="rtl"`, polices hébraïques, mise en page miroir vérifiée en capture (accueil, services, entreprises, guides) | ✅ |
| 4 | **hreflang** : réciprocité vérifiée automatiquement sur toutes les pages, `x-default` = version EN | ✅ |
| 5 | **Canonical** sur 47/47 pages, alignés sur les URL sans `.html` | ✅ |
| 6 | **Liens internes et ancres** : 0 lien cassé, 0 ancre manquante | ✅ |
| 7 | **Formulaires** (9 : rdv, rdv-en, rdv-he, corporate ×3, proprietaires ×3) : `data-netlify`, champ caché `form-name`, honeypot, consentement obligatoire ; envoi vide bloqué ; envoi rempli → requête POST avec le bon `form-name` et tous les champs ; mêmes champs dans les trois langues | ✅ côté navigateur — réception Netlify : **après déploiement** |
| 8 | Bug corrigé pendant le test : le champ « loyer visé » refusait les montants non multiples de 50 | ✅ |
| 9 | **Sitemap** : XML valide, 31 URL, toutes existantes, aucune page `noindex`, alternates hreflang inclus | ✅ |
| 10 | **404 personnalisée** : `/404.html` (FR), `/en/404.html`, `/he/404.html` via `_redirects` | ✅ fichiers — comportement : **après déploiement** |
| 11 | **Mobile** : aucune page plus large que l'écran à 390 px (tableaux larges rendus défilables) | ✅ |
| 12 | **Lighthouse** (mobile, local) — accueil FR : perf 99 / access. 99 / bonnes pratiques 96 / SEO 100 ; accueil HE : 100 / 99 / 96 / 100 ; Services : 100 / 100 / 96 / 100 ; Entreprises : 100 / 100 / 96 / 100 ; guide EN : 100 / 100 / 96 / 92. Pages légales : SEO 66, car en `noindex` (choix existant, inchangé) | ✅ ≥ 90 hors pages légales |
| 13 | **Contraste** : texte laiton trop clair remplacé par une teinte AA sur les petits textes ; bouton d'en-tête des accueils corrigé | ✅ |
| 14 | **Poids** : plus grosse page HTML 51 Ko (accueil FR), site complet 0,9 Mo, aucune image, polices chargées sans bloquer le rendu | ✅ |
| 15 | Plausible et bannière cookies présents sur toutes les pages (sauf la fiche imprimable, qui n'a pas de bannière) | ✅ |
| 16 | Pages légales : contenu inchangé (hors description de l'activité élargie aux entreprises et propriétaires), canonical et hreflang ajoutés | ✅ |
| 17 | Capability statement : une page A4 en PDF (impression Chromium) | ✅ |
| 18 | En-têtes de sécurité (`netlify.toml`) | **après déploiement** (voir README) |
| 19 | Placeholders restants : voir `PLACEHOLDERS.md` | ⚠️ à remplir |
| 20 | Relecture native des textes hébreux ; validation juridique des pages Propriétaires et du guide location | ⚠️ à faire |
