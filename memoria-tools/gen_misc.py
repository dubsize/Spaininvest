#!/usr/bin/env python3
"""Génère les pages 404 (FR à la racine, EN, HE)."""
from layout import page

P = {
    'fr': ('/404', 'Page introuvable | Mémoria', "Cette page n'existe pas ou a été déplacée.",
           'Erreur 404', "Cette page n'existe pas, ou plus.",
           "Le lien est peut-être ancien, ou l'adresse mal recopiée. Voici où reprendre :",
           [('/', 'Accueil'), ('/services/', 'Nos services'), ('/entreprises/', 'Entreprises'), ('/proprietaires/', 'Propriétaires'), ('/guides/', 'Guides pratiques'), ('/#contact', 'Réserver un entretien gratuit')]),
    'en': ('/en/404', 'Page not found | Mémoria', 'This page does not exist or has moved.',
           'Error 404', 'This page does not exist, or no longer does.',
           'The link may be old, or the address mistyped. Here is where to pick up:',
           [('/en/', 'Home'), ('/en/services/', 'Our services'), ('/en/corporate/', 'Corporate'), ('/en/landlords/', 'Landlords'), ('/en/guides/', 'Practical guides'), ('/en/#contact', 'Book a free call')]),
    'he': ('/he/404', 'הדף לא נמצא | Mémoria', 'הדף הזה לא קיים או שהועבר.',
           'שגיאה 404', 'הדף הזה לא קיים, או כבר לא קיים.',
           'ייתכן שהקישור ישן או שהכתובת הוקלדה לא נכון. מכאן אפשר להמשיך:',
           [('/he/', 'דף הבית'), ('/he/services/', 'השירותים שלנו'), ('/he/corporate/', 'לחברות'), ('/he/landlords/', 'לבעלי נכסים'), ('/he/guides/', 'מדריכים'), ('/he/#contact', 'לקבוע שיחה חינם')]),
}

for lang, (url, title, desc, eyebrow, h1, lead, links) in P.items():
    items = '\n'.join(f'        <li><a href="{h}">{t}</a></li>' for h, t in links)
    body = f'''
<section class="art-hero">
  <div class="narrow">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{h1}</h1>
    <p class="standfirst">{lead}</p>
  </div>
</section>
<article>
  <div class="narrow">
    <ul>
{items}
    </ul>
  </div>
</article>
'''
    page(lang, url, title, desc, body, alts={'fr': '/', 'en': '/en/', 'he': '/he/'}, robots='noindex')
