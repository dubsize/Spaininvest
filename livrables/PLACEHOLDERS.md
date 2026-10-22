# Contenus à fournir — Mémoria

Le site est **en ligne depuis le 22 octobre 2026** sans aucun « […] » visible : ce qui n'était pas
prêt a été masqué ou remplacé par une formulation neutre. Voici comment activer chaque élément
quand vous avez l'information. Après une modification dans `memoria-tools/`, relancer :

```
python3 memoria-tools/gen_services.py && python3 memoria-tools/gen_corporate.py && python3 memoria-tools/gen_landlords.py && python3 memoria-tools/gen_guides.py && python3 memoria-tools/gen_misc.py && python3 memoria-tools/seo.py && python3 memoria-tools/qa.py
```

puis redéployer le dossier `memoria/`.

| Élément | État en ligne | Pour l'activer |
|---|---|---|
| Numéro WhatsApp | bouton masqué | `memoria/site-v2.js` ligne 5 : remplacer `[WHATSAPP]` par le numéro international, chiffres seulement (ex. 34600123456). Le bouton apparaît alors sur toutes les pages. |
| Prix de 8 services (briefing pré-arrivée, journée d'orientation, état des lieux d'entrée, permis SER, cartographie scolaire, renting, clôture des suministros, baja du padrón) | « Sur devis » | `memoria-tools/services_data.py` : sur le service concerné, remplacer `price=FROM_TBD` par `price=eur(XXX)` (affiche « XXX € », « €XXX »). |
| Commission propriétaire | « communiquée sur demande » | `memoria-tools/gen_landlords.py` lignes 36, 83, 130. |
| Logos clients, étude de cas, témoignages | blocs masqués (FAQ entreprises visible) | `memoria-tools/proof.py` : remplir les `[…]` (logos avec accord écrit, chiffres `[X]`, citation RH, trois témoignages réels), puis `SHOW_PROOF = True`. Les blocs reviennent sur la page Entreprises ; pour les accueils, réinsérer `home_proof(lang)` avant la FAQ (voir l'historique git, commit T6). |
| LinkedIn, fiche Google Business | non affichés | ajouter `"sameAs": ["URL_LINKEDIN", "URL_FICHE_GOOGLE"]` dans le JSON-LD des trois accueils ; lien « Avis Google » prévu en commentaire dans leur pied de page. |
| Assurance RC pro, contact nommé | absents de la fiche fournisseur | `memoria/docs/memoria-capability-statement.html` : commentaires `[POLICE]` et `[NOM DU CONTACT], [FONCTION], [TÉLÉPHONE]`. |
| Visuel de partage réseaux sociaux | absent (cartes de partage sans image) | déposer `memoria/og-image.png` (1200×630), décommenter les lignes `og:image` / `twitter:image` dans `memoria-tools/seo.py`, relancer `seo.py`. |
