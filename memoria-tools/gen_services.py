#!/usr/bin/env python3
"""Génère /services/, /en/services/, /he/services/ à partir de services_data.py."""
from layout import page
from services_data import BADGES, FAMILIES, EXTRAS

URLS = {'fr': '/services/', 'en': '/en/services/', 'he': '/he/services/'}

TXT = {
    'fr': dict(
        title='Services de relocation à Madrid — catalogue complet | Mémoria',
        desc="Relocation à Madrid : recherche de logement, installation (NIE, padrón, carte sanitaire), immigration, écoles, véhicules et départ. Ce que nous faisons, documents, délais et prix.",
        eyebrow='Catalogue · Relocation à Madrid',
        h1="Tout ce qu'une installation à Madrid demande, en six familles",
        stand="Nous reprenons la classification des professionnels de la relocation, pour que vous, votre employeur ou votre société de relocation sachiez exactement ce qui est couvert. Prix publiés pour les particuliers ; pour les entreprises, devis sur mesure facturé à l'employeur.",
        legend='<span class="lg lg-we">Nous y allons</span> nous nous déplaçons à votre place, avec une autorisation signée. <span class="lg lg-you">Présence requise</span> la loi impose votre présence : nous préparons tout et vous accompagnons, mais vous signez en personne. <span class="lg tl-remote">À distance</span> tout se fait sans déplacement. <span class="lg tl-partner">Avocat partenaire</span> démarche réglementée, déposée par notre avocat partenaire et coordonnée par nous.',
        jump='Aller à une famille',
        labels=('Ce que nous faisons', 'Ce que vous faites', 'Documents nécessaires', 'Délai indicatif'),
        fine="Prix particuliers TTC (TVA 21 % incluse) ; entreprises : devis HT. À la carte, trois démarches ou plus : −15 % (hors packs, non cumulable). Taxes officielles en sus, refacturées à l'euro près. Déplacements inclus dans Madrid. Urgence (moins de 7 jours) : +50 %. Les délais indiqués sont ceux de notre travail ; ceux des administrations dépendent des créneaux qu'elles ouvrent, que personne ne peut garantir.",
        cta_h='Vous ne savez pas par où commencer ?',
        cta_p="Trente minutes en visio, sans engagement : vous repartez avec l'ordre des démarches et un devis précis.",
        cta1=('/#contact', 'Réserver un entretien gratuit'),
        cta2=('/entreprises/#devis', 'Demander un devis entreprise'),
        num='Famille',
    ),
    'en': dict(
        title='Relocation services in Madrid — full catalogue | Mémoria',
        desc='Relocation in Madrid: home search, settling-in (NIE, padrón, health card), immigration, schools, vehicles and departure. What we do, documents, timing and prices.',
        eyebrow='Catalogue · Relocation in Madrid',
        h1='Everything a move to Madrid takes, in six families',
        stand='We follow the relocation industry\'s own service families, so that you, your employer or your relocation management company know exactly what is covered. Published prices for individuals; for employers, a tailored quote invoiced to the company.',
        legend='<span class="lg lg-we">We go for you</span> we attend in your place with a signed authorisation. <span class="lg lg-you">You must attend</span> the law requires your presence: we prepare everything and come with you, but you sign in person. <span class="lg tl-remote">Remote</span> no travel needed. <span class="lg tl-partner">Partner lawyer</span> a regulated procedure, filed by our partner lawyer and coordinated by us.',
        jump='Jump to a family',
        labels=('What we do', 'What you do', 'Documents needed', 'Indicative timing'),
        fine='Prices for individuals include VAT (21%); companies: quotes before VAT. Three or more single procedures: −15% (packs excluded, not combinable). Official fees on top, passed on at cost. Travel within Madrid included. Rush jobs (under 7 days): +50%. Timings are for our own work; the administrations\' timings depend on the slots they release, which nobody can guarantee.',
        cta_h='Not sure where to start?',
        cta_p='Thirty minutes on Zoom, no commitment: you leave with the order of procedures and a precise quote.',
        cta1=('/en/#contact', 'Book a free call'),
        cta2=('/en/corporate/#devis', 'Request a corporate quote'),
        num='Family',
    ),
    'he': dict(
        title='שירותי רילוקיישן במדריד — הקטלוג המלא | Mémoria',
        desc='רילוקיישן למדריד: חיפוש דירה, קליטה (NIE, פדרון, כרטיס בריאות), הגירה, בתי ספר, רכב ועזיבה. מה אנחנו עושים, מסמכים, זמנים ומחירים.',
        eyebrow='קטלוג · רילוקיישן למדריד',
        h1='כל מה שמעבר למדריד דורש, בשש קטגוריות',
        stand='אנחנו משתמשים בחלוקה המקובלת בענף הרילוקיישן, כדי שאתם, המעסיק שלכם או חברת הרילוקיישן תדעו בדיוק מה כלול. מחירים גלויים ללקוחות פרטיים; לחברות — הצעת מחיר מותאמת, בחיוב המעסיק.',
        legend='<span class="lg lg-we">אנחנו הולכים במקומכם</span> מספיק ייפוי כוח חתום. <span class="lg lg-you">נדרשת נוכחות</span> החוק מחייב אתכם להתייצב: אנחנו מכינים הכל ומלווים, אבל החתימה שלכם. <span class="lg tl-remote">מרחוק</span> בלי צורך להגיע. <span class="lg tl-partner">עו״ד שותף</span> הליך מוסדר, שמוגש על ידי עורך הדין השותף ומתואם על ידינו.',
        jump='מעבר לקטגוריה',
        labels=('מה אנחנו עושים', 'מה אתם עושים', 'מסמכים נדרשים', 'זמן משוער'),
        fine='המחירים ללקוחות פרטיים כוללים מע״מ (21%); לחברות: הצעת מחיר לפני מע״מ. שלושה הליכים בודדים ומעלה: הנחה של 15% (לא כולל חבילות, לא במצטבר). אגרות רשמיות בנפרד, לפי העלות בפועל. נסיעות בתוך מדריד כלולות. דחוף (פחות מ-7 ימים): תוספת 50%. הזמנים המצוינים הם של העבודה שלנו; הזמנים של הרשויות תלויים בתורים שהן פותחות, ואף אחד לא יכול להבטיח אותם.',
        cta_h='לא בטוחים מאיפה להתחיל?',
        cta_p='שלושים דקות בזום, בלי התחייבות: תצאו עם סדר ההליכים והצעת מחיר מדויקת.',
        cta1=('/he/#contact', 'לקבוע שיחה חינם'),
        cta2=('/he/corporate/#devis', 'הצעת מחיר לחברות'),
        num='קטגוריה',
    ),
}


def service_html(s, lang, labels):
    name, do, you, docs, delay = s[lang]
    badge = ''
    if s.get('badge'):
        cls, lbl = BADGES[s['badge']]
        badge = f' <span class="tagline {cls}">{lbl[lang]}</span>'
    star = ' star' if s.get('star') else ''
    cells = ''.join(f'<div><h4>{l}</h4><p>{v}</p></div>' for l, v in zip(labels, (do, you, docs, delay)))
    return f'''      <details class="svc{star}">
        <summary><span class="svc-name"><strong>{name}</strong>{badge}</span><span class="svc-price">{s['price'][lang]}</span></summary>
        <div class="svc-body">{cells}</div>
      </details>'''


def family_html(f, lang, i, t):
    num = f"{t['num']} {i:02d} · " if i else ''
    note = f'\n    <div class="callout">{f["note"][lang]}</div>' if f.get('note') else ''
    items = '\n'.join(service_html(s, lang, t['labels']) for s in f['services'])
    return f'''  <section class="fam" id="{f['id']}" aria-labelledby="h-{f['id']}">
    <p class="fam-term">{num}{f['term']}</p>
    <h2 id="h-{f['id']}">{f['title'][lang]}</h2>
    <p class="fam-hook">{f['hook'][lang]}</p>{note}
    <div class="svc-list">
{items}
    </div>
  </section>'''


def build(lang):
    t = TXT[lang]
    fams = FAMILIES + [EXTRAS]
    chips = ''.join(f'<a href="#{f["id"]}">{f["title"][lang]}</a>' for f in fams)
    sections = '\n'.join(family_html(f, lang, i + 1 if f is not EXTRAS else 0, t) for i, f in enumerate(fams))
    body = f'''
<section class="art-hero">
  <div class="container">
    <p class="eyebrow">{t['eyebrow']}</p>
    <h1>{t['h1']}</h1>
    <p class="standfirst">{t['stand']}</p>
  </div>
</section>

<div class="container v2-wrap">
  <p class="carte-legend">{t['legend']}</p>
  <nav class="fam-nav" aria-label="{t['jump']}">{chips}</nav>
{sections}
  <p class="v2-fine">{t['fine']}</p>
  <div class="art-cta">
    <h3>{t['cta_h']}</h3>
    <p>{t['cta_p']}</p>
    <a href="{t['cta1'][0]}">{t['cta1'][1]}</a> <a class="ghost" href="{t['cta2'][0]}">{t['cta2'][1]}</a>
  </div>
</div>
'''
    page(lang, URLS[lang], t['title'], t['desc'], body, alts=URLS, current='services')


if __name__ == '__main__':
    for lang in ('fr', 'en', 'he'):
        build(lang)
