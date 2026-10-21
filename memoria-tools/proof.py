"""Preuve et confiance : logos, étude de cas, témoignages, FAQ entreprises.

Tous les [CHAMPS] sont à remplacer par du contenu réel (avec accord écrit des
clients pour les logos et témoignages) avant mise en ligne.
"""

P = {
'fr': dict(
    logos_eyebrow='Ils nous ont fait confiance',
    logos_h2='Des entreprises et des familles nous ont confié leur installation',
    logo='[LOGO CLIENT {n}]',
    case_eyebrow='Étude de cas',
    case_h3='Une famille mutée à Madrid en cinq semaines',
    case_ctx="Poste de direction dans un groupe international, un couple et deux enfants scolarisés, une arrivée fixée cinq semaines après l'annonce de la mutation. Données anonymisées avec l'accord de l'entreprise.",
    kpis=[('5 sem.', "de l'annonce à l'installation"), ('[X]', 'logements présélectionnés'), ('[X] jours', 'pour obtenir les places scolaires'), ('[X] %', 'de loyer négocié')],
    case_steps=[('Semaine 1', "Brief RH, briefing du foyer en visio, cartographie scolaire et premières pistes de quartiers dans le nord de Madrid."),
                ('Semaine 2', "Home search : [X] biens présélectionnés, contre-visites, visites vidéo avec la famille encore à l'étranger."),
                ('Semaine 3', "Bail négocié et vérifié selon la LAU, garanties portées par une lettre de l'employeur, signature à distance."),
                ('Semaine 4', "Dossiers NIE et certificats préparés, inscriptions scolaires, électricité, gaz, eau et internet activés avant l'arrivée."),
                ('Semaine 5', "Arrivée : remise des clés, état des lieux photo, padrón, cartes sanitaires, compte bancaire. Rapport de fin de mission aux RH.")],
    case_quote='« [CITATION DU RESPONSABLE RH — une à deux phrases] »',
    case_quote_by='[FONCTION], [SECTEUR DE L\'ENTREPRISE]',
    t_eyebrow='Témoignages',
    t_h2='Ce qu\'ils en disent',
    testimonials=[('« [TÉMOIGNAGE 1 — deux à trois phrases sur ce que Mémoria a changé dans l\'installation] »', '[PRÉNOM]', '[NATIONALITÉ]', '[POSTE]'),
                  ('« [TÉMOIGNAGE 2 — deux à trois phrases] »', '[PRÉNOM]', '[NATIONALITÉ]', '[POSTE]'),
                  ('« [TÉMOIGNAGE 3 — deux à trois phrases] »', '[PRÉNOM]', '[NATIONALITÉ]', '[POSTE]')],
    faq_eyebrow='Questions des entreprises',
    faq_h2='FAQ entreprises',
    faq=[('Comment se passe la facturation ?', "Nous facturons l'entreprise ou la RMC, en euros, depuis Star Alliance Consulting S.L., société espagnole. Devis par collaborateur ou par package ; facture à la fin de chaque package, ou mensuelle pour les missions longues. Taxes officielles et frais de tiers (traductions, avocat) refacturés au réel, sur justificatif."),
         ('Sous quels délais pouvez-vous intervenir ?', "Brief RH sous 24 h ouvrées, calendrier sous 48 h ; une recherche de logement peut démarrer la semaine suivante. Les délais des administrations (rendez-vous, délivrance des documents) ne dépendent pas de nous : nous les anticipons dans le calendrier, sans jamais les promettre."),
         ('Comment protégez-vous les données de nos collaborateurs ?', "Un accord de traitement (DPA) est signé avant tout échange. Les données sont hébergées dans l'Union européenne, accessibles aux seules personnes affectées à la mission, transmises uniquement aux administrations et partenaires nécessaires, et supprimées en fin de mission."),
         ('Quelles zones couvrez-vous ?', "Madrid capitale et l'ensemble de la Comunidad de Madrid, dont Pozuelo de Alarcón, Las Rozas, Majadahonda, Boadilla del Monte, Alcobendas, San Sebastián de los Reyes et Tres Cantos. Au-delà, sur demande."),
         ('Dans quelles langues travaillez-vous ?', "Français, anglais, hébreu et espagnol, avec le collaborateur comme avec sa famille. Les documents clés (bail, états des lieux, rapports) sont fournis en version bilingue."),
         ('Quelle différence avec une agence immobilière ?', "Une agence représente le propriétaire et se rémunère sur la location. Nous travaillons pour votre collaborateur et sommes payés par vous : nous cherchons sur tout le marché, négocions pour lui, vérifions le bail, puis prenons en charge tout ce qui suit la remise des clés — démarches, écoles, contrats. Quand nous accompagnons un locataire, nous ne touchons rien du propriétaire.")],
    home_case=('/entreprises/#cas', "Lire l'étude de cas : une famille installée en cinq semaines →"),
),
'en': dict(
    logos_eyebrow='They trusted us',
    logos_h2='Companies and families who trusted us with their move',
    logo='[CLIENT LOGO {n}]',
    case_eyebrow='Case study',
    case_h3='A family relocated to Madrid in five weeks',
    case_ctx='A senior management role in an international group, a couple with two school-age children, and an arrival date set five weeks after the transfer was announced. Data anonymised with the company\'s agreement.',
    kpis=[('5 wks', 'from announcement to move-in'), ('[X]', 'homes shortlisted'), ('[X] days', 'to secure school places'), ('[X]%', 'rent negotiated down')],
    case_steps=[('Week 1', 'HR brief, family briefing by video, school mapping and first neighbourhood options in north Madrid.'),
                ('Week 2', 'Home search: [X] properties shortlisted, pre-visits, video viewings with the family still abroad.'),
                ('Week 3', 'Lease negotiated and reviewed under the LAU, guarantees backed by an employer letter, signed remotely.'),
                ('Week 4', 'NIE and certificate files prepared, school enrolments, electricity, gas, water and internet live before arrival.'),
                ('Week 5', 'Arrival: key handover, photo inventory, padrón, health cards, bank account. End-of-assignment report to HR.')],
    case_quote='“[QUOTE FROM THE HR MANAGER — one or two sentences]”',
    case_quote_by='[JOB TITLE], [COMPANY SECTOR]',
    t_eyebrow='Testimonials',
    t_h2='What they say',
    testimonials=[('“[TESTIMONIAL 1 — two or three sentences on what Mémoria changed about the move]”', '[FIRST NAME]', '[NATIONALITY]', '[JOB TITLE]'),
                  ('“[TESTIMONIAL 2 — two or three sentences]”', '[FIRST NAME]', '[NATIONALITY]', '[JOB TITLE]'),
                  ('“[TESTIMONIAL 3 — two or three sentences]”', '[FIRST NAME]', '[NATIONALITY]', '[JOB TITLE]')],
    faq_eyebrow='Employers\' questions',
    faq_h2='Corporate FAQ',
    faq=[('How does invoicing work?', 'We invoice the company or the RMC, in euros, from Star Alliance Consulting S.L., a Spanish company. Quotes per transferee or per package; invoiced at the end of each package, or monthly for long assignments. Official fees and third-party costs (translations, lawyer) recharged at cost, with receipts.'),
         ('How quickly can you start?', 'HR brief within 24 working hours, timeline within 48 h; a home search can start the following week. Administrative timings (appointments, document issuance) are not in our hands: we build them into the timeline, but never promise them.'),
         ('How do you protect our employees\' data?', 'A data processing agreement (DPA) is signed before anything is shared. Data is hosted in the European Union, accessible only to the people on the assignment, passed only to the administrations and partners that need it, and deleted at the end of the assignment.'),
         ('Which areas do you cover?', 'Madrid city and the whole Comunidad de Madrid, including Pozuelo de Alarcón, Las Rozas, Majadahonda, Boadilla del Monte, Alcobendas, San Sebastián de los Reyes and Tres Cantos. Further afield on request.'),
         ('Which languages do you work in?', 'French, English, Hebrew and Spanish, with the transferee and with the family. Key documents (lease, inventories, reports) are provided in bilingual versions.'),
         ('How is this different from an estate agent?', 'An agent represents the landlord and is paid on the letting. We work for your transferee and are paid by you: we search the whole market, negotiate on their behalf, check the lease, then handle everything after the keys — procedures, schools, contracts. When we support a tenant, we take nothing from the landlord.')],
    home_case=('/en/corporate/#cas', 'Read the case study: a family settled in five weeks →'),
),
'he': dict(
    logos_eyebrow='סמכו עלינו',
    logos_h2='חברות ומשפחות שהפקידו בידינו את המעבר',
    logo='[לוגו לקוח {n}]',
    case_eyebrow='מקרה בוחן',
    case_h3='משפחה שעברה למדריד בחמישה שבועות',
    case_ctx='תפקיד הנהלה בקבוצה בינלאומית, זוג ושני ילדים בגיל בית ספר, ותאריך הגעה שנקבע חמישה שבועות אחרי ההודעה על ההעברה. הנתונים הוסוו בהסכמת החברה.',
    kpis=[('5 שב׳', 'מההודעה ועד הכניסה'), ('[X]', 'נכסים שסוננו'), ('[X] ימים', 'עד קבלת מקומות בבית הספר'), ('[X]%', 'הנחה שהושגה בשכר הדירה')],
    case_steps=[('שבוע 1', 'תדריך משאבי אנוש, תדריך למשפחה בווידאו, מפת בתי ספר וכיווני שכונות ראשונים בצפון מדריד.'),
                ('שבוע 2', 'חיפוש דירה: [X] נכסים שסוננו, ביקורים מקדימים, צפיות בווידאו עם המשפחה שעוד בחו״ל.'),
                ('שבוע 3', 'חוזה שנוהל ונבדק לפי ה-LAU, ערבויות על בסיס מכתב מהמעסיק, חתימה מרחוק.'),
                ('שבוע 4', 'תיקי NIE ותעודות מוכנים, רישום לבתי ספר, חשמל, גז, מים ואינטרנט פעילים לפני ההגעה.'),
                ('שבוע 5', 'הגעה: מסירת מפתחות, פרוטוקול עם תמונות, פדרון, כרטיסי בריאות, חשבון בנק. דוח סיום למשאבי אנוש.')],
    case_quote='״[ציטוט ממנהל/ת משאבי האנוש — משפט או שניים]״',
    case_quote_by='[תפקיד], [תחום החברה]',
    t_eyebrow='המלצות',
    t_h2='מה הם אומרים',
    testimonials=[('״[המלצה 1 — שניים־שלושה משפטים על מה ש-Mémoria שינתה במעבר]״', '[שם פרטי]', '[אזרחות]', '[תפקיד]'),
                  ('״[המלצה 2 — שניים־שלושה משפטים]״', '[שם פרטי]', '[אזרחות]', '[תפקיד]'),
                  ('״[המלצה 3 — שניים־שלושה משפטים]״', '[שם פרטי]', '[אזרחות]', '[תפקיד]')],
    faq_eyebrow='שאלות של חברות',
    faq_h2='שאלות נפוצות לחברות',
    faq=[('איך עובד החיוב?', 'אנחנו מחייבים את החברה או את חברת הרילוקיישן, ביורו, מ-Star Alliance Consulting S.L., חברה ספרדית. הצעת מחיר לפי עובד או לפי חבילה; חשבונית בסוף כל חבילה, או חודשית במשימות ארוכות. אגרות רשמיות ועלויות צד שלישי (תרגום, עורך דין) לפי העלות בפועל, עם אסמכתאות.'),
         ('תוך כמה זמן אפשר להתחיל?', 'תדריך משאבי אנוש תוך 24 שעות עבודה, לוח זמנים תוך 48 שעות; חיפוש דירה יכול להתחיל בשבוע שאחרי. הזמנים של הרשויות (תורים, הנפקת מסמכים) לא בידינו: אנחנו מתכננים אותם מראש, אבל לעולם לא מבטיחים אותם.'),
         ('איך אתם מגינים על הנתונים של העובדים?', 'הסכם עיבוד נתונים (DPA) נחתם לפני כל העברה. הנתונים מאוחסנים באיחוד האירופי, נגישים רק לצוות המשימה, מועברים רק לרשויות ולשותפים שצריכים אותם, ונמחקים בסוף המשימה.'),
         ('אילו אזורים אתם מכסים?', 'מדריד העיר וכל קהילת מדריד, כולל Pozuelo de Alarcón, ‏Las Rozas, ‏Majadahonda, ‏Boadilla del Monte, ‏Alcobendas, ‏San Sebastián de los Reyes ו-Tres Cantos. מעבר לכך — לפי בקשה.'),
         ('באילו שפות אתם עובדים?', 'עברית, אנגלית, צרפתית וספרדית, מול העובד ומול המשפחה. המסמכים המרכזיים (חוזה, פרוטוקולים, דוחות) ניתנים בגרסה דו־לשונית.'),
         ('מה ההבדל בינכם לבין סוכנות נדל״ן?', 'סוכנות מייצגת את בעל הנכס ומרוויחה מההשכרה. אנחנו עובדים בשביל העובד שלכם ומקבלים תשלום מכם: מחפשים בכל השוק, מנהלים משא ומתן בשבילו, בודקים את החוזה, ואחר כך מטפלים בכל מה שבא אחרי המפתחות — הליכים, בתי ספר, חוזים. כשאנחנו מלווים שוכר, איננו מקבלים דבר מבעל הנכס.')],
    home_case=('/he/corporate/#cas', 'למקרה הבוחן: משפחה שהתמקמה בחמישה שבועות ←'),
),
}


def logos(lang):
    p = P[lang]
    cells = ''.join(f'<div class="logo-ph">{p["logo"].format(n=n)}</div>' for n in range(1, 7))
    return f'''<!-- [LOGOS] : remplacer chaque cadre par <img src="/logos/client-N.svg" alt="Nom du client" width="140" height="48"> (accord écrit du client requis) -->
    <div class="logo-row">{cells}</div>'''


def testimonials(lang):
    p = P[lang]
    items = '\n'.join(f'''      <figure class="quote reveal"><p>{q}</p><figcaption><strong>{name}</strong> · {nat} · {job}</figcaption></figure>'''
                      for q, name, nat, job in p['testimonials'])
    return f'''<!-- [TÉMOIGNAGES] : textes réels uniquement, avec accord écrit de la personne -->
    <div class="quote-grid">
{items}
    </div>'''


def corporate_extra(lang):
    p = P[lang]
    kpis = ''.join(f'<div><strong>{a}</strong><span>{b}</span></div>' for a, b in p['kpis'])
    steps = ''.join(f'<li><strong>{a}</strong> — {b}</li>' for a, b in p['case_steps'])
    faq = '\n'.join(f'      <details><summary>{q}</summary><p>{a}</p></details>' for q, a in p['faq'])
    return f'''
<section class="v2-section alt" id="references">
  <div class="container">
    <p class="eyebrow">{p['logos_eyebrow']}</p>
    <h2>{p['logos_h2']}</h2>
    {logos(lang)}
    <article class="case" id="cas">
      <p class="eyebrow">{p['case_eyebrow']}</p>
      <h3>{p['case_h3']}</h3>
      <p>{p['case_ctx']}</p>
      <div class="case-kpis">{kpis}</div>
      <ol>{steps}</ol>
      <figure class="quote" style="margin-top:18px;border:none;padding:0"><p>{p['case_quote']}</p><figcaption>{p['case_quote_by']}</figcaption></figure>
    </article>
  </div>
</section>

<section class="v2-section" id="temoignages">
  <div class="container">
    <p class="eyebrow">{p['t_eyebrow']}</p>
    <h2>{p['t_h2']}</h2>
    {testimonials(lang)}
  </div>
</section>

<section class="v2-section alt" id="faq">
  <div class="container v2-faq">
    <p class="eyebrow">{p['faq_eyebrow']}</p>
    <h2>{p['faq_h2']}</h2>
{faq}
  </div>
</section>
'''


def home_proof(lang):
    """Section compacte insérée sur les accueils (styles inline + site-v2.css)."""
    p = P[lang]
    return f'''<!-- PREUVE ET CONFIANCE -->
<section class="pourquoi" id="references" style="padding-top:0">
  <div class="container">
    <p class="eyebrow reveal">{p['logos_eyebrow']}</p>
    <h2 class="reveal">{p['logos_h2']}</h2>
    {logos(lang)}
    {testimonials(lang)}
    <p class="gt-all reveal" style="margin-top:26px"><a href="{p['home_case'][0]}">{p['home_case'][1]}</a></p>
  </div>
</section>
'''
