# Mémoria — mise en ligne de la refonte

> **En production : grille tarifaire v2, 22 octobre 2026** (déploiement Netlify `6ad9a96b305d06f8ec31b5fd`).
> Versions précédentes, pour revenir en arrière en un clic (Netlify → Deploys → « Publish deploy ») :
> refonte sans grille v2 `6ad9a2fbcbdfe3e596d45d63` ; site d'origine `6a5cfa17baef82e9eb10766d`.
> Les sections ci-dessous servent pour les prochaines mises à jour.

## Ce qu'il faut glisser sur Netlify

Le dossier **`memoria/`** (ou le contenu de `livrables/memoria-netlify.zip`, décompressé) :
c'est le site complet, prêt à déployer, sans étape de build.
Dans Netlify : projet *beamish-valkyrie-7aeabd* → **Deploys** → glisser le dossier.

`memoria-tools/` n'est **pas** à déployer : ce sont les scripts qui ont produit les pages
(gabarit commun, catalogue, guides, SEO, QA). Ils ne servent que si vous voulez régénérer.

## Avant de déployer

1. Remplir les placeholders : voir `livrables/PLACEHOLDERS.md` (au minimum `[WHATSAPP]`,
   `[PRIX]`, `[COMMISSION]`, logos et témoignages — ou retirer les blocs de preuve tant
   que vous n'avez pas de contenu réel).
2. Faire relire les textes en hébreu par un locuteur natif.
3. Faire valider par votre avocat partenaire les passages juridiques : page Propriétaires
   (garanties, fianza, honoraires), guide « Louer à Madrid », mentions légales mises à jour.
4. Lancer `python3 memoria-tools/qa.py` : doit afficher 0 erreur.

## Juste après le déploiement

1. **Formulaires** : Netlify → *Forms*. Vous devez voir cinq formulaires : `rdv`, `rdv-en`,
   `rdv-he` (existants, noms inchangés), `corporate` et `proprietaires` (nouveaux).
   Configurer pour les deux nouveaux une notification e-mail (*Forms → Form notifications*).
   Envoyer une demande test depuis chaque page :
   - /#contact, /en/#contact, /he/#contact
   - /entreprises/#devis, /en/corporate/#devis, /he/corporate/#devis
   - /proprietaires/#bien, /en/landlords/#bien, /he/landlords/#bien
2. **En-têtes de sécurité** :
   `curl -sI https://memoriamadrid.com/ | grep -iE "x-frame|x-content|referrer|permissions"`
   S'ils n'apparaissent pas (possible avec un déploiement par glisser-déposer, qui peut ignorer
   `netlify.toml`), copier `memoria-tools/_headers` dans `memoria/` et redéployer.
3. **Redirections** : https://memoriamadrid.com/corporate doit mener à /en/corporate/ ;
   https://memoriamadrid.com/en/page-inexistante doit afficher la 404 anglaise.
4. **Search Console** : soumettre https://memoriamadrid.com/sitemap.xml (31 URL, avec hreflang).
5. **Plausible** : vérifier que les visites des nouvelles pages remontent ; les clics WhatsApp
   apparaissent comme liens sortants vers wa.me une fois le numéro renseigné.

## Ce qui a changé (résumé)

- Positionnement « Relocation & Destination Services Madrid » : titles, descriptions, OG/Twitter,
  JSON-LD `ProfessionalService`.
- `/services/` (FR, EN, HE) : six familles + services additionnels, fiches détaillées.
- `/entreprises/`, `/en/corporate/`, `/he/corporate/` : offre B2B, formulaire `corporate`.
- `/proprietaires/`, `/en/landlords/`, `/he/landlords/` : offre propriétaires, formulaire `proprietaires`.
- Guides : 7 en FR, 7 en EN, 2 en HE, index par langue.
- `/docs/memoria-capability-statement` : fiche fournisseur A4 (EN) pour les RMC.
- Bouton WhatsApp, champ « Vous êtes » dans le formulaire RDV, « Devis entreprise » dans l'en-tête.
- `site-v2.css`, `site-v2.js`, `_redirects`, `netlify.toml`, pages 404 FR/EN/HE, `favicon.svg`.
- Aucune URL existante supprimée ou renommée.
