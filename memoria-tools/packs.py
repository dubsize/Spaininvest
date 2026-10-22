"""Packs particuliers (grille v2) : tableau comparatif à trois colonnes.

Utilisé par gen_services.py (section #packs) et inséré sur les trois accueils.
Prix TTC. Le Pack Installation reste proposé seul (ligne sous le tableau).
"""

# (clé, Essentiel, Logement, Complet)
ROWS = [
    ('ue', 1, 0, 1), ('padron', 1, 0, 1), ('secu', 1, 0, 1), ('banque', 1, 0, 1),
    ('tsi', 0, 0, 1), ('clave', 0, 0, 1),
    ('search', 0, 1, 1), ('keys', 0, 1, 1), ('utilities', 0, 1, 1), ('internet', 0, 1, 1),
]

T = {
    'fr': dict(
        eyebrow='Packs particuliers', h2='Trois façons de commencer',
        lead="Les démarches seules, le logement seul, ou les deux. Prix TTC, publiés, sans surprise : les taxes officielles sont refacturées à l'euro près.",
        cols=[('Essentiel', 'Les papiers', '590 €', 'couple 890 €'),
              ('Logement', 'Le toit', '1 790 €', 'une personne ou une famille'),
              ('Complet', 'Tout, du bail aux papiers', '2 490 €', 'famille 2 890 €')],
        rows=dict(ue='Certificat UE (« NIE vert »)', padron='Empadronamiento', secu='Numéro de sécurité sociale', banque='Compte bancaire',
                  tsi='Carte sanitaire', clave='Cl@ve', search="Recherche de logement (jusqu'à 6 visites)",
                  keys='Remise des clés et état des lieux photo', utilities='Électricité, gaz, eau', internet='Internet et mobile'),
        yes='Inclus', no='Non inclus', ttc='TTC', cta='Réserver un entretien', contact='/#contact',
        install='<strong>Pack Installation seul</strong> (les huit démarches de la colonne Complet, sans le logement) : 890 € TTC, famille 1 190 € TTC.',
        fine="Famille : deux adultes et inscription scolaire des enfants. Le briefing pré-arrivée (190 €) est déduit de tout pack signé. Urgence (moins de 7 jours) : +50 %.",
        caption='Comparatif des packs Essentiel, Logement et Complet',
    ),
    'en': dict(
        eyebrow='Packs for individuals', h2='Three ways to start',
        lead='The paperwork only, the home only, or both. Published prices including VAT, no surprises: official fees are passed on at cost.',
        cols=[('Essential', 'The paperwork', '€590', 'couple €890'),
              ('Housing', 'A roof', '€1,790', 'one person or a family'),
              ('Complete', 'Everything, lease to paperwork', '€2,490', 'family €2,890')],
        rows=dict(ue='EU certificate (“green NIE”)', padron='Empadronamiento', secu='Social security number', banque='Bank account',
                  tsi='Health card', clave='Cl@ve', search='Home search (up to 6 viewings)',
                  keys='Key handover and photo inventory', utilities='Electricity, gas, water', internet='Internet and mobile'),
        yes='Included', no='Not included', ttc='incl. VAT', cta='Book a call', contact='/en/#contact',
        install='<strong>Settling-In Pack on its own</strong> (the eight procedures of the Complete column, without the home search): €890 incl. VAT, family €1,190.',
        fine='Family: two adults plus school enrolment. The pre-arrival briefing (€190) is deducted from any pack you sign. Rush jobs (under 7 days): +50%.',
        caption='Comparison of the Essential, Housing and Complete packs',
    ),
    'he': dict(
        eyebrow='חבילות ללקוחות פרטיים', h2='שלוש דרכים להתחיל',
        lead='רק הניירת, רק הדירה, או שניהם. מחירים גלויים כולל מע״מ, בלי הפתעות: אגרות רשמיות לפי העלות בפועל.',
        cols=[('בסיס', 'הניירת', '€590', 'זוג €890'),
              ('דיור', 'קורת גג', '€1,790', 'ליחיד או למשפחה'),
              ('מלאה', 'הכל, מהחוזה ועד הניירת', '€2,490', 'משפחה €2,890')],
        rows=dict(ue='תעודת רישום אירופית (״NIE ירוק״)', padron='פדרון', secu='מספר ביטוח לאומי', banque='חשבון בנק',
                  tsi='כרטיס בריאות', clave='Cl@ve', search='חיפוש דירה (עד 6 צפיות)',
                  keys='מסירת מפתחות ופרוטוקול עם תמונות', utilities='חשמל, גז, מים', internet='אינטרנט וסלולר'),
        yes='כלול', no='לא כלול', ttc='כולל מע״מ', cta='לקבוע שיחה', contact='/he/#contact',
        install='<strong>חבילת קליטה בלבד</strong> (שמונת ההליכים של העמודה ״מלאה״, בלי חיפוש דירה): €890 כולל מע״מ, משפחה €1,190.',
        fine='משפחה: שני מבוגרים ורישום הילדים לבית ספר. התדריך לפני ההגעה (€190) מקוזז מכל חבילה. דחוף (פחות מ-7 ימים): תוספת 50%.',
        caption='השוואה בין חבילות בסיס, דיור ומלאה',
    ),
}


def table(lang):
    t = T[lang]
    head = ''.join(f'<th scope="col"><span class="pk-name">{n}</span><span class="pk-sub">{sub}</span>'
                   f'<span class="pk-price">{price} <small>{t["ttc"]}</small></span><span class="pk-alt">{alt}</span></th>'
                   for n, sub, price, alt in t['cols'])
    mark = lambda v: (f'<td class="pk-yes"><span aria-hidden="true">✓</span><span class="sr">{t["yes"]}</span></td>' if v
                      else f'<td class="pk-no"><span aria-hidden="true">—</span><span class="sr">{t["no"]}</span></td>')
    body = '\n'.join(f'        <tr><th scope="row">{t["rows"][k]}</th>{mark(a)}{mark(b)}{mark(c)}</tr>' for k, a, b, c in ROWS)
    cta = ''.join(f'<td><a href="{t["contact"]}">{t["cta"]}</a></td>' for _ in t['cols'])
    return f'''<div class="pk-wrap">
      <table class="pk-table">
        <caption class="sr">{t['caption']}</caption>
        <thead><tr><td></td>{head}</tr></thead>
        <tbody>
{body}
        <tr class="pk-cta"><th scope="row"></th>{cta}</tr>
        </tbody>
      </table>
    </div>
    <p class="pk-install">{t['install']}</p>
    <p class="pk-fine">{t['fine']}</p>'''


def section_services(lang):
    """Section pour la page /services/ (gabarit guides.css)."""
    t = T[lang]
    return f'''  <section class="fam" id="packs" aria-labelledby="h-packs">
    <p class="fam-term">{t['eyebrow']}</p>
    <h2 id="h-packs">{t['h2']}</h2>
    <p class="fam-hook">{t['lead']}</p>
    {table(lang)}
  </section>'''


def section_home(lang):
    """Section pour les accueils (styles inline + site-v2.css)."""
    t = T[lang]
    return f'''<!-- PACKS PARTICULIERS -->
<section class="carte" id="packs">
  <div class="container">
    <p class="eyebrow reveal">{t['eyebrow']}</p>
    <h2 class="reveal">{t['h2']}</h2>
    <p class="lead reveal">{t['lead']}</p>
    {table(lang)}
  </div>
</section>
'''
