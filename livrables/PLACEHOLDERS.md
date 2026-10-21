# Placeholders à remplir — Mémoria

Les crochets `[…]` sont visibles sur le site tant qu'ils ne sont pas remplacés.
À faire **avant** de glisser le dossier sur Netlify.

## Comment les remplir

- **Le plus simple** : modifier la source dans `memoria-tools/` (une seule fois pour les trois langues
  quand c'est possible), puis relancer les scripts :
  `python3 memoria-tools/gen_services.py && python3 memoria-tools/gen_corporate.py && python3 memoria-tools/gen_landlords.py && python3 memoria-tools/gen_guides.py && python3 memoria-tools/gen_misc.py && python3 memoria-tools/seo.py && python3 memoria-tools/qa.py --placeholders`
- **Sans Python** : remplacer directement dans les fichiers HTML de `memoria/` (liste complète plus bas,
  avec fichier et ligne). Dans ce cas, ne relancez plus les générateurs, ils écraseraient vos modifications.

## Par action (source à modifier)

| Placeholder | Où le remplir une fois | Pages concernées |
|---|---|---|
| `[WHATSAPP]` | `memoria/site-v2.js` ligne 5 — numéro international, chiffres seulement (ex. 34600123456). Tant qu'il est vide, le bouton renvoie au formulaire de contact. | toutes |
| `[PRIX]` (8 services) | `memoria-tools/services_data.py`, constante `FROM_TBD` utilisée par : briefing pré-arrivée, journée d'orientation, remise des clés et état des lieux d'entrée, permis de stationnement résident (SER), cartographie scolaire, leasing / renting, clôture des suministros, baja du padrón. Remplacer `price=FROM_TBD` par `price=eur(XXX)` service par service. | /services/ ×3 |
| `[COMMISSION]` | `memoria-tools/gen_landlords.py` lignes 36, 83, 130 (ex. « 1 mois de loyer + TVA ») | /proprietaires/, /en/landlords/, /he/landlords/ |
| `[X]` (étude de cas) | `memoria-tools/proof.py` (indicateurs et « semaine 2 »), FR / EN / HE | pages Entreprises ×3 |
| Citation RH de l'étude de cas `[CITATION…]`, `[FONCTION]`, `[SECTEUR…]` | `memoria-tools/proof.py`, `case_quote` et `case_quote_by` | pages Entreprises ×3 |
| `[LOGO CLIENT 1…6]` | `memoria-tools/proof.py`, fonction `logos()` : remplacer chaque cadre par `<img src="/logos/client-N.svg" alt="Nom" width="140" height="48">` (accord écrit du client requis) | accueils ×3, Entreprises ×3 |
| Témoignages `[TÉMOIGNAGE n]`, `[PRÉNOM]`, `[NATIONALITÉ]`, `[POSTE]` | `memoria-tools/proof.py`, liste `testimonials` (textes réels, avec accord écrit) | accueils ×3, Entreprises ×3 |
| `[LINKEDIN]` | JSON-LD des trois accueils (`sameAs`) | accueils ×3 |
| `[GOOGLE_BUSINESS_PROFILE]` | commentaire au-dessus du JSON-LD + commentaire dans le pied de page des accueils | accueils ×3 |
| `[POLICE]`, `[ASSUREUR]`, `[MONTANT DE GARANTIE]`, `[NOM DU CONTACT]`, `[FONCTION]`, `[TÉLÉPHONE]` | `memoria/docs/memoria-capability-statement.html` | capability statement |
| `[IMAGE : visuel de partage 1200×630]` | déposer `memoria/og-image.png`, puis dans `memoria-tools/seo.py` décommenter les deux lignes `og:image` / `twitter:image` et relancer `seo.py` | 47 pages (commentaire HTML, invisible) |
| `[IMAGE : …]` dans deux guides | `memoria-tools/guides/fr/cita-previa-nie-certificat-ue-madrid.html`, `memoria-tools/guides/fr/louer-madrid-expatrie.html` : remplacer par une image réelle ou supprimer le paragraphe | 2 guides FR |

## Liste complète (fichier dans `memoria/` : ligne — placeholders)

Hors commentaire `og:image` répété dans chaque page.

- `index.html:262` — [GOOGLE_BUSINESS_PROFILE]
- `index.html:304` — [LINKEDIN]
- `index.html:584` — [LOGOS]
- `index.html:585` — [LOGO CLIENT 1]  [LOGO CLIENT 2]  [LOGO CLIENT 3]  [LOGO CLIENT 4]  [LOGO CLIENT 5]  [LOGO CLIENT 6]
- `index.html:586` — [TÉMOIGNAGES]
- `index.html:588` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 1 — deux à trois phrases sur ce que Mémoria a changé dans l'installation]
- `index.html:589` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 2 — deux à trois phrases]
- `index.html:590` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 3 — deux à trois phrases]
- `index.html:747` — [GOOGLE_BUSINESS_PROFILE]
- `site-v2.js:3` — [WHATSAPP]
- `site-v2.js:5` — [WHATSAPP]
- `docs/memoria-capability-statement.html:90` — [ASSUREUR]  [MONTANT DE GARANTIE]  [POLICE]
- `docs/memoria-capability-statement.html:109` — [FONCTION]  [NOM DU CONTACT]  [TÉLÉPHONE]
- `en/index.html:217` — [GOOGLE_BUSINESS_PROFILE]
- `en/index.html:259` — [LINKEDIN]
- `en/index.html:539` — [LOGOS]
- `en/index.html:540` — [CLIENT LOGO 1]  [CLIENT LOGO 2]  [CLIENT LOGO 3]  [CLIENT LOGO 4]  [CLIENT LOGO 5]  [CLIENT LOGO 6]
- `en/index.html:541` — [TÉMOIGNAGES]
- `en/index.html:543` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 1 — two or three sentences on what Mémoria changed about the move]
- `en/index.html:544` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 2 — two or three sentences]
- `en/index.html:545` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 3 — two or three sentences]
- `en/index.html:660` — [GOOGLE_BUSINESS_PROFILE]
- `en/corporate/index.html:146` — [LOGOS]
- `en/corporate/index.html:147` — [CLIENT LOGO 1]  [CLIENT LOGO 2]  [CLIENT LOGO 3]  [CLIENT LOGO 4]  [CLIENT LOGO 5]  [CLIENT LOGO 6]
- `en/corporate/index.html:152` — [X]
- `en/corporate/index.html:153` — [X]
- `en/corporate/index.html:154` — [COMPANY SECTOR]  [JOB TITLE]  [QUOTE FROM THE HR MANAGER — one or two sentences]
- `en/corporate/index.html:163` — [TÉMOIGNAGES]
- `en/corporate/index.html:165` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 1 — two or three sentences on what Mémoria changed about the move]
- `en/corporate/index.html:166` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 2 — two or three sentences]
- `en/corporate/index.html:167` — [FIRST NAME]  [JOB TITLE]  [NATIONALITY]  [TESTIMONIAL 3 — two or three sentences]
- `en/landlords/index.html:103` — [COMMISSION]
- `en/services/index.html:71` — [PRIX]
- `en/services/index.html:75` — [PRIX]
- `en/services/index.html:83` — [PRIX]
- `en/services/index.html:135` — [PRIX]
- `en/services/index.html:186` — [PRIX]
- `en/services/index.html:229` — [PRIX]
- `en/services/index.html:248` — [PRIX]
- `en/services/index.html:252` — [PRIX]
- `entreprises/index.html:146` — [LOGOS]
- `entreprises/index.html:147` — [LOGO CLIENT 1]  [LOGO CLIENT 2]  [LOGO CLIENT 3]  [LOGO CLIENT 4]  [LOGO CLIENT 5]  [LOGO CLIENT 6]
- `entreprises/index.html:152` — [X]
- `entreprises/index.html:153` — [X]
- `entreprises/index.html:154` — [CITATION DU RESPONSABLE RH — une à deux phrases]  [FONCTION]  [SECTEUR DE L'ENTREPRISE]
- `entreprises/index.html:163` — [TÉMOIGNAGES]
- `entreprises/index.html:165` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 1 — deux à trois phrases sur ce que Mémoria a changé dans l'installation]
- `entreprises/index.html:166` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 2 — deux à trois phrases]
- `entreprises/index.html:167` — [NATIONALITÉ]  [POSTE]  [PRÉNOM]  [TÉMOIGNAGE 3 — deux à trois phrases]
- `guides/cita-previa-nie-certificat-ue-madrid.html:125` — [IMAGE : capture annotée de l'écran de choix de la procédure, avec les deux lignes EX-15 et EX-18 mises en évidence]
- `guides/louer-madrid-expatrie.html:161` — [IMAGE : un inventaire d'entrée annoté avec photos des pièces et relevés de compteurs]
- `he/index.html:217` — [GOOGLE_BUSINESS_PROFILE]
- `he/index.html:259` — [LINKEDIN]
- `he/index.html:539` — [LOGOS]
- `he/index.html:540` — [לוגו לקוח 1]  [לוגו לקוח 2]  [לוגו לקוח 3]  [לוגו לקוח 4]  [לוגו לקוח 5]  [לוגו לקוח 6]
- `he/index.html:541` — [TÉMOIGNAGES]
- `he/index.html:543` — [אזרחות]  [המלצה 1 — שניים־שלושה משפטים על מה ש-Mémoria שינתה במעבר]  [שם פרטי]  [תפקיד]
- `he/index.html:544` — [אזרחות]  [המלצה 2 — שניים־שלושה משפטים]  [שם פרטי]  [תפקיד]
- `he/index.html:545` — [אזרחות]  [המלצה 3 — שניים־שלושה משפטים]  [שם פרטי]  [תפקיד]
- `he/index.html:660` — [GOOGLE_BUSINESS_PROFILE]
- `he/corporate/index.html:146` — [LOGOS]
- `he/corporate/index.html:147` — [לוגו לקוח 1]  [לוגו לקוח 2]  [לוגו לקוח 3]  [לוגו לקוח 4]  [לוגו לקוח 5]  [לוגו לקוח 6]
- `he/corporate/index.html:152` — [X]
- `he/corporate/index.html:153` — [X]
- `he/corporate/index.html:154` — [ציטוט ממנהל/ת משאבי האנוש — משפט או שניים]  [תחום החברה]  [תפקיד]
- `he/corporate/index.html:163` — [TÉMOIGNAGES]
- `he/corporate/index.html:165` — [אזרחות]  [המלצה 1 — שניים־שלושה משפטים על מה ש-Mémoria שינתה במעבר]  [שם פרטי]  [תפקיד]
- `he/corporate/index.html:166` — [אזרחות]  [המלצה 2 — שניים־שלושה משפטים]  [שם פרטי]  [תפקיד]
- `he/corporate/index.html:167` — [אזרחות]  [המלצה 3 — שניים־שלושה משפטים]  [שם פרטי]  [תפקיד]
- `he/landlords/index.html:103` — [COMMISSION]
- `he/services/index.html:71` — [PRIX]
- `he/services/index.html:75` — [PRIX]
- `he/services/index.html:83` — [PRIX]
- `he/services/index.html:135` — [PRIX]
- `he/services/index.html:186` — [PRIX]
- `he/services/index.html:229` — [PRIX]
- `he/services/index.html:248` — [PRIX]
- `he/services/index.html:252` — [PRIX]
- `proprietaires/index.html:103` — [COMMISSION]
- `services/index.html:71` — [PRIX]
- `services/index.html:75` — [PRIX]
- `services/index.html:83` — [PRIX]
- `services/index.html:135` — [PRIX]
- `services/index.html:186` — [PRIX]
- `services/index.html:229` — [PRIX]
- `services/index.html:248` — [PRIX]
- `services/index.html:252` — [PRIX]
