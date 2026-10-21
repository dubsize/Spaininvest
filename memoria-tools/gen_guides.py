#!/usr/bin/env python3
"""Génère les guides et les index /guides/, /en/guides/, /he/guides/
à partir des fragments memoria-tools/guides/<lang>/<slug>.html (voir guides/FORMAT.md)."""
import os
import re

from layout import page

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = {'fr': '/guides/', 'en': '/en/guides/', 'he': '/he/guides/'}

# Même guide dans chaque langue, dans l'ordre d'affichage des index.
GUIDES = [
    ('cita', {'fr': 'cita-previa-nie-certificat-ue-madrid', 'en': 'cita-previa-nie-eu-certificate-madrid'}),
    ('nie', {'fr': 'nie-avant-le-depart', 'en': 'nie-before-you-move', 'he': 'nie-before-you-move'}),
    ('padron', {'fr': 'empadronamiento-madrid', 'en': 'empadronamiento-madrid', 'he': 'empadronamiento-madrid'}),
    ('louer', {'fr': 'louer-madrid-expatrie', 'en': 'renting-in-madrid-as-an-expat'}),
    ('energie', {'fr': 'electricite-gaz-eau-madrid', 'en': 'electricity-gas-water-madrid'}),
    ('clave', {'fr': 'certificat-numerique-clave', 'en': 'digital-certificate-clave'}),
    ('ecole', {'fr': 'scolariser-madrid-hors-campagne', 'en': 'school-enrolment-madrid-mid-year'}),
]
RELATED = {
    'cita': ['nie', 'padron', 'clave'],
    'nie': ['cita', 'padron', 'clave'],
    'padron': ['louer', 'cita', 'ecole'],
    'louer': ['energie', 'padron', 'cita'],
    'energie': ['louer', 'clave'],
    'clave': ['cita', 'padron', 'energie'],
    'ecole': ['padron', 'louer'],
}
# Service du catalogue mis en avant sous chaque guide.
SERVICE = {'cita': 'installation', 'nie': 'installation', 'padron': 'installation', 'louer': 'logement',
           'energie': 'installation', 'clave': 'installation', 'ecole': 'ecoles'}

T = {
    'fr': dict(
        related='À lire ensuite', svc_link='Le service correspondant dans notre catalogue →',
        updated='Guide mis à jour le <span>{d}</span> — les règles administratives espagnoles évoluent ; vérifiez les points critiques avant d\'agir.',
        cta_h='Vous préférez qu\'on s\'en occupe ?',
        cta_p='Trente minutes en visio, sans engagement. Vous repartez avec un plan clair et un devis précis, que vous travailliez avec nous ou non.',
        cta=('/#contact', 'Réserver un entretien gratuit'), cta2=('/entreprises/', 'Vous êtes une entreprise ?'),
        idx_title='Guides pratiques — s\'installer à Madrid | Mémoria',
        idx_desc='Guides gratuits pour s\'installer à Madrid : NIE et cita previa, empadronamiento, location et bail LAU, électricité et gaz, Cl@ve, écoles. Écrits à partir de dossiers réels.',
        idx_eyebrow='Guides pratiques', idx_h1='Ce qu\'on aurait aimé savoir avant d\'arriver',
        idx_stand='Des guides détaillés, gratuits, écrits à partir de dossiers réels. Sans jargon, sans approximation, et sans faire semblant que tout est simple.',
        idx_cta_h='Une question sur votre situation ?', other=None,
    ),
    'en': dict(
        related='Read next', svc_link='The matching service in our catalogue →',
        updated='Guide updated on <span>{d}</span> — Spanish administrative rules change; check the critical points before acting.',
        cta_h='Would you rather we handled it?',
        cta_p='Thirty minutes on Zoom, no commitment. You leave with a clear plan and a precise quote, whether you work with us or not.',
        cta=('/en/#contact', 'Book a free call'), cta2=('/en/corporate/', 'Relocating an employee?'),
        idx_title='Practical guides — moving to Madrid | Mémoria',
        idx_desc='Free guides to moving to Madrid: NIE and cita previa, empadronamiento, renting and the LAU lease, electricity and gas, Cl@ve, schools. Written from real cases.',
        idx_eyebrow='Practical guides', idx_h1='What we wish we had known before arriving',
        idx_stand='Detailed, free guides written from real cases. No jargon, no guesswork, and no pretending it is all simple.',
        idx_cta_h='A question about your situation?', other=None,
    ),
    'he': dict(
        related='כדאי לקרוא גם', svc_link='השירות המתאים בקטלוג שלנו ←',
        updated='המדריך עודכן ב-<span>{d}</span> — הכללים המנהליים בספרד משתנים; בדקו את הנקודות הקריטיות לפני שפועלים.',
        cta_h='מעדיפים שנטפל בזה בשבילכם?',
        cta_p='שלושים דקות בזום, בלי התחייבות. תצאו עם תוכנית ברורה והצעת מחיר מדויקת, בין אם תעבדו איתנו ובין אם לא.',
        cta=('/he/#contact', 'לקבוע שיחה חינם'), cta2=('/he/corporate/', 'מעבירים עובד?'),
        idx_title='מדריכים מעשיים — מעבר למדריד | Mémoria',
        idx_desc='מדריכים חינמיים למעבר למדריד: NIE לפני הטיסה ופדרון (רישום תושבות). נכתבו מתוך תיקים אמיתיים.',
        idx_eyebrow='מדריכים מעשיים', idx_h1='מה שהיינו רוצים לדעת לפני שהגענו',
        idx_stand='מדריכים מפורטים וחינמיים, שנכתבו מתוך תיקים אמיתיים. בלי ז׳רגון, בלי הערכות, ובלי להעמיד פנים שהכל פשוט.',
        idx_cta_h='שאלה על המצב שלכם?',
        other=('/en/guides/', 'מדריכים נוספים זמינים באנגלית: תורים (cita previa), שכירות, חשמל וגז, Cl@ve ובתי ספר ←'),
    ),
}

SERVICES = {'fr': '/services/', 'en': '/en/services/', 'he': '/he/services/'}


def read_fragment(lang, slug):
    path = os.path.join(HERE, 'guides', lang, slug + '.html')
    if not os.path.exists(path):
        return None
    src = open(path, encoding='utf-8').read()
    m = re.match(r'\s*<!--(.*?)-->\s*(.*)', src, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(':')
        meta[k.strip()] = v.strip()
    meta['body'] = m.group(2).strip()
    return meta


def url(lang, slug):
    return BASE[lang] + slug


def build_guide(key, slugs, lang, frags):
    g = frags[(key, lang)]
    t = T[lang]
    alts = {l: url(l, s) for l, s in slugs.items() if (key, l) in frags}
    rel = []
    for rk in RELATED[key]:
        rs = dict(GUIDES)[rk]
        if (rk, lang) in frags:
            rel.append((url(lang, rs[lang]), frags[(rk, lang)]['h1']))
        elif lang == 'he' and (rk, 'en') in frags:
            rel.append((url('en', rs['en']), frags[(rk, 'en')]['h1'] + ' (English)'))
    rel_html = '\n'.join(f'        <li><a href="{h}">{ti}</a></li>' for h, ti in rel)
    meta = ''.join(f'<span>{x}</span>' for x in g['meta'].split('|'))
    body = f'''
<section class="art-hero">
  <div class="narrow">
    <p class="eyebrow">{g['eyebrow']}</p>
    <h1>{g['h1']}</h1>
    <p class="standfirst">{g['standfirst']}</p>
    <div class="art-meta">{meta}</div>
  </div>
</section>

<article>
  <div class="narrow">
    {g['body']}

    <div class="art-cta">
      <h3>{t['cta_h']}</h3>
      <p>{t['cta_p']}</p>
      <a href="{t['cta'][0]}">{t['cta'][1]}</a> <a class="ghost" href="{t['cta2'][0]}">{t['cta2'][1]}</a>
    </div>

    <div class="related">
      <p class="lbl">{t['related']}</p>
      <ul>
{rel_html}
        <li><a href="{SERVICES[lang]}#{SERVICE[key]}">{t['svc_link']}</a></li>
      </ul>
    </div>

    <p class="updated">{t['updated'].format(d=g['updated'])}</p>
  </div>
</article>
'''
    page(lang, url(lang, slugs[lang]), g['title'], g['description'], body, alts=alts, current='guides')


def build_index(lang, frags):
    t = T[lang]
    cards = []
    for key, slugs in GUIDES:
        g = frags.get((key, lang))
        if not g:
            continue
        cards.append(f'''      <a class="guide-card" href="{url(lang, slugs[lang])}">
        <span class="tag">{g['tag']}</span>
        <h2>{g['h1']}</h2>
        <p>{g['teaser']}</p>
      </a>''')
    other = f'\n    <p class="gt-all" style="margin-top:26px"><a href="{t["other"][0]}">{t["other"][1]}</a></p>' if t['other'] else ''
    body = f'''
<section class="art-hero">
  <div class="narrow">
    <p class="eyebrow">{t['idx_eyebrow']}</p>
    <h1>{t['idx_h1']}</h1>
    <p class="standfirst">{t['idx_stand']}</p>
  </div>
</section>

<article>
  <div class="container">
    <div class="guides-grid">
{chr(10).join(cards)}
    </div>{other}

    <div class="art-cta">
      <h3>{t['idx_cta_h']}</h3>
      <p>{t['cta_p']}</p>
      <a href="{t['cta'][0]}">{t['cta'][1]}</a> <a class="ghost" href="{t['cta2'][0]}">{t['cta2'][1]}</a>
    </div>
  </div>
</article>
'''
    page(lang, BASE[lang], t['idx_title'], t['idx_desc'], body, alts=BASE, current='guides')


def main():
    frags = {}
    for key, slugs in GUIDES:
        for lang, slug in slugs.items():
            f = read_fragment(lang, slug)
            if f:
                frags[(key, lang)] = f
    for key, slugs in GUIDES:
        for lang in slugs:
            if (key, lang) in frags:
                build_guide(key, slugs, lang, frags)
    for lang in ('fr', 'en', 'he'):
        build_index(lang, frags)
    print('guides générés :', sorted(f'{l}/{k}' for k, l in frags))


if __name__ == '__main__':
    main()
