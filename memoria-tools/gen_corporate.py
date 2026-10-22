#!/usr/bin/env python3
"""Génère /entreprises/, /en/corporate/, /he/corporate/ (formulaire Netlify « corporate »)."""
from layout import page

URLS = {'fr': '/entreprises/', 'en': '/en/corporate/', 'he': '/he/corporate/'}

C = {
'fr': dict(
    title='Relocation Madrid pour entreprises et RMC — destination services | Mémoria',
    desc="Destination services à Madrid pour DRH et sociétés de relocation : briefing, orientation, home search, settling-in, écoles, départ. Réponse sous 24 h ouvrées, facturation à l'employeur.",
    eyebrow='Entreprises · Sociétés de relocation (RMC)',
    h1='Vos collaborateurs mutés à Madrid, installés sans mobiliser vos RH.',
    stand="Nous prenons en charge l'arrivée de vos salariés et de leur famille, du briefing pré-départ à la remise des clés — puis, le moment venu, leur départ. Un interlocuteur unique pour vous, un autre pour eux, et des rapports d'étape que vous n'avez pas à réclamer.",
    hero_cta='Demander un devis entreprise',
    pk_eyebrow='Packages destination services',
    pk_h2='Six packages, combinables, facturés à l\'employeur',
    pk_lead="Les intitulés suivent la terminologie du secteur, pour s'intégrer directement à vos politiques de mobilité et aux bons de commande de votre RMC. Prix sur devis, exprimés HT (la TVA est récupérable par l'entreprise), selon la taille du foyer et le calendrier.",
    pk_price='Sur devis, montants HT · facturé à l\'employeur',
    packages=[
        ('Pre-arrival briefing', 'À distance · 1 h + compte rendu', ["Visio avec le collaborateur (et son conjoint)", "Calendrier des démarches et des pièces à préparer avant le départ", "Premières pistes de quartiers et d'écoles", "Compte rendu écrit, copie RH"]),
        ('Orientation', '1 jour sur place', ["Trois à quatre quartiers selon le lieu de travail", "Trajets réels aux heures de pointe", "Écoles, commerces, santé, sport", "Carnet comparatif remis le soir même"]),
        ('Home Search', '2 à 3 jours de visites + check-in', ["Présélection et contre-visites", "Négociation du loyer et des garanties", "Vérification du bail selon la LAU en vigueur", "Signature (y compris à distance), état des lieux photo, remise des clés"]),
        ('Settling-in', 'Démarches regroupées', ["NIE / certificat UE, padrón, sécurité sociale, carte sanitaire", "Compte bancaire, électricité, gaz, eau, internet", "Cl@ve et certificat numérique", "Immigration hors UE coordonnée avec notre avocat partenaire"]),
        ('School search', 'Cartographie + inscriptions', ["Écoles publiques, concertadas, internationales", "Coût réel et places disponibles", "Visites, tests d'entrée, dossiers", "Admission hors campagne via le SAE"]),
        ('Departure', 'Fin de mission', ["Préavis et état des lieux de sortie", "Récupération de la fianza", "Clôture des contrats et baja du padrón", "Radiation ou export du véhicule"]),
    ],
    pk_more=('/services/', 'Le détail de chaque prestation est dans notre catalogue →'),
    st_eyebrow='Déroulé d\'une mission',
    st_h2='Vous savez toujours où en est votre collaborateur',
    steps=[('Brief RH', "Un appel de 30 minutes : profil du foyer, date d'arrivée, budget logement, services couverts par votre politique."),
           ('Calendrier partagé', "Sous 48 h, un planning daté de chaque étape, partagé avec vous et le collaborateur."),
           ("Rapports d'étape", "Un point écrit chaque semaine : fait, à venir, points d'attention, dépenses engagées."),
           ('Rapport de fin de mission', "Synthèse des prestations réalisées, documents obtenus, échéances à venir pour le collaborateur.")],
    cap="Vous référencez un nouveau prestataire ? Notre fiche fournisseur (capability statement, en anglais) est prête à joindre à vos formulaires →",
    cm_eyebrow='Nos engagements',
    cm_h2='Ce sur quoi vous pouvez compter',
    commits=[('Réponse sous 24 h ouvrées', 'À toute demande RH ou collaborateur.'),
             ('Point hebdomadaire', 'Écrit, daté, sans relance de votre part.'),
             ('DPA disponible', 'Accord de traitement des données signé avant toute transmission.'),
             ('Conformité RGPD', 'Transferts hors UE encadrés par les clauses contractuelles types de la Commission européenne ; accès limités, suppression en fin de mission.'),
             ('Facturation en euros', 'Depuis une S.L. espagnole (Star Alliance Consulting S.L., NIF B19750199).'),
             ('Quatre langues', 'Français, anglais, hébreu et espagnol — pour le collaborateur et sa famille.'),
             ('Démarches réglementées encadrées', 'Visas et permis de travail hors UE déposés par notre avocat partenaire.'),
             ('Aucune commission propriétaire', "Quand nous cherchons pour votre collaborateur, nous ne sommes payés que par vous."),
             ('Sous-traitance RMC', 'Nous intervenons comme DSP pour votre RMC, sous sa marque si elle le souhaite.')],
    form_eyebrow='Devis entreprise',
    form_h2='Parlez-nous de votre prochaine mutation',
    form_p="Nous revenons vers vous sous 24 h ouvrées avec une proposition chiffrée et un calendrier.",
    f=dict(company='Société', contact='Nom et fonction', email='Email professionnel', phone='Téléphone', count='Nombre de collaborateurs', date="Date d'arrivée prévue",
           services='Services souhaités', svc_opts=['Pre-arrival briefing', 'Orientation', 'Home Search', 'Settling-in', 'School search', 'Departure', 'Immigration (hors UE)'],
           message='Contexte, contraintes, questions', optional='(facultatif)', ph="Ex : directeur financier, couple et deux enfants (8 et 12 ans), arrivée en janvier, budget logement 3 500 €/mois, nord de Madrid.",
           consent="J'accepte que ces données soient utilisées pour répondre à ma demande, conformément à la <a href=\"/legal/politique-confidentialite\">politique de confidentialité</a>.",
           submit='Demander un devis entreprise', note='Réponse sous 24 h ouvrées. Vos informations ne sont transmises à personne.', honey='Ne pas remplir :'),
),
'en': dict(
    title='Corporate relocation in Madrid for HR and RMCs — destination services | Mémoria',
    desc='Destination services in Madrid for HR teams and relocation management companies: briefing, orientation, home search, settling-in, schools, departure. Reply within 24 working hours, invoiced to the employer.',
    eyebrow='Employers · Relocation management companies',
    h1='Your people relocated to Madrid, settled in without tying up HR.',
    stand='We take care of your employees\' and their families\' arrival, from the pre-departure briefing to the keys — and, when the time comes, their departure. One point of contact for you, another for them, and progress reports you never have to chase.',
    hero_cta='Request a corporate quote',
    pk_eyebrow='Destination services packages',
    pk_h2='Six packages, combinable, invoiced to the employer',
    pk_lead='Package names follow industry terminology, so they slot straight into your mobility policy and your RMC\'s purchase orders. Priced on quote, before VAT (recoverable by the company), depending on household size and timing.',
    pk_price='On quote, amounts before VAT · invoiced to the employer',
    packages=[
        ('Pre-arrival briefing', 'Remote · 1 h + written summary', ['Video call with the transferee (and partner)', 'Timeline and documents to prepare before leaving', 'First neighbourhood and school options', 'Written summary, copied to HR']),
        ('Orientation', '1 day on the ground', ['Three to four neighbourhoods around the workplace', 'Real rush-hour commutes', 'Schools, shops, healthcare, sport', 'Side-by-side comparison delivered the same evening']),
        ('Home Search', '2 to 3 days of viewings + check-in', ['Shortlisting and pre-visits', 'Negotiation of rent and guarantees', 'Lease review under the current LAU', 'Signing (remote if needed), photo inventory, key handover']),
        ('Settling-in', 'Bundled procedures', ['NIE / EU certificate, padrón, social security, health card', 'Bank account, electricity, gas, water, internet', 'Cl@ve and digital certificate', 'Non-EU immigration coordinated with our partner lawyer']),
        ('School search', 'Mapping + enrolment', ['Public, concertada and international schools', 'Real costs and availability', 'Visits, entrance tests, applications', 'Mid-year admission through the SAE']),
        ('Departure', 'End of assignment', ['Notice and check-out inventory', 'Fianza recovery', 'Closing contracts and padrón removal', 'Vehicle deregistration or export']),
    ],
    pk_more=('/en/services/', 'Every service is detailed in our catalogue →'),
    st_eyebrow='How an assignment runs',
    st_h2='You always know where your transferee stands',
    steps=[('HR brief', 'A 30-minute call: household profile, arrival date, housing budget, services covered by your policy.'),
           ('Shared timeline', 'Within 48 h, a dated plan of every step, shared with you and the transferee.'),
           ('Progress reports', 'A written update every week: done, next, watch-outs, costs committed.'),
           ('End-of-assignment report', 'Summary of services delivered, documents obtained, upcoming deadlines for the transferee.')],
    cap='Onboarding a new supplier? Our capability statement is ready to attach to your vendor forms →',
    cm_eyebrow='Our commitments',
    cm_h2='What you can count on',
    commits=[('Reply within 24 working hours', 'To any HR or transferee request.'),
             ('Weekly update', 'Written and dated, without you having to chase.'),
             ('DPA available', 'Data processing agreement signed before any data is shared.'),
             ('GDPR compliance', 'Transfers outside the EU covered by the European Commission\'s standard contractual clauses; restricted access, deletion at the end of the assignment.'),
             ('Invoicing in euros', 'From a Spanish S.L. (Star Alliance Consulting S.L., tax ID B19750199).'),
             ('Four languages', 'French, English, Hebrew and Spanish — for the transferee and the family.'),
             ('Regulated matters handled properly', 'Non-EU visas and work permits filed by our partner lawyer.'),
             ('No landlord commission', 'When we search for your transferee, you are the only one paying us.'),
             ('RMC subcontracting', 'We act as DSP for your RMC, under its brand if it prefers.')],
    form_eyebrow='Corporate quote',
    form_h2='Tell us about your next move',
    form_p='We come back within 24 working hours with a priced proposal and a timeline.',
    f=dict(company='Company', contact='Name and job title', email='Work email', phone='Phone', count='Number of employees', date='Expected arrival date',
           services='Services needed', svc_opts=['Pre-arrival briefing', 'Orientation', 'Home Search', 'Settling-in', 'School search', 'Departure', 'Immigration (non-EU)'],
           message='Context, constraints, questions', optional='(optional)', ph='e.g. CFO, couple with two children (8 and 12), arriving in January, housing budget €3,500/month, north Madrid.',
           consent='I agree that this data may be used to respond to my request, in accordance with the <a href="/en/legal/privacy-policy">privacy policy</a>.',
           submit='Request a corporate quote', note='Reply within 24 working hours. Your details are never shared.', honey='Do not fill:'),
),
'he': dict(
    title='רילוקיישן למדריד לחברות ולחברות רילוקיישן — Destination Services | Mémoria',
    desc='שירותי Destination במדריד למשאבי אנוש ולחברות רילוקיישן: תדריך, התמצאות, חיפוש דירה, קליטה, בתי ספר ועזיבה. מענה תוך 24 שעות עבודה, בחיוב המעסיק.',
    eyebrow='חברות · חברות רילוקיישן (RMC)',
    h1='העובדים שאתם מעבירים למדריד מתמקמים — בלי להעמיס על משאבי האנוש.',
    stand='אנחנו מטפלים בהגעה של העובדים ובני המשפחה שלהם, מהתדריך לפני הטיסה ועד מסירת המפתחות — וגם בעזיבה, כשיגיע הזמן. איש קשר אחד בשבילכם, אחד בשבילם, ודוחות התקדמות שלא צריך לבקש.',
    hero_cta='לבקש הצעת מחיר לחברה',
    pk_eyebrow='חבילות Destination Services',
    pk_h2='שש חבילות, ניתנות לשילוב, בחיוב המעסיק',
    pk_lead='שמות החבילות לפי המינוח המקובל בענף, כך שהן משתלבות ישירות במדיניות הניידות שלכם ובהזמנות הרכש של חברת הרילוקיישן. מחיר לפי הצעה, לפני מע״מ (שהחברה יכולה לקזז), בהתאם לגודל המשפחה וללוח הזמנים.',
    pk_price='לפי הצעת מחיר, סכומים לפני מע״מ · בחיוב המעסיק',
    packages=[
        ('Pre-arrival briefing', 'מרחוק · שעה + סיכום כתוב', ['שיחת וידאו עם העובד (ובן או בת הזוג)', 'לוח זמנים ומסמכים להכנה לפני הטיסה', 'כיווני שכונות ובתי ספר ראשונים', 'סיכום כתוב, בהעתק למשאבי אנוש']),
        ('Orientation', 'יום אחד בשטח', ['שלוש־ארבע שכונות סביב מקום העבודה', 'נסיעות אמיתיות בשעות העומס', 'בתי ספר, קניות, בריאות, ספורט', 'טבלת השוואה באותו ערב']),
        ('Home Search', 'יומיים־שלושה של צפיות + כניסה', ['סינון וביקורים מקדימים', 'משא ומתן על שכר הדירה והערבויות', 'בדיקת החוזה לפי חוק השכירות (LAU)', 'חתימה (גם מרחוק), פרוטוקול עם תמונות, מסירת מפתחות']),
        ('Settling-in', 'הליכים מרוכזים', ['NIE / תעודה אירופית, פדרון, ביטוח לאומי, כרטיס בריאות', 'חשבון בנק, חשמל, גז, מים, אינטרנט', 'Cl@ve ותעודה דיגיטלית', 'הגירה מחוץ לאיחוד בתיאום עם עורך הדין השותף']),
        ('School search', 'מפה + רישום', ['בתי ספר ציבוריים, concertados ובינלאומיים', 'עלויות אמיתיות ומקומות פנויים', 'ביקורים, מבחני כניסה, תיקים', 'רישום באמצע השנה דרך ה-SAE']),
        ('Departure', 'סיום המשימה', ['הודעה מוקדמת ופרוטוקול יציאה', 'החזר הפיקדון', 'סגירת חוזים וביטול פדרון', 'ביטול רישום או ייצוא הרכב']),
    ],
    pk_more=('/he/services/', 'כל שירות מפורט בקטלוג שלנו ←'),
    st_eyebrow='איך מתנהלת משימה',
    st_h2='תמיד תדעו איפה העובד עומד',
    steps=[('תדריך משאבי אנוש', 'שיחה של 30 דקות: פרופיל המשפחה, תאריך הגעה, תקציב דיור, השירותים שהמדיניות שלכם מכסה.'),
           ('לוח זמנים משותף', 'תוך 48 שעות: תוכנית עם תאריכים לכל שלב, משותפת לכם ולעובד.'),
           ('דוחות התקדמות', 'עדכון כתוב בכל שבוע: מה נעשה, מה הלאה, נקודות לתשומת לב, הוצאות.'),
           ('דוח סיום', 'סיכום השירותים שניתנו, המסמכים שהתקבלו והמועדים הבאים של העובד.')],
    cap='מוסיפים ספק חדש? דף היכולות שלנו (capability statement, באנגלית) מוכן לצירוף לטפסי הספקים שלכם ←',
    cm_eyebrow='ההתחייבויות שלנו',
    cm_h2='על מה אפשר לסמוך',
    commits=[('מענה תוך 24 שעות עבודה', 'לכל פנייה של משאבי אנוש או של העובד.'),
             ('עדכון שבועי', 'בכתב, עם תאריך, בלי שתצטרכו לבקש.'),
             ('הסכם עיבוד נתונים (DPA)', 'נחתם לפני העברת נתונים כלשהי.'),
             ('עמידה ב-GDPR', 'העברות אל מחוץ לאיחוד מוסדרות בסעיפים החוזיים התקניים של הנציבות האירופית; גישה מוגבלת, מחיקה בסוף המשימה.'),
             ('חשבוניות ביורו', 'מחברה ספרדית (Star Alliance Consulting S.L., מס׳ עוסק B19750199).'),
             ('ארבע שפות', 'עברית, אנגלית, צרפתית וספרדית — לעובד ולמשפחה.'),
             ('הליכים מוסדרים כראוי', 'אשרות והיתרי עבודה מחוץ לאיחוד מוגשים על ידי עורך הדין השותף.'),
             ('בלי עמלה מבעל הדירה', 'כשאנחנו מחפשים בשביל העובד שלכם, רק אתם משלמים לנו.'),
             ('קבלני משנה ל-RMC', 'אנחנו פועלים כ-DSP של חברת הרילוקיישן שלכם, גם תחת המותג שלה.')],
    form_eyebrow='הצעת מחיר לחברה',
    form_h2='ספרו לנו על ההעברה הבאה',
    form_p='נחזור אליכם תוך 24 שעות עבודה עם הצעה מתומחרת ולוח זמנים.',
    f=dict(company='חברה', contact='שם ותפקיד', email='אימייל בעבודה', phone='טלפון', count='מספר עובדים', date='תאריך הגעה משוער',
           services='שירותים נדרשים', svc_opts=['Pre-arrival briefing', 'Orientation', 'Home Search', 'Settling-in', 'School search', 'Departure', 'הגירה (מחוץ לאיחוד)'],
           message='רקע, אילוצים, שאלות', optional='(לא חובה)', ph='לדוגמה: סמנכ״ל כספים, זוג ושני ילדים (8 ו-12), הגעה בינואר, תקציב דיור €3,500 לחודש, צפון מדריד.',
           consent='אני מאשר/ת שהנתונים ישמשו למענה לפנייתי, בהתאם ל<a href="/he/legal/privacy-policy">מדיניות הפרטיות</a>.',
           submit='לבקש הצעת מחיר', note='מענה תוך 24 שעות עבודה. הפרטים לא מועברים לאף אחד.', honey='לא למלא:'),
),
}

# Valeurs envoyées par les cases « services » : identiques dans les trois langues
# pour que les soumissions du formulaire « corporate » restent comparables.
SVC_VALUES = ['Pre-arrival briefing', 'Orientation', 'Home Search', 'Settling-in', 'School search', 'Departure', 'Immigration']


def corporate_form(lang, f):
    checks = '\n'.join(f'        <label class="chk"><input type="checkbox" name="services" value="{v}"> {lbl}</label>'
                       for v, lbl in zip(SVC_VALUES, f['svc_opts']))
    return f'''    <form class="rdv-form" name="corporate" method="POST" data-netlify="true" netlify-honeypot="bot-field">
      <input type="hidden" name="form-name" value="corporate">
      <input type="hidden" name="langue" value="{lang}">
      <p class="hidden-field"><label>{f['honey']} <input name="bot-field"></label></p>
      <div class="rdv-row">
        <label><span>{f['company']}</span><input type="text" name="societe" required autocomplete="organization"></label>
        <label><span>{f['contact']}</span><input type="text" name="contact" required autocomplete="name"></label>
      </div>
      <div class="rdv-row">
        <label><span>{f['email']}</span><input type="email" name="email" required autocomplete="email"></label>
        <label><span>{f['phone']} <em>{f['optional']}</em></span><input type="tel" name="telephone" autocomplete="tel"></label>
      </div>
      <div class="rdv-row">
        <label><span>{f['count']}</span><input type="number" name="collaborateurs" min="1" step="1" inputmode="numeric" required></label>
        <label><span>{f['date']}</span><input type="date" name="date_arrivee"></label>
      </div>
      <fieldset>
        <legend>{f['services']}</legend>
{checks}
      </fieldset>
      <label class="rdv-full"><span>{f['message']} <em>{f['optional']}</em></span><textarea name="message" rows="4" placeholder="{f['ph']}"></textarea></label>
      <label class="chk consent"><input type="checkbox" name="consentement" value="oui" required> <span>{f['consent']}</span></label>
      <button type="submit">{f['submit']}</button>
      <p class="rdv-note">{f['note']}</p>
    </form>'''


def build(lang, extra_sections=''):
    c = C[lang]
    pk = '\n'.join(f'''      <div class="pkg">
        <h3>{name}</h3>
        <p class="pkg-meta">{meta}</p>
        <ul>{''.join(f'<li>{li}</li>' for li in items)}</ul>
        <p class="pkg-price">{c['pk_price']}</p>
      </div>''' for name, meta, items in c['packages'])
    steps = '\n'.join(f'      <li><strong>{h}</strong>{t}</li>' for h, t in c['steps'])
    commits = '\n'.join(f'      <li><strong>{h}</strong><small>{t}</small></li>' for h, t in c['commits'])
    body = f'''
<section class="art-hero">
  <div class="container">
    <p class="eyebrow">{c['eyebrow']}</p>
    <h1>{c['h1']}</h1>
    <p class="standfirst">{c['stand']}</p>
    <p class="hero-actions"><a class="hero-btn" href="#devis">{c['hero_cta']}</a></p>
  </div>
</section>

<section class="v2-section" id="packages">
  <div class="container">
    <p class="eyebrow">{c['pk_eyebrow']}</p>
    <h2>{c['pk_h2']}</h2>
    <p class="lead">{c['pk_lead']}</p>
    <div class="pkg-grid">
{pk}
    </div>
    <p class="gt-all" style="margin-top:24px"><a href="{c['pk_more'][0]}">{c['pk_more'][1]}</a></p>
  </div>
</section>

<section class="v2-section alt" id="deroule">
  <div class="container">
    <p class="eyebrow">{c['st_eyebrow']}</p>
    <h2>{c['st_h2']}</h2>
    <ol class="steps">
{steps}
    </ol>
  </div>
</section>

<section class="v2-section" id="engagements">
  <div class="container">
    <p class="eyebrow">{c['cm_eyebrow']}</p>
    <h2>{c['cm_h2']}</h2>
    <ul class="commit-grid">
{commits}
    </ul>
    <p class="v2-fine"><a href="/docs/memoria-capability-statement">{c['cap']}</a></p>
  </div>
</section>
{extra_sections}
<section class="v2-final" id="devis">
  <div class="container">
    <p class="eyebrow">{c['form_eyebrow']}</p>
    <h2>{c['form_h2']}</h2>
    <p>{c['form_p']}</p>
{corporate_form(lang, c['f'])}
  </div>
</section>
'''
    page(lang, URLS[lang], c['title'], c['desc'], body, alts=URLS, current='corporate')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    try:
        from proof import corporate_extra
    except ImportError:
        corporate_extra = lambda lang: ''
    for lang in ('fr', 'en', 'he'):
        build(lang, corporate_extra(lang))
