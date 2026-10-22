"""Gabarit commun des pages générées (services, entreprises, propriétaires, guides…).

Chaque page générée est un fichier HTML statique autonome : ce module ne sert
qu'à écrire en-tête, pied de page et bannière cookies de façon identique.
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memoria')

FONTS = {
    'fr': 'https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Karla:ital,wght@0,400;0,500;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap',
    'he': 'https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500&family=Assistant:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap',
}
FONTS['en'] = FONTS['fr']

HOME = {'fr': '/', 'en': '/en/', 'he': '/he/'}

T = {
    'fr': dict(
        services=('/services/', 'Services'), corporate=('/entreprises/', 'Entreprises'),
        landlords=('/proprietaires/', 'Propriétaires'), guides=('/guides/', 'Guides'),
        quote='Devis entreprise', cta='Entretien gratuit', contact='/#contact',
        copy='© 2026 Mémoria — Star Alliance Consulting S.L., Madrid. Relocation & destination services.',
        legal=[('/legal/mentions-legales', 'Mentions légales'), ('/legal/politique-confidentialite', 'Confidentialité'),
               ('/legal/politique-cookies', 'Cookies'), ('/legal/conditions-generales', 'CGV')],
        cookie="Ce site utilise uniquement des cookies techniques nécessaires à son fonctionnement. Aucun cookie publicitaire ou d'analyse n'est déposé sans votre consentement.",
        cookie_more=('/legal/politique-cookies', 'En savoir plus sur les cookies'),
        reject='Refuser les cookies non essentiels', accept='Tout accepter', skip='Aller au contenu',
        cookie_info="Ce site ne dépose aucun cookie publicitaire ni de mesure d'audience. <a href='/legal/politique-cookies'>Politique cookies</a>",
    ),
    'en': dict(
        services=('/en/services/', 'Services'), corporate=('/en/corporate/', 'Corporate'),
        landlords=('/en/landlords/', 'Landlords'), guides=('/en/guides/', 'Guides'),
        quote='Corporate quote', cta='Free consultation', contact='/en/#contact',
        copy='© 2026 Mémoria — Star Alliance Consulting S.L., Madrid. Relocation & destination services.',
        legal=[('/en/legal/legal-notice', 'Legal notice'), ('/en/legal/privacy-policy', 'Privacy'),
               ('/en/legal/cookie-policy', 'Cookies'), ('/en/legal/terms', 'Terms')],
        cookie='This site only uses technical cookies necessary for it to work. No advertising or analytics cookies are set without your consent.',
        cookie_more=('/en/legal/cookie-policy', 'Learn more about cookies'),
        reject='Reject non-essential', accept='Accept all', skip='Skip to content',
        cookie_info="This site sets no advertising or analytics cookies. <a href='/en/legal/cookie-policy'>Cookie policy</a>",
    ),
    'he': dict(
        services=('/he/services/', 'שירותים'), corporate=('/he/corporate/', 'לחברות'),
        landlords=('/he/landlords/', 'לבעלי נכסים'), guides=('/he/guides/', 'מדריכים'),
        quote='הצעת מחיר לחברות', cta='שיחת ייעוץ חינם', contact='/he/#contact',
        copy='© 2026 Mémoria — Star Alliance Consulting S.L., מדריד. רילוקיישן ושירותי Destination.',
        legal=[('/he/legal/legal-notice', 'תנאים משפטיים'), ('/he/legal/privacy-policy', 'פרטיות'),
               ('/he/legal/cookie-policy', 'עוגיות'), ('/he/legal/terms', 'תנאי שירות')],
        cookie='האתר משתמש רק בעוגיות טכניות הנחוצות לפעולתו. שום עוגיית פרסום או אנליטיקה לא נשמרת ללא הסכמתכם.',
        cookie_more=('/he/legal/cookie-policy', 'מידע נוסף על עוגיות'),
        reject='לדחות עוגיות לא חיוניות', accept='לאשר הכל', skip='דלג לתוכן',
        cookie_info="האתר אינו שומר עוגיות פרסום או מדידה. <a href='/he/legal/cookie-policy'>מדיניות עוגיות</a>",
    ),
}


def lang_switch(lang, alts):
    out = []
    for l, label in (('fr', 'FR'), ('en', 'EN'), ('he', 'עב')):
        href = alts.get(l, HOME[l])
        cls = ' class="active" aria-current="true"' if l == lang else ''
        out.append(f'<a{cls} href="{href}" hreflang="{l}" lang="{l}">{label}</a>')
    return '<span class="lang">' + ''.join(out) + '</span>'


def header(lang, alts, current=None):
    t = T[lang]
    links = []
    for key in ('services', 'corporate', 'landlords', 'guides'):
        href, label = t[key]
        cur = ' aria-current="page"' if key == current else ''
        links.append(f'<a class="nav-txt" href="{href}"{cur}>{label}</a>')
    return f'''<a class="skip-link" href="#main">{t['skip']}</a>
<header>
  <div class="nav">
    <a class="logo" href="{HOME[lang]}"><img src="/logo/memoria-mark.svg" width="30" height="30" alt="">Mémoria<span>.</span></a>
    <nav class="nav-right" aria-label="Navigation">
      {' '.join(links)}
      {lang_switch(lang, alts)}
      <a class="btn-nav-ghost" href="{t['corporate'][0]}#devis">{t['quote']}</a>
      <a class="btn-nav" href="{t['contact']}">{t['cta']}</a>
    </nav>
  </div>
</header>'''


def footer(lang):
    t = T[lang]
    nav = ' · '.join(f'<a href="{t[k][0]}">{t[k][1]}</a>' for k in ('services', 'corporate', 'landlords', 'guides'))
    legal = ' · '.join(f'<a href="{h}">{l}</a>' for h, l in t['legal'])
    return f'''<footer>
  <div class="container">
    <p>{t['copy']}</p>
    <p class="foot-nav">{nav}</p>
    <p>{legal}</p>
    <p class="foot-info">{t['cookie_info']}</p>
  </div>
</footer>'''


def page(lang, url, title, description, body, alts=None, current=None, head_extra='', robots=None):
    """Écrit la page `url` (ex. '/en/services/') et renvoie son chemin."""
    alts = dict(alts or {})
    alts.setdefault(lang, url)
    dir_attr = ' dir="rtl"' if lang == 'he' else ''
    robots_tag = f'\n<meta name="robots" content="{robots}">' if robots else ''
    html = f'''<!DOCTYPE html>
<html lang="{lang}"{dir_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<title>{title}</title>
<meta name="description" content="{description}">{robots_tag}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS[lang]}" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="{FONTS[lang]}" rel="stylesheet"></noscript>
<link rel="stylesheet" href="/guides.css">
<link rel="stylesheet" href="/site-v2.css">
<script defer data-domain="memoriamadrid.com" src="https://plausible.io/js/script.outbound-links.js"></script>{head_extra}
</head>
<body>

{header(lang, alts, current)}

<main id="main">
{body.strip()}
</main>

{footer(lang)}

<script src="/site-v2.js" defer></script>
</body>
</html>
'''
    if url.endswith('/'):
        path = os.path.join(ROOT, url.lstrip('/'), 'index.html')
    else:
        path = os.path.join(ROOT, url.lstrip('/') + '.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(html)
    return path
