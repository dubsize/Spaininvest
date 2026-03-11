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

const stats = [
  { value: '4.8%',   label: 'Average gross yield',      sub: 'Madrid 2025',       color: C.green   },
  { value: '+11.3%', label: 'Rental price increase',    sub: 'Valencia YoY',      color: C.accent  },
  { value: '80+',    label: 'Districts covered',        sub: 'with live rent data',color: '#0369a1' },
];

const steps = [
  { n:'01', icon:'🔗', title:'Paste the listing URL',   desc:'Idealista, Fotocasa, Habitaclia — or paste the text directly, or upload photos.' },
  { n:'02', icon:'⚙️', title:'We run the numbers',      desc:'Estimated rent by district, net yield after tax, charges, IBI, vacancy — all computed instantly.' },
  { n:'03', icon:'📊', title:'You get the real verdict', desc:'A 1–10 investment score, strengths, risks, and live INE market data. No guesswork.' },
];

const features = [
  { icon:'🏘', title:'District-level rent data',    desc:'80+ neighbourhoods across Madrid, Barcelona, Valencia and Málaga with min/max/median rent per m².' },
  { icon:'📈', title:'Net yield after tax',         desc:'Not just gross yield. We factor in charges, IBI, property management, vacancy and income tax.' },
  { icon:'📡', title:'Live INE & BdE data',         desc:'IRAV rent index, IPVA rental inflation, Euribor 12M and mortgage rates — updated automatically.' },
  { icon:'🏙', title:'Socio-demographic context',   desc:'District income, unemployment rate, tenant profile — so you know who will actually rent your flat.' },
  { icon:'⚖️', title:'Rent control alerts',         desc:"Barcelona's Ley de Contenció, IRAV legal cap, Málaga default risk — flagged automatically." },
  { icon:'📸', title:'3 input modes',               desc:'URL scraping, photo upload (2 images), or paste the listing text. Whatever works for you.' },
];

const plans = [
  { name:'Free',     price:'0€',  period:'',       desc:'2 analyses to get started',        cta:'Try for free',   href:'/app', highlight:false },
  { name:'Pass 24h', price:'9€',  period:'one-time',desc:'Unlimited analyses for 24 hours',  cta:'Get the Pass',   href:'/app', highlight:false },
  { name:'Pro',      price:'19€', period:'/month',  desc:'Unlimited analyses, every month',  cta:'Go Pro',         href:'/app', highlight:true  },
];

function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState('—');
  useEffect(() => {
    const num = parseFloat(value.replace(/[^0-9.]/g, ''));
    const prefix = value.match(/^[^0-9]*/)?.[0] || '';
    const suffix = value.match(/[^0-9.]+$/)?.[0] || '';
    if (isNaN(num)) { setDisplay(value); return; }
    let start = 0;
    const duration = 1400;
    const steps2 = 60;
    const inc = num / steps2;
    let count = 0;
    const timer = setInterval(() => {
      count++;
      start += inc;
      if (count >= steps2) { setDisplay(value); clearInterval(timer); return; }
      setDisplay(prefix + start.toFixed(suffix === '%' ? 1 : 0) + suffix);
    }, duration / steps2);
    return () => clearInterval(timer);
  }, [value]);
  return <span>{display}</span>;
}

export default function Landing() {
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
        `}</style>
      </Head>
      <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WSVSC97J" height="0" width="0" style={{display:'none',visibility:'hidden'}}></iframe></noscript>

      <div style={{maxWidth:900,margin:'0 auto',padding:'0 24px'}}>

        {/* NAV */}
        <nav style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'26px 0',borderBottom:`1px solid ${C.border}`}}>
          <div style={{fontFamily:'Playfair Display,serif',fontSize:22,fontWeight:900,letterSpacing:-0.5}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </div>
          <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'10px 22px',borderRadius:10,fontSize:15,fontWeight:600,textDecoration:'none',boxShadow:'0 4px 14px rgba(180,83,9,0.25)'}}>
            Try free →
          </a>
        </nav>

        {/* HERO */}
        <section style={{padding:'76px 0 60px',textAlign:'center'}}>
          <div className="fu" style={{animationDelay:'0.05s',display:'inline-block',background:C.accentL,border:`1px solid #fde68a`,borderRadius:20,padding:'6px 16px',fontSize:13,color:C.accent,fontWeight:600,marginBottom:26,letterSpacing:0.5}}>
            🇪🇸 Spain rental investment analysis
          </div>
          <h1 className="fu" style={{animationDelay:'0.15s',fontFamily:'Playfair Display,serif',fontSize:'clamp(36px,6vw,64px)',fontWeight:900,lineHeight:1.1,letterSpacing:-1.5,color:C.text,marginBottom:22,maxWidth:740,marginLeft:'auto',marginRight:'auto'}}>
            You're about to sign a<br/><span style={{color:C.accent}}>€200,000 mortgage.</span><br/>Know if the rent covers it.
          </h1>
          <p className="fu" style={{animationDelay:'0.28s',fontSize:18,color:C.muted,lineHeight:1.7,maxWidth:520,margin:'0 auto 40px'}}>
            Paste any Spanish listing. Get the real net yield, estimated rent by district, and an investment score — in seconds. We did the data work so you don't have to.
          </p>
          <div className="fu" style={{animationDelay:'0.38s',display:'flex',gap:12,justifyContent:'center',flexWrap:'wrap',marginBottom:14}}>
            <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'16px 36px',borderRadius:14,fontSize:17,fontWeight:700,textDecoration:'none',boxShadow:'0 6px 22px rgba(180,83,9,0.28)'}}>
              Analyze a property — free
            </a>
            <a href="#how" style={{background:C.card,color:C.muted,padding:'16px 26px',borderRadius:14,fontSize:17,fontWeight:500,textDecoration:'none',border:`1px solid ${C.border}`}}>
              See how it works
            </a>
          </div>
          <div className="fu" style={{animationDelay:'0.45s',fontSize:13,color:C.muted}}>No credit card. 2 free analyses.</div>
        </section>

        {/* STATS */}
        <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16,marginBottom:80}}>
          {stats.map((s,i)=>(
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
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>How it works</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>Three steps. Real numbers.</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))',gap:18}}>
            {steps.map((s,i)=>(
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
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>What you get</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text,lineHeight:1.2}}>Everything an analyst would charge<br/>€500 to tell you.</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(255px,1fr))',gap:14}}>
            {features.map((f,i)=>(
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
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>Sample output</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>This is what you get.</h2>
          </div>
          <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:24,padding:28,boxShadow:'0 4px 28px rgba(0,0,0,0.05)'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:14,marginBottom:22,paddingBottom:22,borderBottom:`1px solid ${C.border}`}}>
              <div>
                <div style={{fontSize:11,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:5}}>Madrid · Malasaña</div>
                <div style={{fontSize:20,fontWeight:800,color:C.text,marginBottom:4}}>Calle San Andrés, 2 bed / 65m²</div>
                <div style={{fontSize:26,fontWeight:800,color:C.text}}>320,000 € <span style={{fontSize:15,color:C.muted,fontWeight:400}}>4,923 €/m²</span></div>
              </div>
              <div style={{background:C.accentL,border:`1px solid #fde68a`,borderRadius:14,padding:'14px 18px',textAlign:'center',flexShrink:0}}>
                <div style={{fontSize:11,color:C.accent,fontWeight:700,letterSpacing:1,marginBottom:2}}>SCORE</div>
                <div style={{fontFamily:'Playfair Display,serif',fontSize:40,fontWeight:900,color:C.accent,lineHeight:1}}>7.2</div>
                <div style={{fontSize:11,color:C.muted,marginTop:2}}>GOOD BUY</div>
              </div>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(130px,1fr))',gap:10,marginBottom:18}}>
              {[
                {l:'Est. rent',   v:'1,150 €/mo', c:C.accent},
                {l:'Gross yield', v:'4.31%',       c:C.text},
                {l:'Net yield',   v:'3.12%',       c:C.green},
                {l:'Net income',  v:'+9,984 €/yr', c:C.green},
              ].map((m,i)=>(
                <div key={i} style={{background:C.bg,borderRadius:10,padding:'12px 14px'}}>
                  <div style={{fontSize:11,color:C.muted,fontWeight:600,marginBottom:3}}>{m.l}</div>
                  <div style={{fontSize:18,fontWeight:800,color:m.c}}>{m.v}</div>
                </div>
              ))}
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
              <div style={{background:'#f0fdf4',border:'1px solid #bbf7d0',borderRadius:12,padding:14}}>
                <div style={{fontSize:11,color:C.green,fontWeight:700,letterSpacing:1,textTransform:'uppercase',marginBottom:7}}>Strengths</div>
                {['High expat demand, Malasaña premium','Short walk to Metro L2 Noviciado','Strong short-term rental potential'].map((p,i)=>(
                  <div key={i} style={{fontSize:12,color:'#166534',padding:'2px 0',display:'flex',gap:6}}><span style={{color:C.green,fontWeight:700}}>+</span>{p}</div>
                ))}
              </div>
              <div style={{background:'#fff5f5',border:'1px solid #fecaca',borderRadius:12,padding:14}}>
                <div style={{fontSize:11,color:C.red,fontWeight:700,letterSpacing:1,textTransform:'uppercase',marginBottom:7}}>Risks</div>
                {['Price per m² above district avg','Old building — possible ITE costs','IRAV cap limits rent increases to 2.2%'].map((p,i)=>(
                  <div key={i} style={{fontSize:12,color:'#991b1b',padding:'2px 0',display:'flex',gap:6}}><span style={{color:C.red,fontWeight:700}}>−</span>{p}</div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* PRICING */}
        <section style={{marginBottom:84}}>
          <div style={{textAlign:'center',marginBottom:44}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:10}}>Pricing</div>
            <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,40px)',fontWeight:900,letterSpacing:-0.5,color:C.text}}>Start free. Pay when it matters.</h2>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:14}}>
            {plans.map((p,i)=>(
              <div key={i} className="fc" style={{background:p.highlight?C.accent:C.card,border:`1px solid ${p.highlight?C.accent:C.border}`,borderRadius:20,padding:26,display:'flex',flexDirection:'column',gap:10}}>
                <div style={{fontSize:11,fontWeight:700,color:p.highlight?'rgba(255,255,255,0.7)':C.muted,letterSpacing:2,textTransform:'uppercase'}}>{p.name}</div>
                <div style={{fontFamily:'Playfair Display,serif',fontSize:44,fontWeight:900,color:p.highlight?'#fff':C.text,lineHeight:1}}>
                  {p.price}<span style={{fontSize:15,fontWeight:400,color:p.highlight?'rgba(255,255,255,0.6)':C.muted}}> {p.period}</span>
                </div>
                <div style={{fontSize:14,color:p.highlight?'rgba(255,255,255,0.8)':C.muted,lineHeight:1.5,flex:1}}>{p.desc}</div>
                <a href={p.href} className="cta-btn" style={{
                  display:'block',textAlign:'center',padding:'12px',borderRadius:11,
                  background:p.highlight?'#fff':'transparent',
                  border:`1px solid ${p.highlight?'transparent':C.border2}`,
                  color:p.highlight?C.accent:C.muted,
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
          <div style={{fontSize:11,letterSpacing:3,color:'rgba(255,255,255,0.4)',textTransform:'uppercase',fontWeight:700,marginBottom:14}}>Ready?</div>
          <h2 style={{fontFamily:'Playfair Display,serif',fontSize:'clamp(26px,4vw,42px)',fontWeight:900,color:'#fff',letterSpacing:-0.5,marginBottom:14,lineHeight:1.2}}>
            Your next property analysis<br/>is one paste away.
          </h2>
          <p style={{fontSize:16,color:'rgba(255,255,255,0.55)',marginBottom:32,lineHeight:1.6}}>
            No signup required to start. 2 free analyses, no credit card.
          </p>
          <a href="/app" className="cta-btn" style={{background:C.accent,color:'#fff',padding:'17px 42px',borderRadius:14,fontSize:17,fontWeight:700,textDecoration:'none',boxShadow:'0 6px 22px rgba(180,83,9,0.4)',display:'inline-block'}}>
            Analyze a property — free →
          </a>
        </section>

        {/* FOOTER */}
        <footer style={{textAlign:'center',paddingBottom:36,borderTop:`1px solid ${C.border}`,paddingTop:24}}>
          <div style={{fontFamily:'Playfair Display,serif',fontSize:18,fontWeight:900,color:C.text,marginBottom:6}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </div>
          <div style={{fontSize:13,color:C.muted}}>Rental investment analysis for Spain · Madrid · Barcelona · Valencia · Málaga</div>
          <div style={{fontSize:12,color:C.muted,marginTop:5}}>© 2026 buy2rent.io</div>
        </footer>

      </div>
    </>
  );
}
