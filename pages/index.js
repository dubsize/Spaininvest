import Head from 'next/head';
import { useState, useEffect } from 'react';

const C = {
  bg:      '#f5f0e8',
  card:    '#fffdf8',
  border:  '#e8e0d0',
  border2: '#d6cfc4',
  text:    '#1c1917',
  muted:   '#78716c',
  accent:  '#b45309',
  accentL: '#fef3c7',
  green:   '#15803d',
  red:     '#b91c1c',
};

const L = {
  en: {
    badge:       '🇪🇸 Spain rental investment analysis',
    hero1:       "You're about to sign a",
    hero2:       '€200,000 mortgage.',
    hero3:       'Know if the rent covers it.',
    sub:         "Paste any Spanish listing. Get the real net yield, estimated rent by district, and an investment score — in seconds. We did the data work so you don't have to.",
    ctaMain:     'Analyze a property — free',
    ctaHow:      'See how it works',
    noCard:      'No credit card. 2 free analyses.',
    howTitle:    'How it works',
    howSub:      'Three steps. Real numbers.',
    featTitle:   'What you get',
    featSub:     'Everything an analyst would charge €500 to tell you.',
    sampleTitle: 'Sample output',
    sampleSub:   'This is what you get.',
    pricingTitle:'Pricing',
    pricingSub:  'Start free. Pay when it matters.',
    readyTitle:  'Your next property analysis is one paste away.',
    readySub:    'No signup required to start. 2 free analyses, no credit card.',
    ctaFinal:    'Analyze a property — free →',
    tryFree:     'Try free →',
    footer:      'Rental investment analysis for Spain · Madrid · Barcelona · Valencia · Málaga',
    stats: [
      { value:'4.8%',   label:'Average gross yield',   sub:'Madrid 2025',        color:C.green   },
      { value:'+11.3%', label:'Rental price increase', sub:'Valencia YoY',       color:C.accent  },
      { value:'80+',    label:'Districts covered',     sub:'with live rent data', color:'#0369a1' },
    ],
    steps: [
      { n:'01', icon:'🔗', title:'Paste the listing URL',    desc:'Idealista, Fotocasa, Habitaclia — or paste the text directly, or upload photos.' },
      { n:'02', icon:'⚙️', title:'We run the numbers',       desc:'Estimated rent by district, net yield after tax, charges, IBI, vacancy — all computed instantly.' },
      { n:'03', icon:'📊', title:'You get the real verdict',  desc:'A 1–10 investment score, strengths, risks, and live INE market data. No guesswork.' },
    ],
    features: [
      { icon:'🏘', title:'District-level rent data',   desc:'80+ neighbourhoods across Madrid, Barcelona, Valencia and Málaga with min/max/median rent per m².' },
      { icon:'📈', title:'Net yield after tax',        desc:'Not just gross yield. We factor in charges, IBI, property management, vacancy and income tax.' },
      { icon:'📡', title:'Live INE & BdE data',        desc:'IRAV rent index, IPVA rental inflation, Euribor 12M and mortgage rates — updated automatically.' },
      { icon:'🏙', title:'Socio-demographic context',  desc:'District income, unemployment rate, tenant profile — so you know who will actually rent your flat.' },
      { icon:'⚖️', title:'Rent control alerts',        desc:"Barcelona's Ley de Contenció, IRAV legal cap, Málaga default risk — flagged automatically." },
      { icon:'📸', title:'3 input modes',              desc:'URL scraping, photo upload (2 images), or paste the listing text. Whatever works for you.' },
    ],
    plans: [
      { name:'Free',     price:'0€',  period:'',         desc:'2 analyses to get started',       cta:'Try for free' },
      { name:'Pass 24h', price:'9€',  period:'one-time', desc:'Unlimited analyses for 24 hours', cta:'Get the Pass' },
      { name:'Pro',      price:'19€', period:'/month',   desc:'Unlimited analyses, every month', cta:'Go Pro'       },
    ],
    sampleDistrict: 'Madrid · Malasaña',
    sampleAddr:     'Calle San Andrés, 2 bed / 65m²',
    sampleScore:    'GOOD BUY',
    sampleMetrics: [
      { l:'Est. rent',   v:'1,150 €/mo', c:C.accent },
      { l:'Gross yield', v:'4.31%',      c:C.text   },
      { l:'Net yield',   v:'3.12%',      c:C.green  },
      { l:'Net income',  v:'+9,984 €/yr',c:C.green  },
    ],
    strengths: ['High expat demand, Malasaña premium','Short walk to Metro L2 Noviciado','Strong short-term rental potential'],
    weaknesses:['Price per m² above district avg','Old building — possible ITE costs','IRAV cap limits rent increases to 2.2%'],
    strengthsLabel: 'Strengths',
    weaknessesLabel:'Risks',
    ready: 'Ready?',
  },
  fr: {
    badge:       '🇪🇸 Analyse d\'investissement locatif en Espagne',
    hero1:       'Vous êtes sur le point de signer un',
    hero2:       'crédit de 200 000 €.',
    hero3:       'Sachez si le loyer le couvre.',
    sub:         "Collez n'importe quelle annonce espagnole. Obtenez le rendement net réel, le loyer estimé par quartier et un score d'investissement — en quelques secondes. On a fait le travail de données à votre place.",
    ctaMain:     'Analyser un bien — gratuit',
    ctaHow:      'Voir comment ça marche',
    noCard:      'Sans carte bancaire. 2 analyses gratuites.',
    howTitle:    'Comment ça marche',
    howSub:      'Trois étapes. De vrais chiffres.',
    featTitle:   'Ce que vous obtenez',
    featSub:     'Tout ce qu\'un analyste vous facturerait 500 € à dire.',
    sampleTitle: 'Exemple de résultat',
    sampleSub:   'Voici ce que vous recevez.',
    pricingTitle:'Tarifs',
    pricingSub:  'Commencez gratuitement. Payez quand ça compte.',
    readyTitle:  'Votre prochaine analyse est à un collé-collé.',
    readySub:    'Aucune inscription requise. 2 analyses gratuites, sans carte.',
    ctaFinal:    'Analyser un bien — gratuit →',
    tryFree:     'Essai gratuit →',
    footer:      'Analyse d\'investissement locatif en Espagne · Madrid · Barcelone · Valence · Málaga',
    stats: [
      { value:'4.8%',   label:'Rendement brut moyen',   sub:'Madrid 2025',           color:C.green   },
      { value:'+11.3%', label:'Hausse des loyers',       sub:'Valence sur un an',     color:C.accent  },
      { value:'80+',    label:'Quartiers couverts',      sub:'avec données en direct', color:'#0369a1' },
    ],
    steps: [
      { n:'01', icon:'🔗', title:'Collez l\'URL de l\'annonce', desc:'Idealista, Fotocasa, Habitaclia — ou collez le texte directement, ou importez des photos.' },
      { n:'02', icon:'⚙️', title:'On fait les calculs',         desc:'Loyer estimé par quartier, rendement net après impôts, charges, IBI, vacance — calculés instantanément.' },
      { n:'03', icon:'📊', title:'Vous recevez le vrai verdict', desc:'Un score d\'investissement de 1 à 10, forces, risques et données INE en direct. Zéro approximation.' },
    ],
    features: [
      { icon:'🏘', title:'Loyers par quartier',           desc:'80+ quartiers à Madrid, Barcelone, Valence et Málaga avec les loyers min/médian/max au m².' },
      { icon:'📈', title:'Rendement net après impôts',    desc:'Pas seulement le brut. On intègre les charges, l\'IBI, la gestion, la vacance et l\'impôt sur le revenu.' },
      { icon:'📡', title:'Données INE & BdE en direct',   desc:'Indice IRAV, IPVA, Euribor 12M et taux de crédit — mis à jour automatiquement.' },
      { icon:'🏙', title:'Contexte socio-démographique',  desc:'Revenu du quartier, taux de chômage, profil locatif — pour savoir qui louera vraiment votre bien.' },
      { icon:'⚖️', title:'Alertes contrôle des loyers',   desc:'Ley de Contenció à Barcelone, plafond légal IRAV, risque Málaga — signalés automatiquement.' },
      { icon:'📸', title:'3 modes de saisie',             desc:'URL scraping, import photo (2 images) ou texte collé. Ce qui vous convient.' },
    ],
    plans: [
      { name:'Gratuit',  price:'0€',  period:'',         desc:'2 analyses pour démarrer',          cta:'Essayer gratuitement' },
      { name:'Pass 24h', price:'9€',  period:'unique',   desc:'Analyses illimitées pendant 24h',   cta:'Acheter le Pass'      },
      { name:'Pro',      price:'19€', period:'/mois',    desc:'Analyses illimitées chaque mois',   cta:'Passer en Pro'        },
    ],
    sampleDistrict: 'Madrid · Malasaña',
    sampleAddr:     'Calle San Andrés, 2 ch / 65m²',
    sampleScore:    'BON ACHAT',
    sampleMetrics: [
      { l:'Loyer estimé',     v:'1 150 €/mois', c:C.accent },
      { l:'Rendement brut',   v:'4,31%',         c:C.text   },
      { l:'Rendement net',    v:'3,12%',         c:C.green  },
      { l:'Revenus nets',     v:'+9 984 €/an',   c:C.green  },
    ],
    strengths: ['Forte demande expats, prime Malasaña','À pied du Metro L2 Noviciado','Fort potentiel locatif court terme'],
    weaknesses:['Prix au m² au-dessus de la moyenne du quartier','Ancien immeuble — possible ITE','Plafond IRAV limite la hausse à 2,2%'],
    strengthsLabel: 'Points forts',
    weaknessesLabel:'Risques',
    ready: 'Prêt ?',
  },
  es: {
    badge:       '🇪🇸 Análisis de inversión en alquiler en España',
    hero1:       'Estás a punto de firmar una',
    hero2:       'hipoteca de 200.000 €.',
    hero3:       'Sabe si el alquiler la cubre.',
    sub:         'Pega cualquier anuncio español. Obtén la rentabilidad neta real, el alquiler estimado por barrio y una puntuación de inversión — en segundos. Nosotros hacemos el trabajo de datos por ti.',
    ctaMain:     'Analizar un inmueble — gratis',
    ctaHow:      'Ver cómo funciona',
    noCard:      'Sin tarjeta de crédito. 2 análisis gratuitos.',
    howTitle:    'Cómo funciona',
    howSub:      'Tres pasos. Cifras reales.',
    featTitle:   'Lo que obtienes',
    featSub:     'Todo lo que un analista te cobraría 500 € por decirte.',
    sampleTitle: 'Ejemplo de resultado',
    sampleSub:   'Esto es lo que recibes.',
    pricingTitle:'Precios',
    pricingSub:  'Empieza gratis. Paga cuando importa.',
    readyTitle:  'Tu próximo análisis está a un pegado de distancia.',
    readySub:    'Sin registro previo. 2 análisis gratuitos, sin tarjeta.',
    ctaFinal:    'Analizar un inmueble — gratis →',
    tryFree:     'Prueba gratis →',
    footer:      'Análisis de inversión en alquiler en España · Madrid · Barcelona · Valencia · Málaga',
    stats: [
      { value:'4.8%',   label:'Rentabilidad bruta media', sub:'Madrid 2025',          color:C.green   },
      { value:'+11.3%', label:'Subida del alquiler',      sub:'Valencia interanual',  color:C.accent  },
      { value:'80+',    label:'Barrios cubiertos',        sub:'con datos en directo',  color:'#0369a1' },
    ],
    steps: [
      { n:'01', icon:'🔗', title:'Pega la URL del anuncio',   desc:'Idealista, Fotocasa, Habitaclia — o pega el texto directamente, o sube fotos.' },
      { n:'02', icon:'⚙️', title:'Hacemos los cálculos',      desc:'Alquiler estimado por barrio, rentabilidad neta tras impuestos, gastos, IBI, vacancia — calculado al instante.' },
      { n:'03', icon:'📊', title:'Recibes el veredicto real',  desc:'Una puntuación de inversión del 1 al 10, fortalezas, riesgos y datos INE en directo. Sin suposiciones.' },
    ],
    features: [
      { icon:'🏘', title:'Alquileres por barrio',          desc:'Más de 80 barrios en Madrid, Barcelona, Valencia y Málaga con alquiler mín/mediana/máx por m².' },
      { icon:'📈', title:'Rentabilidad neta tras impuestos',desc:'No solo la bruta. Incluimos gastos, IBI, gestión, vacancia e impuesto sobre la renta.' },
      { icon:'📡', title:'Datos INE y BdE en directo',     desc:'Índice IRAV, IPVA, Euribor 12M y tipos hipotecarios — actualizados automáticamente.' },
      { icon:'🏙', title:'Contexto sociodemográfico',      desc:'Renta del barrio, tasa de desempleo, perfil del inquilino — para saber quién alquilará realmente.' },
      { icon:'⚖️', title:'Alertas control de alquileres',  desc:'Ley de Contención en Barcelona, límite legal IRAV, riesgo Málaga — señalados automáticamente.' },
      { icon:'📸', title:'3 modos de entrada',             desc:'Scraping de URL, subida de foto (2 imágenes) o texto pegado. Lo que te convenga.' },
    ],
    plans: [
      { name:'Gratis',   price:'0€',  period:'',       desc:'2 análisis para empezar',           cta:'Probar gratis'   },
      { name:'Pass 24h', price:'9€',  period:'único',  desc:'Análisis ilimitados durante 24h',   cta:'Comprar el Pass' },
      { name:'Pro',      price:'19€', period:'/mes',   desc:'Análisis ilimitados cada mes',      cta:'Pasarse a Pro'   },
    ],
    sampleDistrict: 'Madrid · Malasaña',
    sampleAddr:     'Calle San Andrés, 2 hab / 65m²',
    sampleScore:    'BUENA COMPRA',
    sampleMetrics: [
      { l:'Alquiler est.',     v:'1.150 €/mes', c:C.accent },
      { l:'Rentab. bruta',     v:'4,31%',       c:C.text   },
      { l:'Rentab. neta',      v:'3,12%',       c:C.green  },
      { l:'Ingresos netos',    v:'+9.984 €/año',c:C.green  },
    ],
    strengths: ['Alta demanda expats, prima Malasaña','A pie del Metro L2 Noviciado','Fuerte potencial alquiler a corto plazo'],
    weaknesses:['Precio m² por encima de la media del barrio','Edificio antiguo — posible ITE','Límite IRAV restringe subida al 2,2%'],
    strengthsLabel: 'Fortalezas',
    weaknessesLabel:'Riesgos',
    ready: '¿Listo?',
  },
};

function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState('—');
  useEffect(() => {
    const num = parseFloat(value.replace(/[^0-9.]/g, ''));
    const prefix = value.match(/^[^0-9]*/)?.[0] || '';
    const suffix = value.match(/[^0-9.]+$/)?.[0] || '';
    if (isNaN(num)) { setDisplay(value); return; }
    let start = 0;
    const steps2 = 60;
    const inc = num / steps2;
    let count = 0;
    const timer = setInterval(() => {
      count++;
      start += inc;
      if (count >= steps2) { setDisplay(value); clearInterval(timer); return; }
      setDisplay(prefix + start.toFixed(suffix === '%' ? 1 : 0) + suffix);
    }, 1400 / steps2);
    return () => clearInterval(timer);
  }, [value]);
  return <span>{display}</span>;
}

export default function Landing() {
  const [lang, setLang] = useState('en');

  useEffect(() => {
    const nav = navigator.language || navigator.userLanguage || 'en';
    const code = nav.slice(0, 2).toLowerCase();
    if (code === 'fr') setLang('fr');
    else if (code === 'es') setLang('es');
    else setLang('en');
  }, []);

  const t = L[lang];

  return (
    <>
      <Head>
        <title>buy2rent.io — Rental Investment Analysis Spain</title>
        <meta name="description" content="Analyze any Spanish property listing and get instant rental yield, market rent estimate and investment score. Madrid, Barcelona, Valencia, Málaga."/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <link rel="icon" href="/favicon.ico"/>
        <meta property="og:title" content="buy2rent.io — Know if the rent covers the mortgage."/>
        <meta property="og:description" content="Paste any Idealista listing. Get net yield, estimated rent and investment score instantly."/>
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true"/>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
        <script dangerouslySetInnerHTML={{__html:`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-WSVSC97J');`}}/>
        <style>{`
          *{box-sizing:border-box;margin:0;padding:0}
          body{background:${C.bg};font-family:'DM Sans',sans-serif;color:${C.text}}
          @keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
          .fu{animation:fadeUp 0.7s cubic-bezier(.22,1,.36,1) both}
          .cta-btn{transition:all 0.2s ease}
          .cta-btn:hover{transform:translateY(-2px);box-shadow:0 12px 32px rgba(180,83,9,0.35)!important}
          .fc{transition:all 0.2s ease}
          .fc:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(0,0,0,0.08)!important}
          .lang-btn{transition:all 0.15s ease}
          .lang-btn:hover{color:#b45309!important}
        `}</style>
      </Head>
      <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WSVSC97J" height="0" width="0" style={{display:'none',visibility:'hidden'}}></iframe></noscript>

      <div style={{maxWidth:900,margin:'0 auto',padding:'0 24px'}}>

        {/* NAV */}
        <nav style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'26px 0',borderBottom:`1px solid ${C.border}`}}>
          <div style={{fontFamily:'Playfair Display,serif',fontSize:22,fontWeight:900,letterSpacing:-0.5}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </div>
          <div style={{display:'flex',alignItems:'center',gap:16}}>
            {/* Language switcher */}
            <div style={{display:'flex',gap:4,background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:3}}>
              {['en','fr','es'].map(l => (
                <button key={l} className="lang-btn" onClick={()=>setLang(l)} style={{
                  padding:'5px 12px',borderRadius:7,border:'none',cursor:'pointer',
                  background:lang===l?C.accent:'transparent',
                  color:lang===l?'#fff':C.muted,
                  fontSize:13,fontWeight:700,textTransform:'uppercase',letterSpacing:0.5,
                }}>{l}</button>
              ))}
            </div>
            <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'10px 22px',borderRadius:10,fontSize:15,fontWeight:600,textDecoration:'none',boxShadow:'0 4px 14px rgba(180,83,9,0.25)'}}>
              {t.tryFree}
            </a>
          </div>
        </nav>

        {/* HERO */}
        <section style={{padding:'76px 0 60px',textAlign:'center'}}>
          <div className="fu" style={{animationDelay:'0.05s',display:'inline-block',background:C.accentL,border:`1px solid #fde68a`,borderRadius:20,padding:'6px 16px',fontSize:13,color:C.accent,fontWeight:600,marginBottom:26,letterSpacing:0.5}}>
            {t.badge}
          </div>
          <h1 className="fu" style={{animationDelay:'0.15s',fontFamily:'Playfair Display,serif',fontSize:'clamp(34px,6vw,62px)',fontWeight:900,lineHeight:1.1,letterSpacing:-1.5,color:C.text,marginBottom:22,maxWidth:740,marginLeft:'auto',marginRight:'auto'}}>
            {t.hero1}<br/><span style={{color:C.accent}}>{t.hero2}</span><br/>{t.hero3}
          </h1>
          <p className="fu" style={{animationDelay:'0.28s',fontSize:18,color:C.muted,lineHeight:1.7,maxWidth:520,margin:'0 auto 40px'}}>
            {t.sub}
          </p>
          <div className="fu" style={{animationDelay:'0.38s',display:'flex',gap:12,justifyContent:'center',flexWrap:'wrap',marginBottom:14}}>
            <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'16px 36px',borderRadius:14,fontSize:17,fontWeight:700,textDecoration:'none',boxShadow:'0 6px 22px rgba(180,83,9,0.28)'}}>
              {t.ctaMain}
            </a>
            <a href="#how" style={{background:C.card,color:C.muted,padding:'16px 26px',borderRadius:14,fontSize:17,fontWeight:500,textDecoration:'none',border:`1px solid ${C.border}`}}>
              {t.ctaHow}
            </a>
          </div>
          <div className="fu" style={{animationDelay:'0.45s',fontSize:13,color:C.muted}}>{t.noCard}</div>
        </section>

        {/* STATS */}
        <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16,marginBottom:80}}>
          {t.stats.map((s,i)=>(
            <div key={i} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:18,padding:'28px 20px',textAlign:'center'}}>
              <div style={{fontFamily:'Playfair Display,serif',fontSize:48,fontWeight:900,color:s.color,lineHeight:1}}>
                <AnimatedNumber value={s.value}/>
              </div>
              <div style={{fontSize:15,fontWeight:600,color:C.text,marginTop:8}}>{s.label}</div>
              <div style={{fontSize:13,color:C.muted,marginTop:3}}>{s.sub}</div>
            </div>
          ))}
        </section>

        {/* HOW IT WORKS */}
        <section id="how" style={{marginBottom:84}}>
          <div style={{textAlign:'center',marginBottom:44}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>{t.howTitle}</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>{t.howSub}</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))',gap:18}}>
            {t.steps.map((s,i)=>(
              <div key={i} className="fc" style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:20,padding:26,position:'relative',overflow:'hidden'}}>
                <div style={{position:'absolute',top:14,right:18,fontFamily:'Playfair Display,serif',fontSize:56,fontWeight:900,color:C.border,lineHeight:1,userSelect:'none'}}>{s.n}</div>
                <div style={{fontSize:30,marginBottom:12}}>{s.icon}</div>
                <div style={{fontSize:16,fontWeight:700,color:C.text,marginBottom:7}}>{s.title}</div>
                <div style={{fontSize:14,color:C.muted,lineHeight:1.6}}>{s.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* FEATURES */}
        <section style={{marginBottom:84}}>
          <div style={{textAlign:'center',marginBottom:44}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>{t.featTitle}</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text,lineHeight:1.2}}>{t.featSub}</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(255px,1fr))',gap:14}}>
            {t.features.map((f,i)=>(
              <div key={i} className="fc" style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:16,padding:22}}>
                <div style={{fontSize:26,marginBottom:10}}>{f.icon}</div>
                <div style={{fontSize:15,fontWeight:700,color:C.text,marginBottom:5}}>{f.title}</div>
                <div style={{fontSize:14,color:C.muted,lineHeight:1.6}}>{f.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* SAMPLE OUTPUT */}
        <section style={{marginBottom:84}}>
          <div style={{textAlign:'center',marginBottom:40}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>{t.sampleTitle}</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>{t.sampleSub}</h2>
          </div>
          <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:24,padding:28,boxShadow:'0 4px 28px rgba(0,0,0,0.05)'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:14,marginBottom:22,paddingBottom:22,borderBottom:`1px solid ${C.border}`}}>
              <div>
                <div style={{fontSize:11,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:5}}>{t.sampleDistrict}</div>
                <div style={{fontSize:20,fontWeight:800,color:C.text,marginBottom:4}}>{t.sampleAddr}</div>
                <div style={{fontSize:26,fontWeight:800,color:C.text}}>320.000 € <span style={{fontSize:15,color:C.muted,fontWeight:400}}>4.923 €/m²</span></div>
              </div>
              <div style={{background:C.accentL,border:`1px solid #fde68a`,borderRadius:14,padding:'14px 18px',textAlign:'center',flexShrink:0}}>
                <div style={{fontSize:11,color:C.accent,fontWeight:700,letterSpacing:1,marginBottom:2}}>SCORE</div>
                <div style={{fontFamily:'Playfair Display,serif',fontSize:40,fontWeight:900,color:C.accent,lineHeight:1}}>7.2</div>
                <div style={{fontSize:11,color:C.muted,marginTop:2}}>{t.sampleScore}</div>
              </div>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(130px,1fr))',gap:10,marginBottom:18}}>
              {t.sampleMetrics.map((m,i)=>(
                <div key={i} style={{background:C.bg,borderRadius:10,padding:'12px 14px'}}>
                  <div style={{fontSize:11,color:C.muted,fontWeight:600,marginBottom:3}}>{m.l}</div>
                  <div style={{fontSize:18,fontWeight:800,color:m.c}}>{m.v}</div>
                </div>
              ))}
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
              <div style={{background:'#f0fdf4',border:'1px solid #bbf7d0',borderRadius:12,padding:14}}>
                <div style={{fontSize:11,color:C.green,fontWeight:700,letterSpacing:1,textTransform:'uppercase',marginBottom:7}}>{t.strengthsLabel}</div>
                {t.strengths.map((p,i)=>(
                  <div key={i} style={{fontSize:12,color:'#166534',padding:'2px 0',display:'flex',gap:6}}><span style={{color:C.green,fontWeight:700}}>+</span>{p}</div>
                ))}
              </div>
              <div style={{background:'#fff5f5',border:'1px solid #fecaca',borderRadius:12,padding:14}}>
                <div style={{fontSize:11,color:C.red,fontWeight:700,letterSpacing:1,textTransform:'uppercase',marginBottom:7}}>{t.weaknessesLabel}</div>
                {t.weaknesses.map((p,i)=>(
                  <div key={i} style={{fontSize:12,color:'#991b1b',padding:'2px 0',display:'flex',gap:6}}><span style={{color:C.red,fontWeight:700}}>−</span>{p}</div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* PRICING */}
        <section style={{marginBottom:84}}>
          <div style={{textAlign:'center',marginBottom:44}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>{t.pricingTitle}</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>{t.pricingSub}</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:14}}>
            {t.plans.map((p,i)=>(
              <div key={i} className="fc" style={{background:i===2?C.accent:C.card,border:`1px solid ${i===2?C.accent:C.border}`,borderRadius:20,padding:26,display:'flex',flexDirection:'column',gap:10}}>
                <div style={{fontSize:11,fontWeight:700,color:i===2?'rgba(255,255,255,0.7)':C.muted,letterSpacing:2,textTransform:'uppercase'}}>{p.name}</div>
                <div style={{fontFamily:'Playfair Display,serif',fontSize:44,fontWeight:900,color:i===2?'#fff':C.text,lineHeight:1}}>
                  {p.price}<span style={{fontSize:15,fontWeight:400,color:i===2?'rgba(255,255,255,0.6)':C.muted}}> {p.period}</span>
                </div>
                <div style={{fontSize:14,color:i===2?'rgba(255,255,255,0.8)':C.muted,lineHeight:1.5,flex:1}}>{p.desc}</div>
                <a href="/app" className="cta-btn" style={{
                  display:'block',textAlign:'center',padding:'12px',borderRadius:11,
                  background:i===2?'#fff':'transparent',
                  border:`1px solid ${i===2?'transparent':C.border2}`,
                  color:i===2?C.accent:C.muted,
                  fontSize:14,fontWeight:700,textDecoration:'none',
                }}>
                  {p.cta}
                </a>
              </div>
            ))}
          </div>
        </section>

        {/* FINAL CTA */}
        <section style={{marginBottom:80,background:C.text,borderRadius:24,padding:'52px 36px',textAlign:'center'}}>
          <div style={{fontSize:11,letterSpacing:3,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',fontWeight:700,marginBottom:14}}>{t.ready}</div>
          <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,42px)',fontWeight:900,color:'#fff',letterSpacing:-0.5,marginBottom:14,lineHeight:1.2}}>
            {t.readyTitle}
          </h2>
          <p style={{fontSize:16,color:'rgba(255,255,255,0.55)',marginBottom:32,lineHeight:1.6}}>{t.readySub}</p>
          <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'17px 42px',borderRadius:14,fontSize:17,fontWeight:700,textDecoration:'none',boxShadow:'0 6px 22px rgba(180,83,9,0.4)',display:'inline-block'}}>
            {t.ctaFinal}
          </a>
        </section>

        {/* FOOTER */}
        <footer style={{textAlign:'center',paddingBottom:36,borderTop:`1px solid ${C.border}`,paddingTop:24}}>
          <div style={{fontFamily:'Playfair Display,serif',fontSize:18,fontWeight:900,color:C.text,marginBottom:6}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </div>
          <div style={{fontSize:13,color:C.muted}}>{t.footer}</div>
          <div style={{fontSize:12,color:C.muted,marginTop:5}}>© 2026 buy2rent.io</div>
        </footer>

      </div>
    </>
  );
}
