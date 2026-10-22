#!/usr/bin/env python3
"""Génère /proprietaires/, /en/landlords/, /he/landlords/ (formulaire Netlify « proprietaires »)."""
from layout import page

URLS = {'fr': '/proprietaires/', 'en': '/en/landlords/', 'he': '/he/landlords/'}

C = {
'fr': dict(
    title='Louer son bien à des expatriés à Madrid — Mémoria pour propriétaires',
    desc="Louez votre appartement ou votre maison à Madrid à des expatriés et cadres mutés : annonce bilingue, dossiers vérifiés, garanties adaptées, bail LAU bilingue, état des lieux photo.",
    eyebrow='Propriétaires · Louer à des expatriés',
    h1='Louez votre bien à des expatriés, sans les incertitudes.',
    stand="Cadres mutés, familles en relocation : des locataires solvables, mais sans historique en Espagne. Nous trouvons, vérifions, rédigeons un bail clair dans les deux langues, et restons l'interlocuteur du locataire pendant la location. Nous l'avons fait pour nous-mêmes : achat, rénovation et mise en location d'une maison à Valdebebas.",
    hero_cta='Proposer mon bien',
    do_eyebrow='Ce que nous faisons',
    do_h2='De l\'annonce à la remise des clés, puis pendant le bail',
    do=[('Annonce bilingue', "Texte en espagnol et en anglais (et français ou hébreu si utile), mise en valeur du quartier pour un public expatrié, diffusion ciblée et auprès des entreprises que nous accompagnons."),
        ('Filtrage des candidats', "Premier échange avec chaque candidat, vérification de l'adéquation (budget, durée, composition du foyer, animaux), visites groupées."),
        ('Vérification des dossiers', "Contrat de travail ou lettre de mutation, fiches de paie, identité ; contrôle de cohérence et, si l'employeur l'accepte, confirmation directe auprès des RH."),
        ('Garanties adaptées', "Pour des candidats sans historique en Espagne : aval bancaire, dépôt complémentaire, garant résident, engagement de l'employeur — dans les limites de la LAU."),
        ('Bail LAU bilingue', "Contrat conforme à la loi sur les baux urbains en vigueur, version espagnole faisant foi et traduction en regard ; inventaire du mobilier en annexe."),
        ('Fianza déposée', "Encaissement de la fianza légale et dépôt auprès de la Comunidad de Madrid, comme la réglementation l'impose."),
        ('État des lieux et remise des clés', "Inventaire pièce par pièce avec photos datées, relevé des compteurs, rapport signé par les deux parties."),
        ('Interlocuteur pendant le bail', "Le locataire nous appelle, pas vous : petites demandes, artisans, changement de titulaire des contrats, puis fin de bail et état des lieux de sortie.")],
    gu_eyebrow='Garanties',
    gu_h2='Sécuriser un candidat sans historique espagnol',
    gu_lead="Un cadre muté n'a ni nómina espagnole ancienne ni historique bancaire local. Voici ce que la loi permet de demander, et ce que nous mettons en place.",
    gu_rows=[('Fianza légale', "Un mois de loyer pour un bail d'habitation (deux pour un usage autre que l'habitation, dont la location de temporada), déposée auprès de la Comunidad de Madrid."),
             ('Garantie additionnelle', "Dépôt ou aval bancaire. Pour un bail d'habitation de cinq ans (sept si le propriétaire est une société), plafonnée à deux mois de loyer."),
             ('Garant résident', "Une personne résidant en Espagne se porte caution solidaire du locataire (fiador)."),
             ("Engagement de l'employeur", "Lettre de l'employeur, voire bail au nom de la société : la solution la plus solide pour une mutation."),
             ('Assurance loyers impayés', "Option à votre charge, souscrite après étude du dossier par l'assureur.")],
    gu_note="À savoir : la loi interdit d'exiger plus d'un mois de loyer payé d'avance. Les « six mois d'avance » parfois proposés ne sont pas une garantie que nous pouvons vous recommander.",
    fee_eyebrow='Rémunération',
    fee_h2='Une commission, à la signature seulement',
    fee=[("Commission à la signature du bail", "Montant communiqué sur demande, avant tout engagement."),
         ('Avant la signature', 'Rien à payer : annonce, visites et vérifications sont comprises.'),
         ('Pour le locataire', 'Rien : comme la loi l\'impose, les frais de gestion immobilière sont à la charge du propriétaire.')],
    fee_note="Nous ne représentons jamais les deux parties d'un même bail : un candidat que nous accompagnons dans sa recherche ne vous sera pas présenté par nous.",
    faq_h2='Questions fréquentes des propriétaires',
    faq=[('Combien de temps faut-il pour louer ?', "Pour un bien au bon prix dans un quartier recherché, deux à quatre semaines entre la mise en ligne et la signature. Nous vous donnons un avis franc sur le loyer avant de commencer."),
         ('Puis-je louer meublé, ou pour quelques mois ?', "Oui. Un bail de temporada (moins d'un an, pour un besoin temporaire du locataire) obéit à d'autres règles qu'un bail d'habitation ; nous vous indiquons lequel correspond à votre situation et à celle du candidat."),
         ("Que se passe-t-il en cas d'impayé ?", "Nous relançons immédiatement et activons les garanties prévues au bail. Si une procédure est nécessaire, elle est menée par notre avocat partenaire. C'est pour éviter d'en arriver là que la vérification des dossiers est sérieuse."),
         ('Je vis hors d\'Espagne. Est-ce un problème ?', "Non, c'est un cas fréquent : signature à distance, état des lieux sans vous, rapport photo, et le locataire a un interlocuteur sur place.")],
    form_eyebrow='Proposer mon bien',
    form_h2='Parlez-nous de votre logement',
    form_p='Nous vous répondons sous 24 h ouvrées avec un avis sur le loyer et le calendrier.',
    f=dict(name='Prénom et nom', email='Email', phone='Téléphone / WhatsApp', address='Adresse du bien', type='Type de bien',
           types=[('appartement', 'Appartement'), ('maison', 'Maison'), ('studio', 'Studio'), ('autre', 'Autre')], choose='Choisissez…',
           furnished='Meublé ?', furn=[('oui', 'Oui'), ('non', 'Non'), ('a-voir', 'À voir')],
           rent='Loyer visé (€ / mois)', avail='Disponible à partir du', message='Précisions (surface, chambres, extérieur, animaux…)', optional='(facultatif)',
           consent="J'accepte que ces données soient utilisées pour répondre à ma demande, conformément à la <a href=\"/legal/politique-confidentialite\">politique de confidentialité</a>.",
           submit='Envoyer', note='Réponse sous 24 h ouvrées. Vos informations ne sont transmises à personne.', honey='Ne pas remplir :'),
),
'en': dict(
    title='Letting your Madrid property to expats — Mémoria for landlords',
    desc='Let your flat or house in Madrid to expats and relocated professionals: bilingual listing, verified applicants, suitable guarantees, bilingual LAU lease, photo inventory.',
    eyebrow='Landlords · Letting to expats',
    h1='Let your property to expats, without the guesswork.',
    stand='Relocated executives and families: tenants who can pay, but with no track record in Spain. We find them, check them, draw up a clear lease in both languages, and stay the tenant\'s point of contact during the tenancy. We have done it for ourselves: buying, renovating and letting a house in Valdebebas.',
    hero_cta='Offer my property',
    do_eyebrow='What we do',
    do_h2='From the listing to the keys, then throughout the lease',
    do=[('Bilingual listing', 'Copy in Spanish and English (plus French or Hebrew where useful), the neighbourhood presented for an expat audience, targeted distribution, including to the employers we work with.'),
        ('Applicant screening', 'A first conversation with every applicant, fit checked (budget, length of stay, household, pets), grouped viewings.'),
        ('Application checks', 'Employment contract or assignment letter, payslips, ID; consistency checks and, where the employer agrees, direct confirmation with HR.'),
        ('Suitable guarantees', 'For applicants without a Spanish history: bank guarantee, additional deposit, resident guarantor, employer commitment — within the limits of the LAU.'),
        ('Bilingual LAU lease', 'A contract compliant with the current urban leases act, the Spanish version prevailing with a side-by-side translation; furniture inventory attached.'),
        ('Fianza deposited', 'The statutory fianza collected and lodged with the Comunidad de Madrid, as the regulations require.'),
        ('Inventory and key handover', 'Room-by-room inventory with dated photos, meter readings, report signed by both parties.'),
        ('Point of contact during the lease', 'The tenant calls us, not you: small requests, tradespeople, utility transfers, then lease end and check-out.')],
    gu_eyebrow='Guarantees',
    gu_h2='Securing an applicant with no Spanish track record',
    gu_lead='A relocated executive has no long Spanish payroll history and no local credit record. Here is what the law allows you to ask for, and what we put in place.',
    gu_rows=[('Statutory fianza', 'One month\'s rent for a residential lease (two for other uses, including seasonal lets), lodged with the Comunidad de Madrid.'),
             ('Additional guarantee', 'Deposit or bank guarantee. For a five-year residential lease (seven if the landlord is a company), capped at two months\' rent.'),
             ('Resident guarantor', 'Someone living in Spain stands as joint guarantor for the tenant (fiador).'),
             ('Employer commitment', 'A letter from the employer, or even a lease in the company\'s name: the strongest option for a relocation.'),
             ('Rent default insurance', 'Optional, at your expense, issued after the insurer reviews the application.')],
    gu_note='Worth knowing: the law prohibits requiring more than one month\'s rent paid in advance. The “six months upfront” sometimes offered is not a guarantee we can recommend.',
    fee_eyebrow='Fees',
    fee_h2='One commission, on signing only',
    fee=[('Commission on signing the lease', 'Amount provided on request, before any commitment.'),
         ('Before signing', 'Nothing to pay: listing, viewings and checks are included.'),
         ('For the tenant', 'Nothing: as the law requires, property management fees are borne by the landlord.')],
    fee_note='We never represent both sides of the same lease: an applicant we are helping with their search will not be put forward to you by us.',
    faq_h2='Landlords\' questions',
    faq=[('How long does it take to let?', 'For a fairly priced property in a sought-after area, two to four weeks from listing to signing. We give you a frank view on the rent before we start.'),
         ('Can I let furnished, or for a few months?', 'Yes. A seasonal lease (temporada: under a year, for a temporary need of the tenant) follows different rules from a residential lease; we tell you which one fits your situation and the applicant\'s.'),
         ('What if the rent is not paid?', 'We chase immediately and call on the guarantees in the lease. If proceedings are needed, our partner lawyer handles them. Thorough checks are there to avoid getting that far.'),
         ('I live outside Spain. Is that a problem?', 'No, it is common: remote signing, inventory without you, photo report, and the tenant has someone on the ground.')],
    form_eyebrow='Offer my property',
    form_h2='Tell us about your home',
    form_p='We reply within 24 working hours with a view on the rent and the timeline.',
    f=dict(name='Full name', email='Email', phone='Phone / WhatsApp', address='Property address', type='Property type',
           types=[('appartement', 'Flat'), ('maison', 'House'), ('studio', 'Studio'), ('autre', 'Other')], choose='Choose…',
           furnished='Furnished?', furn=[('oui', 'Yes'), ('non', 'No'), ('a-voir', 'Open to both')],
           rent='Target rent (€ / month)', avail='Available from', message='Details (size, bedrooms, outdoor space, pets…)', optional='(optional)',
           consent='I agree that this data may be used to respond to my request, in accordance with the <a href="/en/legal/privacy-policy">privacy policy</a>.',
           submit='Send', note='Reply within 24 working hours. Your details are never shared.', honey='Do not fill:'),
),
'he': dict(
    title='השכרת נכס במדריד לתושבי חוץ — Mémoria לבעלי נכסים',
    desc='השכירו את הדירה או הבית שלכם במדריד לתושבי חוץ ולמנהלים מועברים: מודעה דו־לשונית, מועמדים נבדקים, ערבויות מתאימות, חוזה LAU דו־לשוני, פרוטוקול עם תמונות.',
    eyebrow='בעלי נכסים · השכרה לתושבי חוץ',
    h1='השכירו את הנכס לתושבי חוץ, בלי ניחושים.',
    stand='מנהלים מועברים ומשפחות ברילוקיישן: שוכרים עם יכולת תשלום, אבל בלי היסטוריה בספרד. אנחנו מוצאים אותם, בודקים, מכינים חוזה ברור בשתי שפות, ונשארים איש הקשר של השוכר לאורך השכירות. עשינו את זה בעצמנו: קנייה, שיפוץ והשכרה של בית ב-Valdebebas.',
    hero_cta='להציע את הנכס',
    do_eyebrow='מה אנחנו עושים',
    do_h2='מהמודעה ועד המפתחות, ואחר כך לאורך החוזה',
    do=[('מודעה דו־לשונית', 'טקסט בספרדית ובאנגלית (ובעברית או צרפתית לפי הצורך), הצגת השכונה לקהל תושבי חוץ, הפצה ממוקדת — כולל לחברות שאנחנו מלווים.'),
        ('סינון מועמדים', 'שיחה ראשונה עם כל מועמד, בדיקת התאמה (תקציב, משך, הרכב המשפחה, חיות), צפיות מרוכזות.'),
        ('בדיקת תיקים', 'חוזה עבודה או מכתב העברה, תלושי שכר, תעודה מזהה; בדיקת עקביות, ואם המעסיק מסכים — אישור ישיר מול משאבי האנוש.'),
        ('ערבויות מתאימות', 'למועמדים בלי היסטוריה בספרד: ערבות בנקאית, פיקדון נוסף, ערב תושב ספרד, התחייבות של המעסיק — בגבולות חוק השכירות.'),
        ('חוזה LAU דו־לשוני', 'חוזה לפי חוק השכירות העירונית בנוסחו הנוכחי, הנוסח הספרדי מחייב ולצידו תרגום; רשימת ריהוט כנספח.'),
        ('הפקדת הפיקדון', 'גביית הפיקדון החוקי (fianza) והפקדתו בקהילת מדריד, כפי שהתקנות מחייבות.'),
        ('פרוטוקול ומסירת מפתחות', 'רישום חדר אחר חדר עם תמונות מתוארכות, קריאת מונים, דוח חתום על ידי שני הצדדים.'),
        ('איש קשר לאורך החוזה', 'השוכר מתקשר אלינו, לא אליכם: בקשות קטנות, בעלי מקצוע, העברת חשבונות, ובסוף — סיום החוזה ופרוטוקול יציאה.')],
    gu_eyebrow='ערבויות',
    gu_h2='איך מבטיחים מועמד בלי היסטוריה בספרד',
    gu_lead='למנהל מועבר אין תלושי שכר ספרדיים ותיקים ואין היסטוריית אשראי מקומית. הנה מה שהחוק מאפשר לבקש, ומה אנחנו מסדרים.',
    gu_rows=[('פיקדון חוקי (fianza)', 'שכר דירה של חודש לחוזה מגורים (חודשיים לשימוש אחר, כולל השכרה עונתית), מופקד בקהילת מדריד.'),
             ('ערבות נוספת', 'פיקדון או ערבות בנקאית. בחוזה מגורים לחמש שנים (שבע אם המשכיר הוא חברה) — עד שני חודשי שכירות.'),
             ('ערב תושב ספרד', 'אדם שגר בספרד חותם כערב סולידרי לשוכר (fiador).'),
             ('התחייבות המעסיק', 'מכתב מהמעסיק, או אפילו חוזה על שם החברה: האפשרות החזקה ביותר בהעברת עובד.'),
             ('ביטוח אי־תשלום שכירות', 'אופציונלי, על חשבונכם, אחרי שהמבטח בודק את התיק.')],
    gu_note='חשוב לדעת: החוק אוסר לדרוש יותר מחודש שכירות אחד מראש. ״שישה חודשים מראש״, שמוצעים לפעמים, אינם ערבות שנוכל להמליץ עליה.',
    fee_eyebrow='שכר טרחה',
    fee_h2='עמלה אחת, רק בחתימה',
    fee=[('עמלה בחתימת החוזה', 'הסכום נמסר לפי בקשה, לפני כל התחייבות.'),
         ('לפני החתימה', 'אין מה לשלם: מודעה, צפיות ובדיקות כלולות.'),
         ('לשוכר', 'כלום: כפי שהחוק קובע, עלויות התיווך והניהול חלות על המשכיר.')],
    fee_note='לעולם איננו מייצגים את שני הצדדים של אותו חוזה: מועמד שאנחנו מלווים בחיפוש הדירה שלו לא יוצג לכם על ידינו.',
    faq_h2='שאלות של בעלי נכסים',
    faq=[('כמה זמן לוקח להשכיר?', 'לנכס במחיר נכון באזור מבוקש — שבועיים עד ארבעה מהפרסום ועד החתימה. לפני שמתחילים, תקבלו מאיתנו חוות דעת כנה על המחיר.'),
         ('אפשר להשכיר מרוהט, או לכמה חודשים?', 'כן. חוזה עונתי (temporada: פחות משנה, לצורך זמני של השוכר) כפוף לכללים אחרים מחוזה מגורים; נגיד לכם איזה מהם מתאים לכם ולמועמד.'),
         ('מה קורה אם השכירות לא משולמת?', 'אנחנו פונים מיד ומפעילים את הערבויות שבחוזה. אם נדרש הליך, עורך הדין השותף מטפל בו. הבדיקה היסודית של התיקים נועדה למנוע את זה מראש.'),
         ('אני גר מחוץ לספרד. זו בעיה?', 'לא, זה מצב נפוץ: חתימה מרחוק, פרוטוקול בלעדיכם, דוח תמונות, ולשוכר יש מישהו במקום.')],
    form_eyebrow='להציע את הנכס',
    form_h2='ספרו לנו על הנכס',
    form_p='נחזור אליכם תוך 24 שעות עבודה עם חוות דעת על המחיר ולוח זמנים.',
    f=dict(name='שם מלא', email='אימייל', phone='טלפון / וואטסאפ', address='כתובת הנכס', type='סוג הנכס',
           types=[('appartement', 'דירה'), ('maison', 'בית'), ('studio', 'סטודיו'), ('autre', 'אחר')], choose='בחרו…',
           furnished='מרוהט?', furn=[('oui', 'כן'), ('non', 'לא'), ('a-voir', 'גמיש')],
           rent='שכר דירה מבוקש (€ לחודש)', avail='פנוי החל מ', message='פרטים (שטח, חדרים, חוץ, חיות…)', optional='(לא חובה)',
           consent='אני מאשר/ת שהנתונים ישמשו למענה לפנייתי, בהתאם ל<a href="/he/legal/privacy-policy">מדיניות הפרטיות</a>.',
           submit='שליחה', note='מענה תוך 24 שעות עבודה. הפרטים לא מועברים לאף אחד.', honey='לא למלא:'),
),
}


def landlord_form(lang, f):
    types = ''.join(f'<option value="{v}">{l}</option>' for v, l in f['types'])
    furn = ''.join(f'<option value="{v}">{l}</option>' for v, l in f['furn'])
    return f'''    <form class="rdv-form" name="proprietaires" method="POST" data-netlify="true" netlify-honeypot="bot-field">
      <input type="hidden" name="form-name" value="proprietaires">
      <input type="hidden" name="langue" value="{lang}">
      <p class="hidden-field"><label>{f['honey']} <input name="bot-field"></label></p>
      <div class="rdv-row">
        <label><span>{f['name']}</span><input type="text" name="nom" required autocomplete="name"></label>
        <label><span>{f['email']}</span><input type="email" name="email" required autocomplete="email"></label>
      </div>
      <div class="rdv-row">
        <label><span>{f['phone']} <em>{f['optional']}</em></span><input type="tel" name="telephone" autocomplete="tel"></label>
        <label><span>{f['address']}</span><input type="text" name="adresse" required autocomplete="street-address"></label>
      </div>
      <div class="rdv-row">
        <label><span>{f['type']}</span><select name="type" required><option value="">{f['choose']}</option>{types}</select></label>
        <label><span>{f['furnished']}</span><select name="meuble"><option value="">{f['choose']}</option>{furn}</select></label>
      </div>
      <div class="rdv-row">
        <label><span>{f['rent']}</span><input type="number" name="loyer_vise" min="0" step="1" inputmode="numeric" required></label>
        <label><span>{f['avail']}</span><input type="date" name="disponibilite" required></label>
      </div>
      <label class="rdv-full"><span>{f['message']} <em>{f['optional']}</em></span><textarea name="message" rows="3"></textarea></label>
      <label class="chk consent"><input type="checkbox" name="consentement" value="oui" required> <span>{f['consent']}</span></label>
      <button type="submit">{f['submit']}</button>
      <p class="rdv-note">{f['note']}</p>
    </form>'''


def build(lang):
    c = C[lang]
    steps = '\n'.join(f'      <li><strong>{h}</strong>{t}</li>' for h, t in c['do'])
    rows = '\n'.join(f'        <tr><th scope="row">{h}</th><td>{t}</td></tr>' for h, t in c['gu_rows'])
    fee = '\n'.join(f'      <li><strong>{h}</strong><small>{t}</small></li>' for h, t in c['fee'])
    faq = '\n'.join(f'      <details><summary>{q}</summary><p>{a}</p></details>' for q, a in c['faq'])
    body = f'''
<section class="art-hero">
  <div class="container">
    <p class="eyebrow">{c['eyebrow']}</p>
    <h1>{c['h1']}</h1>
    <p class="standfirst">{c['stand']}</p>
    <p class="hero-actions"><a class="hero-btn" href="#bien">{c['hero_cta']}</a></p>
  </div>
</section>

<section class="v2-section" id="services">
  <div class="container">
    <p class="eyebrow">{c['do_eyebrow']}</p>
    <h2>{c['do_h2']}</h2>
    <ol class="steps">
{steps}
    </ol>
  </div>
</section>

<section class="v2-section alt" id="garanties">
  <div class="container">
    <p class="eyebrow">{c['gu_eyebrow']}</p>
    <h2>{c['gu_h2']}</h2>
    <p class="lead">{c['gu_lead']}</p>
    <table class="datatable v2-table">
      <tbody>
{rows}
      </tbody>
    </table>
    <div class="callout warn"><p>{c['gu_note']}</p></div>
  </div>
</section>

<section class="v2-section" id="remuneration">
  <div class="container">
    <p class="eyebrow">{c['fee_eyebrow']}</p>
    <h2>{c['fee_h2']}</h2>
    <ul class="commit-grid">
{fee}
    </ul>
    <p class="v2-fine">{c['fee_note']}</p>
  </div>
</section>

<section class="v2-section alt" id="faq">
  <div class="container v2-faq">
    <h2>{c['faq_h2']}</h2>
{faq}
  </div>
</section>

<section class="v2-final" id="bien">
  <div class="container">
    <p class="eyebrow">{c['form_eyebrow']}</p>
    <h2>{c['form_h2']}</h2>
    <p>{c['form_p']}</p>
{landlord_form(lang, c['f'])}
  </div>
</section>
'''
    page(lang, URLS[lang], c['title'], c['desc'], body, alts=URLS, current='landlords')


if __name__ == '__main__':
    for lang in ('fr', 'en', 'he'):
        build(lang)
