import { useState, useEffect } from 'react';
import Head from 'next/head';
import T from '../components/translations';

// ─── Colors ───────────────────────────────────────────────
const C = {
  bg:       '#f5f0e8',
  card:     '#fffdf8',
  border:   '#e8e0d0',
  border2:  '#d6cfc4',
  text:     '#1c1917',
  muted:    '#78716c',
  accent:   '#b45309',
  accentBg: '#fef3c7',
  green:    '#15803d',
  red:      '#b91c1c',
  tag:      '#92400e',
};

const CITY_COLORS = {
  'Madrid':    '#d97706',
  'Barcelona': '#db2777',
  'Valencia':  '#059669',
  'Málaga':    '#2563eb',
};

// ─── Utilities ────────────────────────────────────────────
function stripHtml(html) {
  if (typeof document === 'undefined') return html;
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  tmp.querySelectorAll('script,style,nav,footer,header').forEach(el => el.remove());
  return tmp.innerText.replace(/\s{3,}/g, '\n\n').trim().slice(0, 8000);
}

async function fetchViaProxy(url) {
  // Call ScraperAPI directly from browser (avoids Vercel timeout limits)
  const SCRAPER_KEY = 'f5779bfd8d4a12533930560ac6faca10';
  const scraperUrl = `http://api.scraperapi.com?api_key=${SCRAPER_KEY}&url=${encodeURIComponent(url)}&country_code=es&render=false`;
  try {
    const res = await fetch(scraperUrl, { signal: AbortSignal.timeout(40000) });
    if (!res.ok) throw new Error('proxy_failed');
    const html = await res.text();
    if (html.length < 500) throw new Error('proxy_failed');
    return html
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 8000);
  } catch(e) {
    throw new Error('proxy_failed');
  }
}

// ─── Email Gate Modal ─────────────────────────────────────
function EmailModal({ t, onConfirm, onClose, loading, error }) {
  const [email, setEmail] = useState('');
  const valid = email.includes('@') && email.includes('.');

  return (
    <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.4)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center',padding:24}}>
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:24,padding:40,maxWidth:460,width:'100%',boxShadow:'0 20px 60px rgba(0,0,0,0.15)',animation:'fadeUp 0.3s ease both'}}>
        <div style={{textAlign:'center',marginBottom:28}}>
          <div style={{fontSize:40,marginBottom:12}}>🏠</div>
          <h2 style={{fontSize:24,fontWeight:800,color:C.text,marginBottom:8}}>{t.emailTitle}</h2>
          <p style={{fontSize:15,color:C.muted,lineHeight:1.6}}>{t.emailSubtitle}</p>
        </div>
        <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:14,padding:'12px 16px',marginBottom:20,fontSize:13,color:C.tag,textAlign:'center',fontWeight:600}}>
          ✨ {t.emailFreeOffer}
        </div>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && valid && !loading && onConfirm(email)}
          placeholder={t.emailPlaceholder}
          autoFocus
          style={{width:'100%',background:C.bg,border:`1px solid ${valid?C.accent:C.border2}`,borderRadius:12,padding:'14px 16px',color:C.text,fontSize:15,marginBottom:12,transition:'border-color 0.2s'}}
        />
        {error && <div style={{fontSize:13,color:C.red,marginBottom:12,textAlign:'center'}}>⚠️ {error}</div>}
        <button onClick={() => onConfirm(email)} disabled={!valid||loading} style={{
          width:'100%',padding:'16px',borderRadius:12,border:'none',
          background:valid&&!loading?C.accent:C.border,
          color:valid&&!loading?'#fff':C.muted,fontSize:15,fontWeight:800,
          cursor:valid&&!loading?'pointer':'not-allowed',transition:'all 0.2s',
          display:'flex',alignItems:'center',justifyContent:'center',gap:10,
          boxShadow:valid&&!loading?'0 4px 16px rgba(180,83,9,0.3)':'none'
        }}>
          {loading?<><div style={{width:18,height:18,border:'2px solid #fff',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>{t.emailLoading}</>:t.emailCta}
        </button>
        <p style={{textAlign:'center',fontSize:11,color:C.muted,marginTop:12,lineHeight:1.5}}>{t.emailPrivacy}</p>
      </div>
    </div>
  );
}

// ─── Quota Exceeded Modal ─────────────────────────────────
function QuotaModal({ t, onClose }) {
  return (
    <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.4)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center',padding:24}}>
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:24,padding:40,maxWidth:460,width:'100%',boxShadow:'0 20px 60px rgba(0,0,0,0.15)',animation:'fadeUp 0.3s ease both',textAlign:'center'}}>
        <div style={{fontSize:40,marginBottom:16}}>🔒</div>
        <h2 style={{fontSize:24,fontWeight:800,color:C.text,marginBottom:10}}>{t.quotaTitle}</h2>
        <p style={{fontSize:15,color:C.muted,lineHeight:1.6,marginBottom:24}}>{t.quotaSubtitle}</p>
        <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:16,padding:20,marginBottom:24}}>
          <div style={{fontSize:28,fontWeight:800,color:C.accent,marginBottom:4}}>19€ <span style={{fontSize:14,fontWeight:400,color:C.muted}}>{t.quotaPerMonth}</span></div>
          <div style={{fontSize:13,color:C.tag}}>{t.quotaUnlimited}</div>
        </div>
        <button style={{width:'100%',padding:'16px',borderRadius:12,border:'none',background:C.accent,color:'#fff',fontSize:15,fontWeight:800,cursor:'pointer',boxShadow:'0 4px 16px rgba(180,83,9,0.3)',marginBottom:12}}>
          {t.quotaCta}
        </button>
        <button onClick={onClose} style={{width:'100%',padding:'12px',borderRadius:12,border:`1px solid ${C.border2}`,background:'transparent',color:C.muted,fontSize:13,cursor:'pointer'}}>
          {t.quotaClose}
        </button>
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────
function ScoreGauge({ score, t, size = 110 }) {
  const r = size * 0.38, circ = 2 * Math.PI * r, fill = (score / 10) * circ;
  const color = score >= 7 ? C.green : score >= 5 ? '#d97706' : score >= 3 ? '#ea580c' : C.red;
  const label = score >= 7 ? t.score.good : score >= 5 ? t.score.avg : score >= 3 ? t.score.weak : t.score.avoid;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={C.border} strokeWidth={size*0.08}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.08}
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`} style={{transition:'stroke-dasharray 1s ease'}}/>
      <text x={size/2} y={size/2+5} textAnchor="middle" fontSize={size*0.22} fontWeight="800" fill={color}>{score.toFixed(1)}</text>
      <text x={size/2} y={size/2+size*0.19} textAnchor="middle" fontSize={size*0.1} fill={C.muted} letterSpacing="1">{label}</text>
    </svg>
  );
}

function RentaBar({ brute, nette, t }) {
  return (
    <div style={{display:'flex',flexDirection:'column',gap:12}}>
      {[{label:t.yieldBrute,val:brute,color:C.accent},{label:t.yieldNet,val:nette,color:C.green}].map(b=>(
        <div key={b.label}>
          <div style={{display:'flex',justifyContent:'space-between',fontSize:12,color:C.muted,marginBottom:5}}>
            <span>{b.label}</span><span style={{fontWeight:700,color:b.color}}>{b.val.toFixed(2)}%</span>
          </div>
          <div style={{height:7,background:C.border,borderRadius:4,overflow:'hidden'}}>
            <div style={{height:'100%',width:`${Math.min(100,(b.val/8)*100)}%`,background:b.color,borderRadius:4,transition:'width 1s ease'}}/>
          </div>
        </div>
      ))}
    </div>
  );
}

function Chip({ children, color }) {
  return (
    <span style={{background:color+'18',color,border:`1px solid ${color}33`,borderRadius:20,padding:'4px 12px',fontSize:12,fontWeight:600,display:'inline-flex',alignItems:'center'}}>
      {children}
    </span>
  );
}

function Section({ title, color, children }) {
  return (
    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:18,padding:24}}>
      <div style={{fontSize:11,letterSpacing:2,color:color||C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:16}}>{title}</div>
      {children}
    </div>
  );
}

function ResultCard({ data, url, t }) {
  const prix=data.prix||0, loyer=data.loyer_estime_median||0, surface=data.surface||1;
  const charges=data.charges_copro_estimees||prix*0.003/12, ibi=data.ibi_annuel_estime||prix*0.004;
  const loyerAnnuel=loyer*11.5, chargesAn=charges*12, base=loyerAnnuel-chargesAn-ibi;
  const impot=base>0?base*0.19:0, revenusNets=base-impot;
  const rentaBrute=prix>0?(loyer*12/prix)*100:0, rentaNette=prix>0?(revenusNets/prix)*100:0;
  const prixM2=prix/surface;
  const dpeColor=['A','B','C'].includes(data.classe_energetique)?C.green:['E','F','G'].includes(data.classe_energetique)?C.red:'#d97706';
  const cityColor = CITY_COLORS[data.ville] || C.accent;

  return (
    <div style={{animation:'fadeUp 0.5s ease both'}}>
      <div style={{background:C.card,border:`2px solid ${cityColor}55`,borderRadius:24,padding:32,marginBottom:16,boxShadow:'0 4px 32px rgba(0,0,0,0.06)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:20,flexWrap:'wrap'}}>
          <div style={{flex:1}}>
            <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:10,flexWrap:'wrap'}}>
              <span style={{fontSize:11,letterSpacing:2,color:cityColor,fontWeight:700,textTransform:'uppercase'}}>{t.aiTag}</span>
              {data.ville&&<span style={{background:cityColor+'18',color:cityColor,border:`1px solid ${cityColor}44`,borderRadius:20,padding:'3px 12px',fontSize:12,fontWeight:700}}>📍 {data.ville}</span>}
            </div>
            <div style={{fontSize:22,fontWeight:800,marginBottom:12,lineHeight:1.3,color:C.text}}>{data.titre}</div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:16}}>
              {data.adresse&&<Chip color={C.muted}>{data.adresse}</Chip>}
              {data.annee_construction&&<Chip color={C.muted}>🏗 {data.annee_construction}</Chip>}
              {data.classe_energetique&&<Chip color={dpeColor}>DPE {data.classe_energetique}</Chip>}
              {data.garage&&<Chip color={CITY_COLORS.Madrid}>🚗 Garage</Chip>}
              {data.piscine&&<Chip color={CITY_COLORS.Barcelona}>🏊 Pool</Chip>}
              {data.trastero&&<Chip color={C.accent}>📦 Storage</Chip>}
              {data.neuf&&<Chip color={C.green}>✨ New</Chip>}
            </div>
            <div style={{fontSize:32,fontWeight:800,color:C.text}}>{prix.toLocaleString('fr')} €
              <span style={{fontSize:14,color:C.muted,fontWeight:400,marginLeft:10}}>{Math.round(prixM2).toLocaleString('fr')} €/m²</span>
            </div>
          </div>
          <ScoreGauge score={data.note_globale||5} t={t} size={110}/>
        </div>
        <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:16,padding:20,marginTop:20}}>
          <div style={{fontSize:11,letterSpacing:2,color:C.tag,textTransform:'uppercase',fontWeight:700,marginBottom:14}}>{t.estimatedRent}</div>
          <div style={{display:'flex',gap:14,marginBottom:12}}>
            {[{l:t.rentMin,v:data.loyer_estime_min,h:false},{l:t.rentMedian,v:data.loyer_estime_median,h:true},{l:t.rentMax,v:data.loyer_estime_max,h:false}].map(x=>(
              <div key={x.l} style={{flex:1,textAlign:'center',background:'#fff',borderRadius:12,padding:'12px 8px',border:`1px solid ${x.h?C.accent+'55':C.border}`}}>
                <div style={{fontSize:11,color:C.muted,textTransform:'uppercase',letterSpacing:1,marginBottom:4}}>{x.l}</div>
                <div style={{fontSize:x.h?28:18,fontWeight:800,color:x.h?C.accent:C.muted}}>{x.v?.toLocaleString('fr')} €</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:13,color:C.tag,background:'rgba(255,255,255,0.5)',borderRadius:10,padding:'10px 14px',lineHeight:1.6}}>💡 {data.justification_loyer}</div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
        <Section title={t.yield} color={C.accent}>
          <RentaBar brute={rentaBrute} nette={rentaNette} t={t}/>
          <div style={{marginTop:14,paddingTop:12,borderTop:`1px solid ${C.border}`,fontSize:13,color:C.muted}}>
            {t.netPerYear} : <span style={{color:revenusNets>0?C.green:C.red,fontWeight:700}}>{Math.round(revenusNets).toLocaleString('fr')} €</span>
          </div>
        </Section>
        <Section title={t.exploitation} color={C.accent}>
          {[
            {l:t.rents,v:`+${Math.round(loyerAnnuel).toLocaleString('fr')} €`,c:C.green},
            {l:t.charges,v:`−${Math.round(chargesAn).toLocaleString('fr')} €`,c:C.red},
            {l:t.ibi,v:`−${Math.round(ibi).toLocaleString('fr')} €`,c:C.red},
            {l:t.tax,v:`−${Math.round(impot).toLocaleString('fr')} €`,c:C.red},
          ].map(r=>(
            <div key={r.l} style={{display:'flex',justifyContent:'space-between',fontSize:12,padding:'6px 0',borderBottom:`1px solid ${C.border}`}}>
              <span style={{color:C.muted}}>{r.l}</span><span style={{color:r.c,fontWeight:700}}>{r.v}</span>
            </div>
          ))}
        </Section>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
        <div style={{background:'#f0fdf4',border:`1px solid #bbf7d0`,borderRadius:18,padding:20}}>
          <div style={{fontSize:11,letterSpacing:2,color:C.green,textTransform:'uppercase',fontWeight:700,marginBottom:12}}>{t.strengths}</div>
          {(data.points_positifs||[]).map((p,i)=>(
            <div key={i} style={{fontSize:13,color:'#166534',padding:'5px 0',borderBottom:'1px solid #dcfce7',display:'flex',gap:8}}><span style={{color:C.green,fontWeight:700}}>+</span>{p}</div>
          ))}
        </div>
        <div style={{background:'#fff5f5',border:`1px solid #fecaca`,borderRadius:18,padding:20}}>
          <div style={{fontSize:11,letterSpacing:2,color:C.red,textTransform:'uppercase',fontWeight:700,marginBottom:12}}>{t.weaknesses}</div>
          {(data.points_negatifs||[]).map((p,i)=>(
            <div key={i} style={{fontSize:13,color:'#991b1b',padding:'5px 0',borderBottom:'1px solid #fee2e2',display:'flex',gap:8}}><span style={{color:C.red,fontWeight:700}}>−</span>{p}</div>
          ))}
        </div>
      </div>

      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:18,padding:24,fontSize:14,color:C.text,lineHeight:1.7}}>
        <span style={{fontWeight:800,color:C.accent}}>{t.verdict} : </span>{data.verdict}
        {url&&<div style={{marginTop:10}}><a href={url} target="_blank" rel="noopener noreferrer" style={{fontSize:12,color:C.accent,textDecoration:'none',fontWeight:600}}>{t.sourceLink} ↗</a></div>}
      </div>

      {/* INE Data block */}
      {(data.irav || data.ipva_city_change) && (
        <div style={{background:'#fffbeb',border:`1px solid #fde68a`,borderRadius:18,padding:20,marginTop:14,display:'flex',gap:20,flexWrap:'wrap'}}>
          <div style={{fontSize:11,letterSpacing:2,color:C.tag,textTransform:'uppercase',fontWeight:700,width:'100%',marginBottom:4}}>📊 {t.ineData}</div>
          {data.irav && (
            <div style={{flex:1,minWidth:180}}>
              <div style={{fontSize:11,color:C.muted,marginBottom:4}}>{t.iravLabel} <span style={{fontSize:10,color:C.muted}}>({data.irav_period})</span></div>
              <div style={{fontSize:26,fontWeight:800,color:C.accent}}>{data.irav}%</div>
              <div style={{fontSize:11,color:C.muted,marginTop:2}}>{t.iravNote}</div>
            </div>
          )}
          {data.ipva_city_change && (
            <div style={{flex:1,minWidth:180}}>
              <div style={{fontSize:11,color:C.muted,marginBottom:4}}>{t.ipvaLabel} {data.ville}</div>
              <div style={{fontSize:26,fontWeight:800,color:data.ipva_city_change>0?C.green:C.red}}>{data.ipva_city_change>0?'+':''}{data.ipva_city_change}%</div>
              <div style={{fontSize:11,color:C.muted,marginTop:2}}>{t.ipvaNote}</div>
            </div>
          )}
          <div style={{width:'100%',fontSize:10,color:C.muted,borderTop:`1px solid ${C.border}`,paddingTop:8,marginTop:4}}>Source : INE — Instituto Nacional de Estadística</div>
        </div>
      )}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────
export default function Home() {
  const [lang, setLang] = useState('fr');
  const [marketData, setMarketData] = useState({
    euribor: { value: 2.45, period: 'Fév. 2026' },
    mortgage_rate: { value: 2.81, period: 'Jan. 2026' },
    ipv: {
      nacional: { change: 8.1, period: 'T4 2025' },
      madrid:   { change: 9.2, period: 'T4 2025' },
      barcelona:{ change: 7.8, period: 'T4 2025' },
      valencia: { change: 11.3, period: 'T4 2025' },
      malaga:   { change: 12.1, period: 'T4 2025' },
    },
    live: false,
  });
  const [url, setUrl] = useState('');
  const [manualText, setManualText] = useState('');
  const [images, setImages] = useState([]); // [{base64, mediaType, preview}]
  const [mode, setMode] = useState('url');
  const [status, setStatus] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  // Email gate
  const [userEmail, setUserEmail] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showQuotaModal, setShowQuotaModal] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [pendingRun, setPendingRun] = useState(false);

  const t = T[lang];

  useEffect(() => {
    fetch('/api/market-data')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setMarketData(d); })
      .catch(() => {});
  }, []);

  async function handleEmailConfirm(email) {
    setEmailLoading(true);
    setEmailError('');
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      if (!data.can_analyze) {
        setShowEmailModal(false);
        setShowQuotaModal(true);
        return;
      }
      setUserEmail(email);
      setShowEmailModal(false);
      setPendingRun(true);
    } catch {
      setEmailError(t.emailError);
    } finally {
      setEmailLoading(false);
    }
  }

  async function run() {
    if (!userEmail) {
      setShowEmailModal(true);
      return;
    }
    setResult(null); setStatus(null);
    let content = '';
    if (mode === 'url') {
      if (!url.trim()) return;
      setStatus('fetching'); setStatusMsg(t.fetching);
      try {
        content = await fetchViaProxy(url.trim());
        setStatusMsg(t.fetched);
      } catch {
        setStatus('error'); setStatusMsg(t.proxyError); return;
      }
    } else if (mode === 'image') {
      if (!images || images.length === 0) return;
    } else {
      if (manualText.trim().length < 50) return;
      content = manualText;
    }
    setStatus('analyzing'); setStatusMsg(t.analyzing);
    try {
      const body = mode === 'image'
        ? { images, lang, email: userEmail }
        : { content: `URL: ${url||'N/A'}\n\n${content}`, lang, email: userEmail };
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (response.status === 403) {
        setStatus(null);
        setShowQuotaModal(true);
        return;
      }
      const parsed = await response.json();
      if (!response.ok) throw new Error(parsed.error);
      setResult(parsed);
      setStatus('done');
      setHistory(prev => [{ url, result: parsed }, ...prev.slice(0, 8)]);
    } catch {
      setStatus('error'); setStatusMsg(t.analyzeError);
    }
  }

  // Run after email confirmed
  useState(() => {
    if (pendingRun && userEmail) {
      setPendingRun(false);
      run();
    }
  });

  function reset() { setResult(null); setStatus(null); setUrl(''); setManualText(''); setImages([]); }

  const isLoading = status === 'fetching' || status === 'analyzing';
  const canRun = mode === 'url' ? url.trim().length > 0 : mode === 'image' ? images.length > 0 : manualText.trim().length >= 50;

  return (
    <>
      <Head>
        <title>buy2rent.io — Rental Investment Analysis Spain</title>
        <meta name="description" content="Analyze any Spanish property listing and get instant rental yield, market rent estimate and investment score. Madrid, Barcelona, Valencia, Málaga."/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <link rel="icon" href="/favicon.ico"/>
        <meta property="og:title" content="buy2rent.io — Rental Investment Analysis Spain"/>
        <meta property="og:description" content="Paste any Idealista listing. Get rental yield, estimated rent and investment score instantly."/>
        <meta property="og:type" content="website"/>
        <script dangerouslySetInnerHTML={{__html:`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-WSVSC97J');`}}/>
      </Head>

      <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WSVSC97J" height="0" width="0" style={{display:'none',visibility:'hidden'}}></iframe></noscript>

      {showEmailModal && <EmailModal t={t} onConfirm={handleEmailConfirm} onClose={()=>setShowEmailModal(false)} loading={emailLoading} error={emailError}/>}
      {showQuotaModal && <QuotaModal t={t} onClose={()=>setShowQuotaModal(false)}/>}

      <div style={{position:'fixed',inset:0,pointerEvents:'none',zIndex:0,
        background:'radial-gradient(ellipse at 80% 0%,#fde68a22 0%,transparent 60%),radial-gradient(ellipse at 20% 100%,#fed7aa18 0%,transparent 60%)'}}/>

      <div style={{position:'relative',zIndex:1,maxWidth:980,margin:'0 auto',padding:'56px 40px'}}>

        {/* Header */}
        <div style={{textAlign:'center',marginBottom:56,animation:'fadeUp 0.4s ease both'}}>
          <div style={{display:'flex',justifyContent:'center',marginBottom:24}}>
            <div style={{display:'flex',gap:2,background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:4,boxShadow:'0 2px 8px rgba(0,0,0,0.06)'}}>
              {['en','fr','es'].map(l=>(
                <button key={l} onClick={()=>{setLang(l);setResult(null);setStatus(null);}} style={{
                  padding:'8px 22px',borderRadius:9,border:'none',cursor:'pointer',
                  background:lang===l?C.accent:'transparent',
                  color:lang===l?'#fff':C.muted,fontSize:13,fontWeight:700,
                  transition:'all 0.2s',textTransform:'uppercase',letterSpacing:1
                }}>{l}</button>
              ))}
            </div>
          </div>

          <div style={{display:'inline-flex',alignItems:'center',gap:8,background:C.accentBg,border:`1px solid #fde68a`,borderRadius:20,padding:'7px 20px',marginBottom:22}}>
            <div style={{width:8,height:8,borderRadius:'50%',background:C.accent,animation:'blink 2s infinite'}}/>
            <span style={{fontSize:11,letterSpacing:3,color:C.tag,fontWeight:700,textTransform:'uppercase'}}>{t.badge}</span>
          </div>

          <h1 style={{fontSize:72,fontWeight:800,color:C.text,marginBottom:18,lineHeight:1,letterSpacing:'-3px'}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </h1>
          <p style={{fontSize:19,color:C.muted,maxWidth:580,margin:'0 auto 28px',lineHeight:1.6}}>{t.subtitle}</p>

          <div style={{display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
            {Object.entries(CITY_COLORS).map(([city])=>(
              <span key={city} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:20,padding:'7px 20px',fontSize:13,fontWeight:600,color:C.accent,boxShadow:'0 2px 8px rgba(0,0,0,0.06)'}}>{city}</span>
            ))}
          </div>
        </div>


        {/* Email status bar */}
        {userEmail && (
          <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:14,padding:'12px 20px',marginBottom:20,display:'flex',alignItems:'center',justifyContent:'space-between',fontSize:13}}>
            <span style={{color:C.tag}}>✅ {userEmail}</span>
            <span style={{color:C.muted,fontSize:12}}>{t.analysesLeft}</span>
          </div>
        )}

        {/* Form */}
        {!result && (
          <div style={{animation:'fadeUp 0.5s ease 0.1s both'}}>
            <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:28,padding:48,boxShadow:'0 8px 48px rgba(0,0,0,0.08)',marginBottom:18}}>
              <div style={{display:'flex',background:C.bg,borderRadius:14,padding:4,marginBottom:30,border:`1px solid ${C.border}`}}>
                {[{k:'url',label:t.modeUrl},{k:'image',label:t.modeImage},{k:'manual',label:t.modeManual}].map(m=>(
                  <button key={m.k} onClick={()=>setMode(m.k)} style={{
                    flex:1,padding:'13px 16px',borderRadius:11,border:'none',cursor:'pointer',
                    background:mode===m.k?C.accent:'transparent',
                    color:mode===m.k?'#fff':C.text,fontSize:13,fontWeight:600,transition:'all 0.2s'
                  }}>{m.label}</button>
                ))}
              </div>

              {mode==='url'?(
                <div>
                  <label style={{fontSize:11,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.urlLabel}</label>
                  <input value={url} onChange={e=>setUrl(e.target.value)} onKeyDown={e=>e.key==='Enter'&&run()} placeholder={t.urlPlaceholder}
                    style={{width:'100%',background:C.bg,border:`1px solid ${C.border2}`,borderRadius:14,padding:'18px 20px',color:C.text,fontSize:16,transition:'border-color 0.2s'}}
                    onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border2}/>
                  <div style={{marginTop:10,fontSize:12,color:C.muted,lineHeight:1.6}}>{t.urlNote}</div>
                </div>
              ):mode==='image'?(
                <div>
                  <label style={{fontSize:11,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.imageLabel}</label>
                  {/* Image previews */}
                  <div style={{display:'flex',gap:10,marginBottom:images.length>0?12:0,flexWrap:'wrap'}}>
                    {images.map((img,i)=>(
                      <div key={i} style={{position:'relative',width:120,height:100,borderRadius:10,overflow:'hidden',border:`1px solid ${C.border}`}}>
                        <img src={img.preview} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
                        <button onClick={()=>setImages(prev=>prev.filter((_,j)=>j!==i))}
                          style={{position:'absolute',top:4,right:4,background:'rgba(0,0,0,0.6)',border:'none',color:'#fff',borderRadius:'50%',width:22,height:22,cursor:'pointer',fontSize:12,display:'flex',alignItems:'center',justifyContent:'center'}}>✕</button>
                      </div>
                    ))}
                    {images.length < 2 && (
                      <div onClick={()=>document.getElementById('imgUpload').click()}
                        style={{width:images.length===0?'100%':120,minHeight:images.length===0?180:100,background:C.bg,
                        border:`2px dashed ${images.length>0?C.border2:C.border2}`,borderRadius:images.length===0?14:10,
                        display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',cursor:'pointer',transition:'border-color 0.2s',flex:images.length===0?1:'none'}}>
                        {images.length===0?(
                          <div style={{textAlign:'center',padding:24}}>
                            <div style={{fontSize:36,marginBottom:10}}>📸</div>
                            <div style={{color:C.muted,fontSize:14,fontWeight:500}}>{t.imagePlaceholder}</div>
                            <div style={{color:C.muted,fontSize:11,marginTop:6,opacity:0.7}}>{t.imageNote}</div>
                          </div>
                        ):(
                          <div style={{textAlign:'center',padding:8}}>
                            <div style={{fontSize:22}}>+</div>
                            <div style={{color:C.muted,fontSize:10}}>{t.imageAdd}</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <input id='imgUpload' type='file' accept='image/*' style={{display:'none'}} onChange={e=>{
                    const file = e.target.files[0];
                    if (!file) return;
                    const imgEl = new Image();
                    const objectUrl = URL.createObjectURL(file);
                    imgEl.onload = () => {
                      const MAX = 1200;
                      let w = imgEl.width, h = imgEl.height;
                      if (w > MAX || h > MAX) {
                        if (w > h) { h = Math.round(h * MAX / w); w = MAX; }
                        else { w = Math.round(w * MAX / h); h = MAX; }
                      }
                      const canvas = document.createElement('canvas');
                      canvas.width = w; canvas.height = h;
                      canvas.getContext('2d').drawImage(imgEl, 0, 0, w, h);
                      const dataUrl = canvas.toDataURL('image/jpeg', 0.75);
                      URL.revokeObjectURL(objectUrl);
                      const base64 = dataUrl.split(',')[1];
                      setImages(prev => [...prev, {base64, mediaType:'image/jpeg', preview:dataUrl}]);
                      e.target.value = '';
                    };
                    imgEl.src = objectUrl;
                  }}/>
                </div>
              ):(
                <div>
                  <label style={{fontSize:11,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.textLabel}</label>
                  <textarea value={manualText} onChange={e=>setManualText(e.target.value)} placeholder={t.textPlaceholder}
                    style={{width:'100%',height:260,background:C.bg,border:`1px solid ${C.border2}`,borderRadius:14,padding:'18px 20px',color:C.text,fontSize:15,resize:'vertical',lineHeight:1.7,transition:'border-color 0.2s'}}
                    onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border2}/>
                </div>
              )}

              <button onClick={run} disabled={isLoading||!canRun} style={{
                width:'100%',marginTop:24,padding:'22px',borderRadius:16,border:'none',
                background:isLoading||!canRun?C.border:C.accent,
                color:isLoading||!canRun?C.muted:'#fff',fontSize:17,fontWeight:800,
                cursor:isLoading||!canRun?'not-allowed':'pointer',letterSpacing:'0.5px',
                display:'flex',alignItems:'center',justifyContent:'center',gap:12,transition:'all 0.2s',
                boxShadow:isLoading||!canRun?'none':'0 6px 20px rgba(180,83,9,0.3)'
              }}>
                {isLoading?(
                  <><div style={{width:20,height:20,border:'2px solid #fff',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>{statusMsg}</>
                ):(canRun?t.cta:t.ctaDisabled)}
              </button>

              {status==='error'&&(
                <div style={{marginTop:16,padding:16,background:'#fff5f5',border:`1px solid #fecaca`,borderRadius:12,fontSize:13,color:C.red}}>⚠️ {statusMsg}</div>
              )}
            </div>

            <button onClick={()=>{setMode('manual');setManualText('Calle de Isabel Clara Eugenia, 37\nSanchinarro, Madrid\n560,000 euros\n\n2 dormitorios y 2 baños, urbanización privada con piscina, jardines, gimnasio, coworking, zona infantil, conserjería y ascensor. 1 plaza de garaje y trastero.\n\n84 m² construidos, planta 3ª exterior, construido en 2005, calefacción gas natural, aire acondicionado.\n\nCertificado energético: 167 kWh/m² año, 25 kg CO2/m² año');}}
              style={{width:'100%',padding:'15px',borderRadius:14,background:'transparent',border:`1px dashed ${C.border2}`,color:C.muted,fontSize:14,cursor:'pointer',transition:'all 0.2s',fontWeight:500}}
              onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent}}
              onMouseLeave={e=>{e.target.style.borderColor=C.border2;e.target.style.color=C.muted}}>
              {t.example}
            </button>
          </div>
        )}


        {/* Market Data Widget */}
        {marketData && !result && (
          <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:20,padding:'20px 24px',marginBottom:24,boxShadow:'0 4px 24px rgba(0,0,0,0.06)'}}>
            <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:16}}>
              <div style={{width:7,height:7,borderRadius:'50%',background:'#22c55e',animation:'blink 2s infinite'}}/>
              <span style={{fontSize:10,letterSpacing:2,color:C.muted,textTransform:'uppercase',fontWeight:700}}>{t.marketTitle}</span>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))',gap:10}}>
              <div style={{background:C.bg,borderRadius:12,padding:'12px 14px'}}>
                <div style={{fontSize:10,color:C.muted,marginBottom:3,fontWeight:600}}>Euribor 12M</div>
                <div style={{fontSize:20,fontWeight:800,color:C.text}}>{marketData.euribor.value}%</div>
                <div style={{fontSize:10,color:C.muted,marginTop:2}}>{marketData.euribor.period}</div>
              </div>
              <div style={{background:C.bg,borderRadius:12,padding:'12px 14px'}}>
                <div style={{fontSize:10,color:C.muted,marginBottom:3,fontWeight:600}}>{t.mortgageRate}</div>
                <div style={{fontSize:20,fontWeight:800,color:C.text}}>{marketData.mortgage_rate.value}%</div>
                <div style={{fontSize:10,color:C.muted,marginTop:2}}>{marketData.mortgage_rate.period}</div>
              </div>
              {Object.entries(marketData.ipv).map(([city, d]) => (
                <div key={city} style={{background:C.bg,borderRadius:12,padding:'12px 14px'}}>
                  <div style={{fontSize:10,color:C.muted,marginBottom:3,fontWeight:600,textTransform:'capitalize'}}>{t.ipvLabel} {city === 'nacional' ? t.ipvNacional : city.charAt(0).toUpperCase()+city.slice(1)}</div>
                  <div style={{fontSize:20,fontWeight:800,color:parseFloat(d.change)>0?'#22c55e':C.red}}>{parseFloat(d.change)>0?'+':''}{d.change}%</div>
                  <div style={{fontSize:10,color:C.muted,marginTop:2}}>{d.period}</div>
                </div>
              ))}
            </div>
            <div style={{marginTop:10,fontSize:10,color:C.muted,borderTop:`1px solid ${C.border}`,paddingTop:10}}>
              📊 {t.marketSource} {marketData.live ? 'Live' : 'Données de référence'}
            </div>
          </div>
        )}
        {/* Result */}
        {result&&(
          <div>
            <ResultCard data={result} url={url} t={t}/>
            <button onClick={reset} style={{width:'100%',marginTop:18,padding:'18px',borderRadius:14,background:'transparent',border:`1px solid ${C.border2}`,color:C.muted,fontSize:14,cursor:'pointer',fontWeight:600,transition:'all 0.2s'}}
              onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent}}
              onMouseLeave={e=>{e.target.style.borderColor=C.border2;e.target.style.color=C.muted}}>
              {t.newAnalysis}
            </button>
          </div>
        )}

        {/* History */}
        {history.length>1&&!result&&(
          <div style={{marginTop:40}}>
            <div style={{fontSize:11,letterSpacing:3,color:C.muted,textTransform:'uppercase',marginBottom:14,fontWeight:600}}>{t.recentTitle}</div>
            {history.slice(1).map((h,i)=>{
              const cityColor = CITY_COLORS[h.result.ville] || C.accent;
              return (
                <div key={i} onClick={()=>{setResult(h.result);setUrl(h.url);}}
                  style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:14,padding:'16px 22px',cursor:'pointer',display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10,transition:'all 0.2s',boxShadow:'0 2px 8px rgba(0,0,0,0.04)'}}
                  onMouseEnter={e=>{e.currentTarget.style.borderColor=C.accent;e.currentTarget.style.boxShadow='0 4px 16px rgba(180,83,9,0.1)'}}
                  onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border;e.currentTarget.style.boxShadow='0 2px 8px rgba(0,0,0,0.04)'}}>
                  <div>
                    <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:3}}>
                      {h.result.ville&&<span style={{fontSize:11,color:cityColor,fontWeight:700}}>● {h.result.ville}</span>}
                      <span style={{fontSize:14,fontWeight:700,color:C.text}}>{h.result.titre}</span>
                    </div>
                    <div style={{fontSize:12,color:C.muted}}>{h.result.prix?.toLocaleString('fr')} {'€'} — {h.result.loyer_estime_median?.toLocaleString('fr')} €/mois</div>
                  </div>
                  <div style={{width:42,height:42,borderRadius:'50%',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,
                    border:`2px solid ${h.result.note_globale>=7?C.green:h.result.note_globale>=5?'#d97706':C.red}`,
                    fontSize:13,fontWeight:800,color:h.result.note_globale>=7?C.green:h.result.note_globale>=5?'#d97706':C.red}}>
                    {h.result.note_globale?.toFixed(1)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{textAlign:'center',marginTop:64,fontSize:12,color:C.muted}}>
          buy2rent.io — 2026
        </div>
      </div>
    </>
  );
}
