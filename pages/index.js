import { useState } from 'react';
import Head from 'next/head';
import T from '../components/translations';

function stripHtml(html) {
  if (typeof document === 'undefined') return html;
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  tmp.querySelectorAll('script,style,nav,footer,header').forEach(el => el.remove());
  return tmp.innerText.replace(/\s{3,}/g, '\n\n').trim().slice(0, 8000);
}

async function fetchViaProxy(url) {
  const proxies = [
    `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`,
    `https://corsproxy.io/?${encodeURIComponent(url)}`,
  ];
  for (const proxy of proxies) {
    try {
      const res = await fetch(proxy, { signal: AbortSignal.timeout(10000) });
      if (!res.ok) continue;
      const data = await res.json().catch(() => null);
      const html = data?.contents || await res.text();
      if (html && html.length > 500) return stripHtml(html);
    } catch { continue; }
  }
  throw new Error('proxy_failed');
}

const CITY_COLORS = {
  'Madrid': '#f59e0b',
  'Barcelona': '#ec4899',
  'Valencia': '#10b981',
  'Málaga': '#3b82f6',
};

function ScoreGauge({ score, t, size = 100 }) {
  const r = size * 0.38, circ = 2 * Math.PI * r, fill = (score / 10) * circ;
  const color = score >= 7 ? '#4ade80' : score >= 5 ? '#facc15' : score >= 3 ? '#fb923c' : '#f87171';
  const label = score >= 7 ? t.score.good : score >= 5 ? t.score.avg : score >= 3 ? t.score.weak : t.score.avoid;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e1b2e" strokeWidth={size*0.08}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.08}
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`} style={{transition:'stroke-dasharray 1s ease'}}/>
      <text x={size/2} y={size/2+5} textAnchor="middle" fontSize={size*0.22} fontWeight="800" fill={color}>{score.toFixed(1)}</text>
      <text x={size/2} y={size/2+size*0.19} textAnchor="middle" fontSize={size*0.1} fill="#6b7280" letterSpacing="1">{label}</text>
    </svg>
  );
}

function RentaBar({ brute, nette, t }) {
  return (
    <div style={{display:'flex',flexDirection:'column',gap:10}}>
      {[{label:t.yieldBrute,val:brute,color:'#c084fc'},{label:t.yieldNet,val:nette,color:'#818cf8'}].map(b=>(
        <div key={b.label}>
          <div style={{display:'flex',justifyContent:'space-between',fontSize:11,color:'#9ca3af',marginBottom:4}}>
            <span>{b.label}</span><span style={{fontWeight:700,color:b.color}}>{b.val.toFixed(2)}%</span>
          </div>
          <div style={{height:6,background:'#1e1b2e',borderRadius:3,overflow:'hidden'}}>
            <div style={{height:'100%',width:`${Math.min(100,(b.val/8)*100)}%`,background:`linear-gradient(90deg,${b.color}66,${b.color})`,borderRadius:3,transition:'width 1s ease'}}/>
          </div>
        </div>
      ))}
    </div>
  );
}

function Chip({ children, color='#374151' }) {
  return (
    <span style={{background:color+'22',color,border:`1px solid ${color}44`,borderRadius:20,padding:'3px 10px',fontSize:11,fontWeight:600,display:'inline-flex',alignItems:'center'}}>
      {children}
    </span>
  );
}

function ResultCard({ data, url, t }) {
  const prix=data.prix||0, loyer=data.loyer_estime_median||0, surface=data.surface||1;
  const charges=data.charges_copro_estimees||prix*0.003/12, ibi=data.ibi_annuel_estime||prix*0.004;
  const loyerAnnuel=loyer*11.5, chargesAn=charges*12, base=loyerAnnuel-chargesAn-ibi;
  const impot=base>0?base*0.19:0, revenusNets=base-impot;
  const rentaBrute=prix>0?(loyer*12/prix)*100:0, rentaNette=prix>0?(revenusNets/prix)*100:0;
  const prixM2=prix/surface;
  const dpeColor=['A','B','C'].includes(data.classe_energetique)?'#4ade80':['E','F','G'].includes(data.classe_energetique)?'#f87171':'#facc15';
  const cityColor = CITY_COLORS[data.ville] || '#9333ea';

  return (
    <div style={{animation:'fadeUp 0.5s ease both'}}>
      <div style={{background:'linear-gradient(135deg,#13111c,#1a1625)',border:`1px solid ${cityColor}44`,borderRadius:20,padding:24,marginBottom:14}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:16,flexWrap:'wrap'}}>
          <div style={{flex:1}}>
            <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8,flexWrap:'wrap'}}>
              <div style={{fontSize:10,letterSpacing:3,color:cityColor,fontWeight:700,textTransform:'uppercase'}}>{t.aiTag}</div>
              {data.ville && (
                <span style={{background:cityColor+'22',color:cityColor,border:`1px solid ${cityColor}44`,borderRadius:20,padding:'2px 10px',fontSize:11,fontWeight:700}}>
                  📍 {data.ville}
                </span>
              )}
            </div>
            <div style={{fontSize:19,fontWeight:800,marginBottom:10,lineHeight:1.3}}>{data.titre}</div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap',marginBottom:14}}>
              {data.adresse&&<Chip color="#9ca3af">{data.adresse}</Chip>}
              {data.annee_construction&&<Chip color="#6b7280">🏗 {data.annee_construction}</Chip>}
              {data.classe_energetique&&<Chip color={dpeColor}>DPE {data.classe_energetique}</Chip>}
              {data.garage&&<Chip color="#60a5fa">🚗 Garage</Chip>}
              {data.piscine&&<Chip color="#38bdf8">🏊 Pool</Chip>}
              {data.trastero&&<Chip color="#a78bfa">📦 Storage</Chip>}
              {data.neuf&&<Chip color="#4ade80">✨ New build</Chip>}
            </div>
            <div style={{fontSize:26,fontWeight:800}}>{prix.toLocaleString('fr')} €
              <span style={{fontSize:13,color:'#6b7280',fontWeight:400,marginLeft:8}}>{Math.round(prixM2).toLocaleString('fr')} €/m²</span>
            </div>
          </div>
          <ScoreGauge score={data.note_globale||5} t={t} size={100}/>
        </div>

        {/* Rent block */}
        <div style={{background:'linear-gradient(135deg,#2d1b69,#1e1b4b)',border:'1px solid #4c1d95',borderRadius:14,padding:16,marginTop:16}}>
          <div style={{fontSize:10,letterSpacing:2,color:'#a78bfa',textTransform:'uppercase',fontWeight:600,marginBottom:12}}>{t.estimatedRent}</div>
          <div style={{display:'flex',gap:12,marginBottom:12}}>
            {[{l:t.rentMin,v:data.loyer_estime_min,h:false},{l:t.rentMedian,v:data.loyer_estime_median,h:true},{l:t.rentMax,v:data.loyer_estime_max,h:false}].map(x=>(
              <div key={x.l} style={{flex:1,textAlign:'center'}}>
                <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:1,marginBottom:2}}>{x.l}</div>
                <div style={{fontSize:x.h?24:16,fontWeight:800,color:x.h?'#c084fc':'#6b7280'}}>{x.v?.toLocaleString('fr')} €</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:12,color:'#7c3aed',background:'#1e1b2e',borderRadius:8,padding:'8px 12px',lineHeight:1.6}}>💡 {data.justification_loyer}</div>
        </div>
      </div>

      {/* Metrics */}
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12,marginBottom:14}}>
        <div style={{background:'#13111c',border:'1px solid #2d2640',borderRadius:16,padding:18}}>
          <div style={{fontSize:10,letterSpacing:2,color:'#9333ea',textTransform:'uppercase',fontWeight:600,marginBottom:14}}>{t.yield}</div>
          <RentaBar brute={rentaBrute} nette={rentaNette} t={t}/>
          <div style={{marginTop:12,paddingTop:10,borderTop:'1px solid #1e1b2e',fontSize:12,color:'#6b7280'}}>
            {t.netPerYear} : <span style={{color:revenusNets>0?'#4ade80':'#f87171',fontWeight:700}}>{Math.round(revenusNets).toLocaleString('fr')} €</span>
          </div>
        </div>
        <div style={{background:'#13111c',border:'1px solid #2d2640',borderRadius:16,padding:18}}>
          <div style={{fontSize:10,letterSpacing:2,color:'#9333ea',textTransform:'uppercase',fontWeight:600,marginBottom:14}}>{t.exploitation}</div>
          {[
            {l:t.rents,v:`+${Math.round(loyerAnnuel).toLocaleString('fr')} €`,c:'#4ade80'},
            {l:t.charges,v:`−${Math.round(chargesAn).toLocaleString('fr')} €`,c:'#f87171'},
            {l:t.ibi,v:`−${Math.round(ibi).toLocaleString('fr')} €`,c:'#f87171'},
            {l:t.tax,v:`−${Math.round(impot).toLocaleString('fr')} €`,c:'#f87171'},
          ].map(r=>(
            <div key={r.l} style={{display:'flex',justifyContent:'space-between',fontSize:11,padding:'4px 0',borderBottom:'1px solid #1e1b2e'}}>
              <span style={{color:'#6b7280'}}>{r.l}</span><span style={{color:r.c,fontWeight:600}}>{r.v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Strengths / Weaknesses */}
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12,marginBottom:14}}>
        <div style={{background:'#0d1f13',border:'1px solid #14532d',borderRadius:16,padding:16}}>
          <div style={{fontSize:10,letterSpacing:2,color:'#4ade80',textTransform:'uppercase',fontWeight:600,marginBottom:10}}>{t.strengths}</div>
          {(data.points_positifs||[]).map((p,i)=><div key={i} style={{fontSize:12,color:'#86efac',padding:'4px 0',borderBottom:'1px solid #14532d22',display:'flex',gap:6}}><span style={{color:'#4ade80'}}>+</span>{p}</div>)}
        </div>
        <div style={{background:'#1f0d0d',border:'1px solid #7f1d1d',borderRadius:16,padding:16}}>
          <div style={{fontSize:10,letterSpacing:2,color:'#f87171',textTransform:'uppercase',fontWeight:600,marginBottom:10}}>{t.weaknesses}</div>
          {(data.points_negatifs||[]).map((p,i)=><div key={i} style={{fontSize:12,color:'#fca5a5',padding:'4px 0',borderBottom:'1px solid #7f1d1d22',display:'flex',gap:6}}><span style={{color:'#f87171'}}>−</span>{p}</div>)}
        </div>
      </div>

      {/* Verdict */}
      <div style={{background:'linear-gradient(135deg,#1e1b2e,#13111c)',border:'1px solid #4c1d95',borderRadius:16,padding:18,fontSize:14,color:'#e2e8f0',lineHeight:1.6}}>
        <span style={{fontWeight:700,color:'#c084fc'}}>{t.verdict} : </span>{data.verdict}
        {url&&<div style={{marginTop:8}}><a href={url} target="_blank" rel="noopener noreferrer" style={{fontSize:11,color:'#7c3aed',textDecoration:'none'}}>{t.sourceLink}</a></div>}
      </div>
    </div>
  );
}

export default function Home() {
  const [lang, setLang] = useState('fr');
  const [url, setUrl] = useState('');
  const [manualText, setManualText] = useState('');
  const [mode, setMode] = useState('url');
  const [status, setStatus] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const t = T[lang];

  async function run() {
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
    } else {
      if (manualText.trim().length < 50) return;
      content = manualText;
    }
    setStatus('analyzing'); setStatusMsg(t.analyzing);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: `URL: ${url||'N/A'}\n\n${content}`, lang }),
      });
      const parsed = await response.json();
      if (!response.ok) throw new Error(parsed.error);
      setResult(parsed);
      setStatus('done');
      setHistory(prev => [{ url, result: parsed }, ...prev.slice(0, 8)]);
    } catch {
      setStatus('error'); setStatusMsg(t.analyzeError);
    }
  }

  function reset() { setResult(null); setStatus(null); setUrl(''); setManualText(''); }

  const isLoading = status === 'fetching' || status === 'analyzing';
  const canRun = mode === 'url' ? url.trim().length > 0 : manualText.trim().length >= 50;

  return (
    <>
      <Head>
        <title>Spain Invest — AI Rental Property Analysis</title>
        <meta name="description" content="Analyze any Spanish property listing and get instant rental yield, market rent estimate and investment score. Madrid, Barcelona, Valencia, Málaga."/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <link rel="icon" href="/favicon.ico"/>
        {/* OG tags for sharing */}
        <meta property="og:title" content="Spain Invest — AI Rental Property Analysis"/>
        <meta property="og:description" content="Paste any Idealista listing. Get rental yield, estimated rent and investment score instantly."/>
        <meta property="og:type" content="website"/>
      </Head>

      <div style={{position:'fixed',inset:0,pointerEvents:'none',zIndex:0}}>
        <div style={{position:'absolute',top:-150,right:-150,width:500,height:500,background:'radial-gradient(circle,#7c3aed0d 0%,transparent 70%)',borderRadius:'50%'}}/>
        <div style={{position:'absolute',bottom:-100,left:-100,width:350,height:350,background:'radial-gradient(circle,#4f46e50a 0%,transparent 70%)',borderRadius:'50%'}}/>
      </div>

      <div style={{position:'relative',zIndex:1,maxWidth:660,margin:'0 auto',padding:'28px 16px'}}>

        {/* Header */}
        <div style={{textAlign:'center',marginBottom:32,animation:'fadeUp 0.4s ease both'}}>
          <div style={{display:'flex',justifyContent:'center',marginBottom:16}}>
            <div style={{display:'flex',gap:4,background:'#0c0a14',border:'1px solid #1e1b2e',borderRadius:10,padding:3}}>
              {['en','fr','es'].map(l=>(
                <button key={l} onClick={()=>{setLang(l);setResult(null);setStatus(null);}} style={{
                  padding:'5px 12px',borderRadius:7,border:'none',cursor:'pointer',
                  background:lang===l?'linear-gradient(135deg,#7c3aed,#4f46e5)':'transparent',
                  color:lang===l?'#fff':'#6b7280',fontSize:12,fontWeight:700,
                  transition:'all 0.2s',textTransform:'uppercase',letterSpacing:1
                }}>{l}</button>
              ))}
            </div>
          </div>
          <div style={{display:'inline-flex',alignItems:'center',gap:8,background:'#1a1625',border:'1px solid #2d2640',borderRadius:20,padding:'5px 14px',marginBottom:14}}>
            <div style={{width:7,height:7,borderRadius:'50%',background:'#9333ea',animation:'blink 2s infinite'}}/>
            <span style={{fontSize:10,letterSpacing:3,color:'#9333ea',fontWeight:700,textTransform:'uppercase'}}>{t.badge}</span>
          </div>
          <h1 style={{fontSize:34,fontWeight:800,background:'linear-gradient(135deg,#fff 40%,#c084fc)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',marginBottom:8}}>{t.title}</h1>
          <p style={{fontSize:13,color:'#6b7280',maxWidth:400,margin:'0 auto 12px'}}>{t.subtitle}</p>
          {/* City pills */}
          <div style={{display:'flex',justifyContent:'center',gap:6,flexWrap:'wrap'}}>
            {Object.entries(CITY_COLORS).map(([city,color])=>(
              <span key={city} style={{background:color+'18',color,border:`1px solid ${color}33`,borderRadius:20,padding:'3px 12px',fontSize:11,fontWeight:600}}>{city}</span>
            ))}
          </div>
        </div>

        {/* Form */}
        {!result && (
          <div style={{animation:'fadeUp 0.5s ease 0.1s both'}}>
            <div style={{background:'#13111c',border:'1px solid #2d2640',borderRadius:20,padding:24,boxShadow:'0 0 60px #7c3aed11',marginBottom:14}}>
              <div style={{display:'flex',background:'#0c0a14',borderRadius:12,padding:4,marginBottom:20,border:'1px solid #1e1b2e'}}>
                {[{k:'url',label:t.modeUrl},{k:'manual',label:t.modeManual}].map(m=>(
                  <button key={m.k} onClick={()=>setMode(m.k)} style={{
                    flex:1,padding:'9px 12px',borderRadius:9,border:'none',cursor:'pointer',
                    background:mode===m.k?'linear-gradient(135deg,#7c3aed,#4f46e5)':'transparent',
                    color:mode===m.k?'#fff':'#6b7280',fontSize:13,fontWeight:600,transition:'all 0.2s'
                  }}>{m.label}</button>
                ))}
              </div>

              {mode==='url'?(
                <div>
                  <label style={{fontSize:10,letterSpacing:2,color:'#7c3aed',textTransform:'uppercase',fontWeight:600,display:'block',marginBottom:8}}>{t.urlLabel}</label>
                  <input value={url} onChange={e=>setUrl(e.target.value)} onKeyDown={e=>e.key==='Enter'&&run()} placeholder={t.urlPlaceholder}
                    style={{width:'100%',background:'#0c0a14',border:'1px solid #2d2640',borderRadius:11,padding:'12px 14px',color:'#e2e8f0',fontSize:14}}
                    onFocus={e=>e.target.style.borderColor='#7c3aed'} onBlur={e=>e.target.style.borderColor='#2d2640'}/>
                  <div style={{marginTop:8,fontSize:11,color:'#4b5563',lineHeight:1.6}}>{t.urlNote}</div>
                </div>
              ):(
                <div>
                  <label style={{fontSize:10,letterSpacing:2,color:'#7c3aed',textTransform:'uppercase',fontWeight:600,display:'block',marginBottom:8}}>{t.textLabel}</label>
                  <textarea value={manualText} onChange={e=>setManualText(e.target.value)} placeholder={t.textPlaceholder}
                    style={{width:'100%',height:180,background:'#0c0a14',border:'1px solid #2d2640',borderRadius:11,padding:'12px 14px',color:'#e2e8f0',fontSize:13,resize:'vertical',lineHeight:1.6}}
                    onFocus={e=>e.target.style.borderColor='#7c3aed'} onBlur={e=>e.target.style.borderColor='#2d2640'}/>
                </div>
              )}

              <button onClick={run} disabled={isLoading||!canRun} style={{
                width:'100%',marginTop:16,padding:'14px',borderRadius:12,border:'none',
                background:isLoading||!canRun?'#1e1b2e':'linear-gradient(135deg,#7c3aed,#4f46e5)',
                color:isLoading||!canRun?'#4b5563':'#fff',fontSize:14,fontWeight:700,
                cursor:isLoading||!canRun?'not-allowed':'pointer',
                display:'flex',alignItems:'center',justifyContent:'center',gap:10,transition:'opacity 0.2s'
              }}>
                {isLoading?(<><div style={{width:16,height:16,border:'2px solid #7c3aed',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>{statusMsg}</>):(canRun?t.cta:t.ctaDisabled)}
              </button>

              {status==='error'&&(
                <div style={{marginTop:12,padding:12,background:'#1f0d0d',border:'1px solid #7f1d1d',borderRadius:10,fontSize:13,color:'#f87171'}}>⚠️ {statusMsg}</div>
              )}
            </div>

            <button onClick={()=>{setMode('manual');setManualText('Calle de Isabel Clara Eugenia, 37\nSanchinarro, Madrid\n560,000 euros\n\n2 dormitorios y 2 baños, urbanización privada con piscina, jardines, gimnasio, coworking, zona infantil, conserjería y ascensor. 1 plaza de garaje y trastero.\n\n84 m² construidos, planta 3ª exterior, construido en 2005, calefacción gas natural, aire acondicionado.\n\nCertificado energético: 167 kWh/m² año, 25 kg CO2/m² año');}}
              style={{width:'100%',padding:'10px',borderRadius:10,background:'transparent',border:'1px dashed #2d2640',color:'#4b5563',fontSize:12,cursor:'pointer',transition:'all 0.2s'}}
              onMouseEnter={e=>{e.target.style.borderColor='#7c3aed';e.target.style.color='#9333ea'}}
              onMouseLeave={e=>{e.target.style.borderColor='#2d2640';e.target.style.color='#4b5563'}}>
              {t.example}
            </button>
          </div>
        )}

        {/* Result */}
        {result&&(
          <div>
            <ResultCard data={result} url={url} t={t}/>
            <button onClick={reset} style={{width:'100%',marginTop:14,padding:'13px',borderRadius:12,background:'transparent',border:'1px solid #2d2640',color:'#6b7280',fontSize:13,cursor:'pointer',fontWeight:600,transition:'all 0.2s'}}
              onMouseEnter={e=>{e.target.style.borderColor='#7c3aed';e.target.style.color='#c084fc'}}
              onMouseLeave={e=>{e.target.style.borderColor='#2d2640';e.target.style.color='#6b7280'}}>
              {t.newAnalysis}
            </button>
          </div>
        )}

        {/* History */}
        {history.length>1&&!result&&(
          <div style={{marginTop:28}}>
            <div style={{fontSize:10,letterSpacing:3,color:'#4b5563',textTransform:'uppercase',marginBottom:10}}>{t.recentTitle}</div>
            {history.slice(1).map((h,i)=>{
              const cityColor = CITY_COLORS[h.result.ville] || '#9333ea';
              return (
                <div key={i} onClick={()=>{setResult(h.result);setUrl(h.url);}}
                  style={{background:'#13111c',border:'1px solid #1e1b2e',borderRadius:12,padding:'12px 16px',cursor:'pointer',display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8,transition:'border-color 0.2s'}}
                  onMouseEnter={e=>e.currentTarget.style.borderColor='#2d2640'}
                  onMouseLeave={e=>e.currentTarget.style.borderColor='#1e1b2e'}>
                  <div>
                    <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:2}}>
                      {h.result.ville&&<span style={{fontSize:10,color:cityColor,fontWeight:700}}>● {h.result.ville}</span>}
                      <span style={{fontSize:13,fontWeight:600,color:'#e2e8f0'}}>{h.result.titre}</span>
                    </div>
                    <div style={{fontSize:11,color:'#4b5563'}}>{h.result.prix?.toLocaleString('fr')} € · {h.result.loyer_estime_median?.toLocaleString('fr')} €/mo</div>
                  </div>
                  <div style={{width:36,height:36,borderRadius:'50%',display:'flex',alignItems:'center',justifyContent:'center',
                    border:`2px solid ${h.result.note_globale>=7?'#4ade80':h.result.note_globale>=5?'#facc15':'#f87171'}`,
                    fontSize:12,fontWeight:700,color:h.result.note_globale>=7?'#4ade80':h.result.note_globale>=5?'#facc15':'#f87171'}}>
                    {h.result.note_globale?.toFixed(1)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{textAlign:'center',marginTop:40,fontSize:11,color:'#374151'}}>
          Spain Invest · Powered by Claude AI · {new Date().getFullYear()}
        </div>
      </div>
    </>
  );
}
