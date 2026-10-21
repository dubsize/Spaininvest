# Format des fragments de guides Mémoria

Un fichier par guide et par langue : memoria-tools/guides/<lang>/<slug>.html
Le générateur (memoria-tools/gen_guides.py) ajoute en-tête, hero, CTA, « à lire ensuite »,
date de mise à jour et pied de page. Le fragment ne contient QUE :

1. Un en-tête de métadonnées dans un commentaire HTML, une clé par ligne, valeurs sur une seule ligne :

<!--
title: <balise title, ~60-70 caractères, finit par " | Mémoria">
description: <meta description, 140-170 caractères>
eyebrow: Guide · <rubrique>
h1: <titre visible>
standfirst: <chapeau, 1-2 phrases>
meta: <LECTURE : 8 MIN>|<NIVEAU : ESSENTIEL>   (EN : READING TIME: 8 MIN|LEVEL: ESSENTIAL ; HE : זמן קריאה: 8 דק׳|רמה: חיוני)
tag: <rubrique courte pour la carte d'index>
teaser: <une à deux phrases pour la carte d'index>
updated: <date, ex. 21 octobre 2026 / 21 October 2026 / 21 באוקטובר 2026>
-->

2. Le corps de l'article, dans cet ordre :
   - <div class="toc"><p>Au sommaire</p><ol><li><a href="#id">…</a></li>…</ol></div>
     (EN : "In this guide" ; HE : "בתוכן")
   - des sections <h2 id="…">…</h2> avec <p>, <ul>, <ol>, <h3>
   - encadrés : <div class="callout"><p>…</p></div> ; mise en garde : <div class="callout warn"><p>…</p></div>
   - tableaux : <table class="datatable"><tr><th>…</th><th>…</th></tr><tr><td>…</td><td>…</td></tr></table>
   - une section FAQ en dernier : <h2 id="faq">Questions fréquentes</h2> puis des paires
     <p class="faq-q">Question ?</p><p>Réponse.</p>
   NE PAS inclure : CTA, « à lire ensuite », date de mise à jour, header, footer.

Liens internes : URL sans .html. Pages existantes :
  FR : /services/ (ancres #logement #installation #immigration #ecoles #vehicules #depart), /entreprises/, /proprietaires/, /#contact
       /guides/nie-avant-le-depart, /guides/empadronamiento-madrid, /guides/certificat-numerique-clave,
       /guides/scolariser-madrid-hors-campagne, /guides/cita-previa-nie-certificat-ue-madrid,
       /guides/louer-madrid-expatrie, /guides/electricite-gaz-eau-madrid
  EN : /en/services/ (mêmes ancres), /en/corporate/, /en/landlords/, /en/#contact
       /en/guides/nie-before-you-move, /en/guides/empadronamiento-madrid, /en/guides/digital-certificate-clave,
       /en/guides/school-enrolment-madrid-mid-year, /en/guides/cita-previa-nie-eu-certificate-madrid,
       /en/guides/renting-in-madrid-as-an-expat, /en/guides/electricity-gas-water-madrid
  HE : /he/services/, /he/corporate/, /he/landlords/, /he/#contact, /he/guides/nie-before-you-move,
       /he/guides/empadronamiento-madrid (les autres guides n'existent pas en hébreu : lier vers la version EN)

Règles éditoriales (impératives) :
- Textes réels, concrets, ton direct, zéro jargon marketing, zéro lorem ipsum.
- Typographie : FR guillemets « » avec espace insécable (&nbsp;) et espaces insécables avant ; : ? ! ;
  EN guillemets “ ” ; HE guillemets ״ ״ ou " ", termes espagnols conservés en caractères latins.
- UTF-8 direct (pas besoin d'entités HTML, sauf &nbsp; et &amp;).
- Ne JAMAIS promettre de « garantir » un rendez-vous administratif ni un délai officiel. Formuler
  « nous gérons la prise de rendez-vous », « selon les créneaux ouverts par l'administration ».
- Mémoria n'est ni gestor colegiado ni avocat : visas non-UE, permis de travail, contentieux =
  « coordonnés avec notre avocat partenaire ».
- Exactitude juridique : si un chiffre, un montant ou une date n'est pas certain, rester général et
  inviter à vérifier la source officielle ; ne jamais inventer de numéro de formulaire, d'adresse de
  bureau ou d'URL officielle. Sites officiels citables sans URL précise : sede.administracionespublicas.gob.es,
  madrid.es, comunidad.madrid, sede.fnmt.gob.es, agenciatributaria.es, seg-social.es, dgt.es, ine.es.
- Pas d'images. Si une image serait utile : [IMAGE : description] dans un <p>.
- Longueur : 1 400 à 2 200 mots par guide (comme les guides existants), 5 à 8 sections h2 + FAQ (4 à 6 questions).
