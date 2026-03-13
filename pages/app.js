import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import T from '../components/translations';
// This file lives at pages/app.js

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
  const res = await fetch('/api/fetch-listing', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
    signal: AbortSignal.timeout(45000),
  });
  if (!res.ok) throw new Error('proxy_failed');
  const data = await res.json();
  if (!data.content || data.content.length < 100) throw new Error('proxy_failed');
  return data.content;
}

// ─── Soft Gate Modal (after 2 anon analyses) ─────────────
// ─── Quota Exceeded Modal ─────────────────────────────────
function QuotaModal({ t, onClose, userEmail }) {
  const [loadingVariant, setLoadingVariant] = useState(null);
  const [email, setEmail] = useState(userEmail || '');
  const [emailStep, setEmailStep] = useState(!userEmail);
  const validEmail = email.includes('@') && email.includes('.');

  async function handleCheckout(priceId) {
    const finalEmail = email.trim();
    if (!finalEmail) { setEmailStep(true); return; }
    setLoadingVariant(priceId);
    try {
      const res = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceId, email: finalEmail }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
      else alert('Error creating checkout. Please try again.');
    } catch {
      alert('Error creating checkout. Please try again.');
    } finally {
      setLoadingVariant(null);
    }
  }

  const PRICE_PASS = 'pass_24h';
  const PRICE_PRO  = 'pro';

  return (
    <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.4)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center',padding:24}}>
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:24,padding:40,maxWidth:480,width:'100%',boxShadow:'0 20px 60px rgba(0,0,0,0.15)',animation:'fadeUp 0.3s ease both',textAlign:'center'}}>
        <div style={{fontSize:40,marginBottom:16}}>🔒</div>
        <h2 style={{fontSize:24,fontWeight:800,color:C.text,marginBottom:10}}>{t.quotaTitle}</h2>
        <p style={{fontSize:16,color:C.muted,lineHeight:1.6,marginBottom:20}}>{t.quotaSubtitle}</p>

        {/* Email capture if not authenticated */}
        {emailStep && (
          <div style={{marginBottom:20}}>
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)}
              placeholder="your@email.com"
              style={{width:'100%',padding:'13px 16px',borderRadius:12,border:`1px solid ${validEmail?C.accent:C.border2}`,background:C.bg,fontSize:15,color:C.text,marginBottom:8,outline:'none',transition:'border-color 0.2s'}}
              onFocus={e=>e.target.style.borderColor=C.accent}
              onBlur={e=>e.target.style.borderColor=validEmail?C.accent:C.border2}
            />
            {validEmail && <button onClick={()=>setEmailStep(false)} style={{width:'100%',padding:'11px',borderRadius:12,border:'none',background:C.accent,color:'#fff',fontSize:15,fontWeight:700,cursor:'pointer',marginBottom:8}}>
              Continue →
            </button>}
            <p style={{fontSize:13,color:C.muted}}>Used for your invoice and account access.</p>
          </div>
        )}

        {/* Pass 24h */}
        <div style={{background:'#f0f9ff',border:`1px solid #bae6fd`,borderRadius:16,padding:20,marginBottom:14,textAlign:'left',opacity:emailStep?0.4:1,transition:'opacity 0.2s'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
            <div style={{fontSize:18,fontWeight:700,color:'#0369a1'}}>⚡ Pass 24h</div>
            <div style={{fontSize:24,fontWeight:800,color:C.text}}>9€</div>
          </div>
          <div style={{fontSize:15,color:C.muted,marginBottom:14}}>Analyses illimitées pendant 24h. Idéal pour une session de recherche.</div>
          <button
            onClick={() => handleCheckout(PRICE_PASS)}
            disabled={loadingVariant !== null || emailStep}
            style={{width:'100%',padding:'13px',borderRadius:12,border:'none',background:'#0369a1',color:'#fff',fontSize:16,fontWeight:700,cursor:emailStep?'not-allowed':'pointer'}}>
            {loadingVariant === PRICE_PASS ? '...' : 'Acheter le Pass 24h'}
          </button>
        </div>

        {/* Pro Mensuel */}
        <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:16,padding:20,marginBottom:20,textAlign:'left',opacity:emailStep?0.4:1,transition:'opacity 0.2s'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
            <div style={{fontSize:18,fontWeight:700,color:C.accent}}>🏆 Pro Mensuel</div>
            <div style={{fontSize:24,fontWeight:800,color:C.text}}>19€<span style={{fontSize:16,fontWeight:400,color:C.muted}}>/mois</span></div>
          </div>
          <div style={{fontSize:15,color:C.muted,marginBottom:14}}>Analyses illimitées chaque mois. Pour le chasseur en recherche active.</div>
          <button
            onClick={() => handleCheckout(PRICE_PRO)}
            disabled={loadingVariant !== null || emailStep}
            style={{width:'100%',padding:'13px',borderRadius:12,border:'none',background:C.accent,color:'#fff',fontSize:16,fontWeight:700,cursor:emailStep?'not-allowed':'pointer',boxShadow:emailStep?'none':'0 4px 16px rgba(180,83,9,0.3)'}}>
            {loadingVariant === PRICE_PRO ? '...' : 'Passer en Pro'}
          </button>
        </div>

        <button onClick={onClose} style={{width:'100%',padding:'12px',borderRadius:12,border:`1px solid ${C.border2}`,background:'transparent',color:C.muted,fontSize:18,cursor:'pointer'}}>
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
          <div style={{display:'flex',justifyContent:'space-between',fontSize:18,color:C.muted,marginBottom:5}}>
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
    <span style={{background:color+'18',color,border:`1px solid ${color}33`,borderRadius:20,padding:'4px 12px',fontSize:18,fontWeight:600,display:'inline-flex',alignItems:'center'}}>
      {children}
    </span>
  );
}

function Section({ title, color, children }) {
  return (
    <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:18,padding:24}}>
      <div style={{fontSize:18,letterSpacing:2,color:color||C.accent,textTransform:'uppercase',fontWeight:700,marginBottom:16}}>{title}</div>
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
              <span style={{fontSize:18,letterSpacing:2,color:cityColor,fontWeight:700,textTransform:'uppercase'}}>{t.aiTag}</span>
              {data.ville&&<span style={{background:cityColor+'18',color:cityColor,border:`1px solid ${cityColor}44`,borderRadius:20,padding:'3px 12px',fontSize:18,fontWeight:700}}>📍 {data.ville}</span>}
            </div>
            <div style={{fontSize:24,fontWeight:800,marginBottom:12,lineHeight:1.3,color:C.text}}>{data.titre}</div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:16}}>
              {data.adresse&&<Chip color={C.muted}>{data.adresse}</Chip>}
              {data.annee_construction&&<Chip color={C.muted}>🏗 {data.annee_construction}</Chip>}
              {data.classe_energetique&&<Chip color={dpeColor}>DPE {data.classe_energetique}</Chip>}
              {data.garage&&<Chip color={CITY_COLORS.Madrid}>🚗 Garage</Chip>}
              {data.piscine&&<Chip color={CITY_COLORS.Barcelona}>🏊 Pool</Chip>}
              {data.trastero&&<Chip color={C.accent}>📦 Storage</Chip>}
              {data.neuf&&<Chip color={C.green}>✨ New</Chip>}
            </div>
            <div style={{fontSize:34,fontWeight:800,color:C.text}}>{prix.toLocaleString('fr')} €
              <span style={{fontSize:18,color:C.muted,fontWeight:400,marginLeft:10}}>{Math.round(prixM2).toLocaleString('fr')} €/m²</span>
            </div>
          </div>
          <ScoreGauge score={data.note_globale||5} t={t} size={110}/>
        </div>
        <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:16,padding:20,marginTop:20}}>
          <div style={{fontSize:18,letterSpacing:2,color:C.tag,textTransform:'uppercase',fontWeight:700,marginBottom:14}}>{t.estimatedRent}</div>
          <div style={{display:'flex',gap:14,marginBottom:12}}>
            {[{l:t.rentMin,v:data.loyer_estime_min,h:false},{l:t.rentMedian,v:data.loyer_estime_median,h:true},{l:t.rentMax,v:data.loyer_estime_max,h:false}].map(x=>(
              <div key={x.l} style={{flex:1,textAlign:'center',background:'#fff',borderRadius:12,padding:'12px 8px',border:`1px solid ${x.h?C.accent+'55':C.border}`}}>
                <div style={{fontSize:18,color:C.muted,textTransform:'uppercase',letterSpacing:1,marginBottom:4}}>{x.l}</div>
                <div style={{fontSize:x.h?28:18,fontWeight:800,color:x.h?C.accent:C.muted}}>{x.v?.toLocaleString('fr')} €</div>
              </div>
            ))}
          </div>
          <div style={{fontSize:18,color:C.tag,background:'rgba(255,255,255,0.5)',borderRadius:10,padding:'10px 14px',lineHeight:1.6}}>💡 {data.justification_loyer}</div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:14,marginBottom:14}}>
        <Section title={t.yield} color={C.accent}>
          <RentaBar brute={rentaBrute} nette={rentaNette} t={t}/>
          <div style={{marginTop:14,paddingTop:12,borderTop:`1px solid ${C.border}`,fontSize:18,color:C.muted}}>
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
            <div key={r.l} style={{display:'flex',justifyContent:'space-between',alignItems:'center',fontSize:15,padding:'8px 0',borderBottom:`1px solid ${C.border}`}}>
              <span style={{color:C.muted}}>{r.l}</span><span style={{color:r.c,fontWeight:700,whiteSpace:'nowrap',marginLeft:8}}>{r.v}</span>
            </div>
          ))}
        </Section>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:14,marginBottom:14}}>
        <div style={{background:'#f0fdf4',border:`1px solid #bbf7d0`,borderRadius:18,padding:20}}>
          <div style={{fontSize:18,letterSpacing:2,color:C.green,textTransform:'uppercase',fontWeight:700,marginBottom:12}}>{t.strengths}</div>
          {(data.points_positifs||[]).map((p,i)=>(
            <div key={i} style={{fontSize:15,color:'#166534',padding:'6px 0',borderBottom:'1px solid #dcfce7',display:'flex',gap:8,lineHeight:1.5}}><span style={{color:C.green,fontWeight:700,flexShrink:0}}>+</span>{p}</div>
          ))}
        </div>
        <div style={{background:'#fff5f5',border:`1px solid #fecaca`,borderRadius:18,padding:20}}>
          <div style={{fontSize:18,letterSpacing:2,color:C.red,textTransform:'uppercase',fontWeight:700,marginBottom:12}}>{t.weaknesses}</div>
          {(data.points_negatifs||[]).map((p,i)=>(
            <div key={i} style={{fontSize:15,color:'#991b1b',padding:'6px 0',borderBottom:'1px solid #fee2e2',display:'flex',gap:8,lineHeight:1.5}}><span style={{color:C.red,fontWeight:700,flexShrink:0}}>−</span>{p}</div>
          ))}
        </div>
      </div>

      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:18,padding:24,fontSize:18,color:C.text,lineHeight:1.7}}>
        <span style={{fontWeight:800,color:C.accent}}>{t.verdict} : </span>{data.verdict}
        {url&&<div style={{marginTop:10}}><a href={url} target="_blank" rel="noopener noreferrer" style={{fontSize:18,color:C.accent,textDecoration:'none',fontWeight:600}}>{t.sourceLink} ↗</a></div>}
      </div>

      {/* Socio-demographic block */}
      {(data.renta_district_persona || data.paro_region || data.district_profile) && (
        <div style={{background:'#f0f9ff',border:`1px solid #bae6fd`,borderRadius:18,padding:20,marginTop:14}}>
          <div style={{fontSize:18,letterSpacing:2,color:'#0369a1',textTransform:'uppercase',fontWeight:700,marginBottom:14}}>🏘 {t.socioTitle}</div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:10,marginBottom:12}}>
            {data.renta_district_persona && (
              <div style={{background:'#fff',borderRadius:12,padding:'12px 14px'}}>
                <div style={{fontSize:18,color:'#64748b',marginBottom:3,fontWeight:600}}>{t.socioRentaPersona}</div>
                <div style={{fontSize:24,fontWeight:800,color:'#0c4a6e'}}>{data.renta_district_persona.toLocaleString('fr')} €</div>
                <div style={{fontSize:18,color:'#94a3b8',marginTop:2}}>{t.socioPerYear}</div>
              </div>
            )}
            {data.renta_district_hogar && (
              <div style={{background:'#fff',borderRadius:12,padding:'12px 14px'}}>
                <div style={{fontSize:18,color:'#64748b',marginBottom:3,fontWeight:600}}>{t.socioRentaHogar}</div>
                <div style={{fontSize:24,fontWeight:800,color:'#0c4a6e'}}>{data.renta_district_hogar.toLocaleString('fr')} €</div>
                <div style={{fontSize:18,color:'#94a3b8',marginTop:2}}>{t.socioPerYear}</div>
              </div>
            )}
            {data.paro_region && (
              <div style={{background:'#fff',borderRadius:12,padding:'12px 14px'}}>
                <div style={{fontSize:18,color:'#64748b',marginBottom:3,fontWeight:600}}>{t.socioParo}</div>
                <div style={{fontSize:24,fontWeight:800,color:data.paro_region>12?'#dc2626':data.paro_region>10?'#d97706':'#16a34a'}}>{data.paro_region}%</div>
                <div style={{fontSize:18,color:'#94a3b8',marginTop:2}}>EPA T4 2025</div>
              </div>
            )}
          </div>
          {data.district_profile && (
            <div style={{fontSize:18,color:'#0369a1',background:'rgba(255,255,255,0.6)',borderRadius:10,padding:'8px 12px',lineHeight:1.6}}>
              👥 {data.district_profile}
            </div>
          )}
          <div style={{width:'100%',fontSize:18,color:'#94a3b8',borderTop:`1px solid #e0f2fe`,paddingTop:8,marginTop:10}}>
            {t.socioSource}
          </div>
        </div>
      )}

      {/* INE Data block */}
      {(data.irav || data.ipva_city_change) && (
        <div style={{background:'#fffbeb',border:`1px solid #fde68a`,borderRadius:18,padding:20,marginTop:14,display:'flex',gap:20,flexWrap:'wrap'}}>
          <div style={{fontSize:18,letterSpacing:2,color:C.tag,textTransform:'uppercase',fontWeight:700,width:'100%',marginBottom:4}}>📊 {t.ineData}</div>
          {data.irav && (
            <div style={{flex:1,minWidth:180}}>
              <div style={{fontSize:18,color:C.muted,marginBottom:4}}>{t.iravLabel} <span style={{fontSize:18,color:C.muted}}>({data.irav_period})</span></div>
              <div style={{fontSize:30,fontWeight:800,color:C.accent}}>{data.irav}%</div>
              <div style={{fontSize:18,color:C.muted,marginTop:2}}>{t.iravNote}</div>
            </div>
          )}
          {data.ipva_city_change && (
            <div style={{flex:1,minWidth:180}}>
              <div style={{fontSize:18,color:C.muted,marginBottom:4}}>{t.ipvaLabel} {data.ville}</div>
              <div style={{fontSize:30,fontWeight:800,color:data.ipva_city_change>0?C.green:C.red}}>{data.ipva_city_change>0?'+':''}{data.ipva_city_change}%</div>
              <div style={{fontSize:18,color:C.muted,marginTop:2}}>{t.ipvaNote}</div>
            </div>
          )}
          <div style={{width:'100%',fontSize:18,color:C.muted,borderTop:`1px solid ${C.border}`,paddingTop:8,marginTop:4}}>Source : INE — Instituto Nacional de Estadística</div>
        </div>
      )}

      {/* CapEx Alert */}
      {data.capex_alerte && (
        <div style={{background:'#fff7ed',border:`2px solid #fed7aa`,borderRadius:18,padding:20,marginTop:14}}>
          <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:12}}>
            <span style={{fontSize:24}}>⚠️</span>
            <div style={{fontSize:13,letterSpacing:2,color:'#c2410c',textTransform:'uppercase',fontWeight:700}}>
              Détecteur CapEx — Bien à rénover
            </div>
          </div>
          <div style={{fontSize:15,color:'#7c2d12',lineHeight:1.7,marginBottom:14}}>
            {data.capex_note}
          </div>
          {data.capex_estimation_m2_low && data.capex_estimation_m2_high && data.surface && (
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:10,marginBottom:12}}>
              {[
                { l: 'Coût min estimé', v: `${Math.round(data.capex_estimation_m2_low * data.surface).toLocaleString('fr')} €`, sub: `${data.capex_estimation_m2_low} €/m²` },
                { l: 'Coût max estimé', v: `${Math.round(data.capex_estimation_m2_high * data.surface).toLocaleString('fr')} €`, sub: `${data.capex_estimation_m2_high} €/m²` },
                { l: 'Impact rendement', v: 'Année 1', sub: 'cash-flow négatif probable' },
              ].map(m => (
                <div key={m.l} style={{background:'#fff',borderRadius:12,padding:'12px 14px',border:'1px solid #fed7aa'}}>
                  <div style={{fontSize:12,color:'#9a3412',marginBottom:3,fontWeight:600}}>{m.l}</div>
                  <div style={{fontSize:18,fontWeight:800,color:'#c2410c'}}>{m.v}</div>
                  <div style={{fontSize:11,color:'#a16207',marginTop:2}}>{m.sub}</div>
                </div>
              ))}
            </div>
          )}
          {data.capex_keywords && data.capex_keywords.length > 0 && (
            <div style={{fontSize:12,color:'#9a3412',background:'rgba(255,255,255,0.6)',borderRadius:8,padding:'6px 10px'}}>
              🔍 Mots-clés détectés : {data.capex_keywords.join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Simulateur interactif */}
      {data.prix > 0 && data.loyer_estime_median > 0 && (
        <SimulateurSliders data={data} t={t} />
      )}
    </div>
  );
}

function SimulateurSliders({ data, t }) {
  const prix = data.prix || 0;
  const loyerBase = data.loyer_estime_median || 0;
  const charges = data.charges_copro_estimees || prix * 0.003 / 12;
  const ibi = data.ibi_annuel_estime || prix * 0.004;

  const [apport, setApport] = useState(20);
  const [taux, setTaux] = useState(3.5);
  const [loyerPct, setLoyerPct] = useState(0);

  // Input field states for manual entry
  const [apportInput, setApportInput] = useState('20');
  const [tauxInput, setTauxInput] = useState('3.5');
  const [loyerInput, setLoyerInput] = useState('0');
  const [fiscalMode, setFiscalMode] = useState('non_resident');
  const [ibiCustom, setIbiCustom] = useState(null);
  const [ibiEditing, setIbiEditing] = useState(false);
  const [ibiInput, setIbiInput] = useState('');
  const [chargesDeduct, setChargesDeduct] = useState(0);
  const [chargesDeductInput, setChargesDeductInput] = useState('0');
  const [chargesDeductEditing, setChargesDeductEditing] = useState(false);

  const ibiVal = ibiCustom !== null ? ibiCustom : ibi;
  const loyer = Math.round(loyerBase * (1 + loyerPct / 100));
  const emprunt = prix * (1 - apport / 100);
  const duree = 25;
  const tauxM = taux / 100 / 12;
  const mensualite = emprunt > 0 && tauxM > 0
    ? Math.round(emprunt * tauxM / (1 - Math.pow(1 + tauxM, -duree * 12)))
    : 0;

  function calcIRPF(base) {
    if (base <= 0) return 0;
    const tranches = [
      { max: 12450, rate: 0.19 },
      { max: 20200, rate: 0.24 },
      { max: 35200, rate: 0.30 },
      { max: 60000, rate: 0.37 },
      { max: Infinity, rate: 0.45 },
    ];
    let impot = 0, prev = 0;
    for (const t of tranches) {
      if (base <= prev) break;
      impot += (Math.min(base, t.max) - prev) * t.rate;
      prev = t.max;
    }
    return impot;
  }

  const loyerAnnuel = loyer * 11.5;
  const chargesAn = charges * 12;
  const baseAvantImpot = loyerAnnuel - chargesAn - ibiVal;
  // Résident : on déduit les charges supplémentaires (amortissement, intérêts...) avant abattement
  const baseResidentAvantAbattement = baseAvantImpot - (fiscalMode === 'resident_60' ? chargesDeduct : 0);
  const impot = fiscalMode === 'non_resident'
    ? (baseAvantImpot > 0 ? baseAvantImpot * 0.19 : 0)
    : calcIRPF(baseResidentAvantAbattement > 0 ? baseResidentAvantAbattement * 0.40 : 0);
  const revenusNets = baseAvantImpot - impot;
  const cashflow = Math.round(revenusNets / 12 - mensualite);
  const rentaNette = prix > 0 ? (revenusNets / prix) * 100 : 0;
  const cashflowColor = cashflow >= 0 ? C.green : C.red;

  function clamp(val, min, max) { return Math.min(max, Math.max(min, val)); }

  function SliderRow({ label, value, min, max, step, unit, onChange, inputVal, setInputVal, format, displayVal }) {
    const pct = ((value - min) / (max - min)) * 100;
    const trackRef = useRef(null);

    function valueFromPosition(clientX) {
      const rect = trackRef.current.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const raw = min + ratio * (max - min);
      const stepped = Math.round(raw / step) * step;
      return Math.min(max, Math.max(min, parseFloat(stepped.toFixed(2))));
    }

    function handleTrackClick(e) {
      const v = valueFromPosition(e.clientX);
      onChange(v);
      setInputVal(String(v));
    }

    function handleTouchStart(e) {
      e.preventDefault();
      const touch = e.touches[0];
      const v = valueFromPosition(touch.clientX);
      onChange(v);
      setInputVal(String(v));
    }

    function handleTouchMove(e) {
      e.preventDefault();
      const touch = e.touches[0];
      const v = valueFromPosition(touch.clientX);
      onChange(v);
      setInputVal(String(v));
    }

    function handleInputBlur() {
      const v = parseFloat(inputVal);
      if (!isNaN(v)) {
        const clamped = clamp(v, min, max);
        onChange(clamped);
        setInputVal(String(clamped));
      } else {
        setInputVal(String(value));
      }
    }

    return (
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <span style={{ fontSize: 14, color: C.muted, fontWeight: 600 }}>{label}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <input
              type="number" value={inputVal} min={min} max={max} step={step}
              onChange={e => setInputVal(e.target.value)}
              onBlur={handleInputBlur}
              style={{ width: 64, padding: '4px 8px', borderRadius: 8, border: `1px solid ${C.border2}`, background: C.bg, fontSize: 15, fontWeight: 800, color: C.accent, textAlign: 'right', outline: 'none' }}
            />
            <span style={{ fontSize: 13, color: C.muted, fontWeight: 600 }}>{unit}</span>
          </div>
        </div>

        {/* Custom touch-native track */}
        <div
          ref={trackRef}
          onClick={handleTrackClick}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          style={{ position: 'relative', height: 28, display: 'flex', alignItems: 'center', cursor: 'pointer', touchAction: 'none', userSelect: 'none' }}
        >
          {/* Background track */}
          <div style={{ position: 'absolute', left: 0, right: 0, height: 6, background: C.border, borderRadius: 3 }} />
          {/* Filled track */}
          <div style={{ position: 'absolute', left: 0, height: 6, width: `${pct}%`, background: C.accent, borderRadius: 3 }} />
          {/* Thumb */}
          <div style={{
            position: 'absolute',
            left: `${pct}%`,
            transform: 'translateX(-50%)',
            width: 26, height: 26,
            background: '#fff',
            border: `3px solid ${C.accent}`,
            borderRadius: '50%',
            boxShadow: '0 2px 8px rgba(180,83,9,0.35)',
            pointerEvents: 'none',
          }} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2, fontSize: 11, color: C.muted }}>
          <span>{min}{unit}</span>
          {displayVal && <span style={{ color: C.accent, fontWeight: 700 }}>{displayVal}</span>}
          <span>{max}{unit}</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: C.card, border: `2px solid ${cashflow >= 0 ? '#bbf7d0' : '#fecaca'}`, borderRadius: 18, padding: '20px 16px', marginTop: 14 }}>

      {/* Header + fiscal toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
        <div style={{ fontSize: 13, letterSpacing: 2, color: C.accent, textTransform: 'uppercase', fontWeight: 700 }}>🎛 Simulateur</div>
        <div style={{ display: 'flex', background: C.bg, border: `1px solid ${C.border}`, borderRadius: 10, padding: 3, gap: 2 }}>
          {[
            { key: 'non_resident', label: '🌍 Non-résident · 19%' },
            { key: 'resident_60', label: '🇪🇸 Résident · IRPF −60%' },
          ].map(opt => (
            <button key={opt.key} onClick={() => setFiscalMode(opt.key)} style={{
              padding: '6px 10px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 700,
              background: fiscalMode === opt.key ? C.accent : 'transparent',
              color: fiscalMode === opt.key ? '#fff' : C.muted,
            }}>{opt.label}</button>
          ))}
        </div>
      </div>

      {/* IBI éditable */}
      <div style={{ background: C.bg, borderRadius: 10, padding: '10px 14px', marginBottom: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, color: C.muted, fontWeight: 600 }}>IBI annuel {ibiCustom !== null ? <span style={{color:'#16a34a'}}>✓ exact</span> : '(estimé)'}</span>
        {ibiEditing ? (
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="number" value={ibiInput} onChange={e => setIbiInput(e.target.value)} autoFocus
              style={{ width: 80, padding: '4px 8px', borderRadius: 8, border: `1px solid ${C.accent}`, fontSize: 14, fontWeight: 700, color: C.accent, textAlign: 'right', outline: 'none' }} />
            <span style={{ fontSize: 12, color: C.muted }}>€</span>
            <button onClick={() => { const v = parseFloat(ibiInput); if (!isNaN(v) && v >= 0) setIbiCustom(v); setIbiEditing(false); }}
              style={{ padding: '4px 10px', borderRadius: 8, border: 'none', background: C.accent, color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>✓</button>
            <button onClick={() => setIbiEditing(false)}
              style={{ padding: '4px 8px', borderRadius: 8, border: `1px solid ${C.border}`, background: 'transparent', color: C.muted, fontSize: 12, cursor: 'pointer' }}>✕</button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: C.text }}>{Math.round(ibiVal).toLocaleString('fr')} €</span>
            <button onClick={() => { setIbiEditing(true); setIbiInput(String(Math.round(ibiVal))); }}
              style={{ background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 8, padding: '3px 8px', cursor: 'pointer', fontSize: 13 }}>✏️</button>
            {ibiCustom !== null && <button onClick={() => setIbiCustom(null)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 11, color: C.muted, textDecoration: 'underline' }}>reset</button>}
          </div>
        )}
      </div>

      {/* Charges déductibles supplémentaires — résident uniquement */}
      {fiscalMode === 'resident_60' && (
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 10, padding: '10px 14px', marginBottom: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: 13, color: '#166534', fontWeight: 600 }}>Charges déductibles/an</span>
            <div style={{ fontSize: 11, color: '#4ade80', marginTop: 2 }}>amortissement · intérêts · frais de gestion</div>
          </div>
          {chargesDeductEditing ? (
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input type="number" value={chargesDeductInput} onChange={e => setChargesDeductInput(e.target.value)} autoFocus
                style={{ width: 80, padding: '4px 8px', borderRadius: 8, border: '1px solid #16a34a', fontSize: 14, fontWeight: 700, color: '#16a34a', textAlign: 'right', outline: 'none' }} />
              <span style={{ fontSize: 12, color: C.muted }}>€</span>
              <button onClick={() => { const v = parseFloat(chargesDeductInput); setChargesDeduct(!isNaN(v) && v >= 0 ? v : 0); setChargesDeductEditing(false); }}
                style={{ padding: '4px 10px', borderRadius: 8, border: 'none', background: '#16a34a', color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>✓</button>
              <button onClick={() => setChargesDeductEditing(false)}
                style={{ padding: '4px 8px', borderRadius: 8, border: `1px solid ${C.border}`, background: 'transparent', color: C.muted, fontSize: 12, cursor: 'pointer' }}>✕</button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 15, fontWeight: 800, color: '#16a34a' }}>{chargesDeduct > 0 ? `−${chargesDeduct.toLocaleString('fr')} €` : 'Non renseigné'}</span>
              <button onClick={() => { setChargesDeductEditing(true); setChargesDeductInput(String(chargesDeduct)); }}
                style={{ background: 'transparent', border: '1px solid #bbf7d0', borderRadius: 8, padding: '3px 8px', cursor: 'pointer', fontSize: 13 }}>✏️</button>
              {chargesDeduct > 0 && <button onClick={() => setChargesDeduct(0)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 11, color: C.muted, textDecoration: 'underline' }}>reset</button>}
            </div>
          )}
        </div>
      )}

      {/* Sliders */}
      <SliderRow label="Apport personnel" value={apport} min={10} max={90} step={5} unit="%" onChange={v => setApport(v)} inputVal={apportInput} setInputVal={setApportInput} />
      <SliderRow label="Taux d'intérêt" value={taux} min={1} max={6} step={0.1} unit="%" onChange={v => setTaux(v)} inputVal={tauxInput} setInputVal={setTauxInput} />
      <SliderRow label="Loyer mensuel" value={loyerPct} min={-50} max={50} step={5} unit="%" onChange={v => setLoyerPct(v)} inputVal={loyerInput} setInputVal={setLoyerInput} displayVal={`${loyer.toLocaleString('fr')} €/mois`} />

      {/* Results grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(130px,1fr))', gap: 10, marginTop: 8, marginBottom: 14 }}>
        {[
          { l: 'Apport', v: `${Math.round(prix * apport / 100).toLocaleString('fr')} €`, c: C.text },
          { l: 'Mensualité', v: `${mensualite.toLocaleString('fr')} €/mois`, c: C.red },
          { l: 'Revenus nets/mois', v: `${Math.round(revenusNets / 12).toLocaleString('fr')} €`, c: C.green },
          { l: 'Impôts/an', v: `−${Math.round(impot).toLocaleString('fr')} €`, c: '#d97706' },
          { l: 'Rendement net', v: `${rentaNette.toFixed(2)}%`, c: rentaNette >= 4 ? C.green : rentaNette >= 2 ? '#d97706' : C.red },
        ].map(r => (
          <div key={r.l} style={{ background: C.bg, borderRadius: 10, padding: '10px 12px' }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, marginBottom: 3 }}>{r.l}</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: r.c }}>{r.v}</div>
          </div>
        ))}
      </div>

      {/* Cash-flow */}
      <div style={{ background: cashflow >= 0 ? '#f0fdf4' : '#fff5f5', border: `1px solid ${cashflow >= 0 ? '#bbf7d0' : '#fecaca'}`, borderRadius: 14, padding: 16, textAlign: 'center' }}>
        <div style={{ fontSize: 12, color: C.muted, fontWeight: 600, marginBottom: 4 }}>CASH-FLOW NET MENSUEL</div>
        <div style={{ fontSize: 36, fontWeight: 900, color: cashflowColor, fontFamily: 'Georgia, serif' }}>
          {cashflow >= 0 ? '+' : ''}{cashflow.toLocaleString('fr')} €
        </div>
        <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>loyer − mensualité − charges − IBI − impôts</div>
      </div>

      <div style={{ fontSize: 11, color: C.muted, marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}` }}>
        {fiscalMode === 'non_resident'
          ? 'Non-résident : 19% flat sur revenus nets · crédit 25 ans · 11.5 mois/an'
          : 'Résident : IRPF progressif par tranches avec abattement 60% (Ley de Vivienda) · crédit 25 ans'}
      </div>
    </div>
  );
}
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

  // Quota state
  const [showQuotaModal, setShowQuotaModal] = useState(false);

  const t = T[lang];

  useEffect(() => {
    fetch('/api/market-data')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setMarketData(d); })
      .catch(() => {});
  }, []);

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
    } else if (mode === 'image') {
      if (!images || images.length === 0) return;
    } else {
      if (manualText.trim().length < 50) return;
      content = manualText;
    }
    setStatus('analyzing'); setStatusMsg(t.analyzing);
    try {
      const body = mode === 'image'
        ? { images, lang }
        : { content: `URL: ${url||'N/A'}\n\n${content}`, lang };
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
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true"/>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
      </Head>

      <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WSVSC97J" height="0" width="0" style={{display:'none',visibility:'hidden'}}></iframe></noscript>

      {showQuotaModal && <QuotaModal t={t} onClose={()=>setShowQuotaModal(false)} userEmail={userEmail}/>}

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
                  color:lang===l?'#fff':C.muted,fontSize:18,fontWeight:700,
                  transition:'all 0.2s',textTransform:'uppercase',letterSpacing:1
                }}>{l}</button>
              ))}
            </div>
          </div>

          <div style={{display:'inline-flex',alignItems:'center',gap:8,background:C.accentBg,border:`1px solid #fde68a`,borderRadius:20,padding:'7px 20px',marginBottom:22}}>
            <div style={{width:8,height:8,borderRadius:'50%',background:C.accent,animation:'blink 2s infinite'}}/>
            <span style={{fontSize:18,letterSpacing:3,color:C.tag,fontWeight:700,textTransform:'uppercase'}}>{t.badge}</span>
          </div>

          <h1 style={{fontSize:72,fontWeight:900,color:C.text,marginBottom:18,lineHeight:1,letterSpacing:'-3px',fontFamily:'Playfair Display,serif'}}>
            buy2rent<span style={{color:C.accent}}>.io</span>
          </h1>
          <p style={{fontSize:21,color:C.muted,maxWidth:580,margin:'0 auto 28px',lineHeight:1.6}}>{t.subtitle}</p>

          <div style={{display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
            {Object.entries(CITY_COLORS).map(([city])=>(
              <span key={city} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:20,padding:'7px 20px',fontSize:18,fontWeight:600,color:C.accent,boxShadow:'0 2px 8px rgba(0,0,0,0.06)'}}>{city}</span>
            ))}
          </div>
        </div>


        {/* Email status bar */}
        {userEmail && (
          <div style={{background:C.accentBg,border:`1px solid #fde68a`,borderRadius:14,padding:'12px 20px',marginBottom:20,display:'flex',alignItems:'center',justifyContent:'space-between',fontSize:18}}>
            <span style={{color:C.tag}}>✅ {userEmail}</span>
            <span style={{color:C.muted,fontSize:16}}>{t.analysesLeft}</span>
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
                    color:mode===m.k?'#fff':C.text,fontSize:18,fontWeight:600,transition:'all 0.2s'
                  }}>{m.label}</button>
                ))}
              </div>

              {mode==='url'?(
                <div>
                  <label style={{fontSize:18,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.urlLabel}</label>
                  <input value={url} onChange={e=>setUrl(e.target.value)} onKeyDown={e=>e.key==='Enter'&&run()} placeholder={t.urlPlaceholder}
                    style={{width:'100%',background:C.bg,border:`1px solid ${C.border2}`,borderRadius:14,padding:'18px 20px',color:C.text,fontSize:18,transition:'border-color 0.2s'}}
                    onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border2}/>
                </div>
              ):mode==='image'?(
                <div>
                  <label style={{fontSize:18,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.imageLabel}</label>
                  {/* Image previews */}
                  <div style={{display:'flex',gap:10,marginBottom:images.length>0?12:0,flexWrap:'wrap'}}>
                    {images.map((img,i)=>(
                      <div key={i} style={{position:'relative',width:120,height:100,borderRadius:10,overflow:'hidden',border:`1px solid ${C.border}`}}>
                        <img src={img.preview} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
                        <button onClick={()=>setImages(prev=>prev.filter((_,j)=>j!==i))}
                          style={{position:'absolute',top:4,right:4,background:'rgba(0,0,0,0.6)',border:'none',color:'#fff',borderRadius:'50%',width:22,height:22,cursor:'pointer',fontSize:18,display:'flex',alignItems:'center',justifyContent:'center'}}>✕</button>
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
                            <div style={{color:C.muted,fontSize:18,fontWeight:500}}>{t.imagePlaceholder}</div>
                            <div style={{color:C.muted,fontSize:18,marginTop:6,opacity:0.7}}>{t.imageNote}</div>
                          </div>
                        ):(
                          <div style={{textAlign:'center',padding:8}}>
                            <div style={{fontSize:22}}>+</div>
                            <div style={{color:C.muted,fontSize:16}}>{t.imageAdd}</div>
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
                  <label style={{fontSize:18,letterSpacing:2,color:C.accent,textTransform:'uppercase',fontWeight:700,display:'block',marginBottom:10}}>{t.textLabel}</label>
                  <textarea value={manualText} onChange={e=>setManualText(e.target.value)} placeholder={t.textPlaceholder}
                    style={{width:'100%',height:260,background:C.bg,border:`1px solid ${C.border2}`,borderRadius:14,padding:'18px 20px',color:C.text,fontSize:18,resize:'vertical',lineHeight:1.7,transition:'border-color 0.2s'}}
                    onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border2}/>
                </div>
              )}

              <button onClick={run} disabled={isLoading||!canRun} style={{
                width:'100%',marginTop:24,padding:'22px',borderRadius:16,border:'none',
                background:isLoading||!canRun?C.border:C.accent,
                color:isLoading||!canRun?C.muted:'#fff',fontSize:18,fontWeight:800,
                cursor:isLoading||!canRun?'not-allowed':'pointer',letterSpacing:'0.5px',
                display:'flex',alignItems:'center',justifyContent:'center',gap:12,transition:'all 0.2s',
                boxShadow:isLoading||!canRun?'none':'0 6px 20px rgba(180,83,9,0.3)'
              }}>
                {isLoading?(
                  <><div style={{width:20,height:20,border:'2px solid #fff',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>{statusMsg}</>
                ):(canRun?t.cta:t.ctaDisabled)}
              </button>

              {status==='error'&&(
                <div style={{marginTop:16,padding:16,background:'#fff5f5',border:`1px solid #fecaca`,borderRadius:12,fontSize:18,color:C.red}}>⚠️ {statusMsg}</div>
              )}
            </div>

            <button onClick={()=>{setMode('manual');setManualText('Calle de Isabel Clara Eugenia, 37\nSanchinarro, Madrid\n560,000 euros\n\n2 dormitorios y 2 baños, urbanización privada con piscina, jardines, gimnasio, coworking, zona infantil, conserjería y ascensor. 1 plaza de garaje y trastero.\n\n84 m² construidos, planta 3ª exterior, construido en 2005, calefacción gas natural, aire acondicionado.\n\nCertificado energético: 167 kWh/m² año, 25 kg CO2/m² año');}}
              style={{width:'100%',padding:'15px',borderRadius:14,background:'transparent',border:`1px dashed ${C.border2}`,color:C.muted,fontSize:18,cursor:'pointer',transition:'all 0.2s',fontWeight:500}}
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
              <span style={{fontSize:18,letterSpacing:2,color:C.muted,textTransform:'uppercase',fontWeight:700}}>{t.marketTitle}</span>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(120px,1fr))',gap:10}}>
              <div style={{background:C.bg,borderRadius:12,padding:'12px 14px',display:'flex',flexDirection:'column'}}>
                <div style={{fontSize:12,color:C.muted,fontWeight:600,height:34,lineHeight:1.3,display:'flex',alignItems:'center'}}>Euribor 12M</div>
                <div style={{fontSize:24,fontWeight:800,color:C.text}}>{marketData.euribor.value}%</div>
                <div style={{fontSize:12,color:C.muted,marginTop:2}}>{marketData.euribor.period}</div>
              </div>
              <div style={{background:C.bg,borderRadius:12,padding:'12px 14px',display:'flex',flexDirection:'column'}}>
                <div style={{fontSize:12,color:C.muted,fontWeight:600,height:34,lineHeight:1.3,display:'flex',alignItems:'center'}}>{t.mortgageRate}</div>
                <div style={{fontSize:24,fontWeight:800,color:C.text}}>{marketData.mortgage_rate.value}%</div>
                <div style={{fontSize:12,color:C.muted,marginTop:2}}>{marketData.mortgage_rate.period}</div>
              </div>
              {Object.entries(marketData.ipv).map(([city, d]) => (
                <div key={city} style={{background:C.bg,borderRadius:12,padding:'12px 14px',display:'flex',flexDirection:'column'}}>
                  <div style={{fontSize:12,color:C.muted,fontWeight:600,height:34,lineHeight:1.3,display:'flex',alignItems:'center',textTransform:'capitalize'}}>{t.ipvLabel} {city === 'nacional' ? 'Nacional' : city.charAt(0).toUpperCase()+city.slice(1)}</div>
                  <div style={{fontSize:24,fontWeight:800,color:parseFloat(d.change)>0?'#22c55e':C.red}}>{parseFloat(d.change)>0?'+':''}{d.change}%</div>
                  <div style={{fontSize:12,color:C.muted,marginTop:2}}>{d.period}</div>
                </div>
              ))}
            </div>
            <div style={{marginTop:10,fontSize:18,color:C.muted,borderTop:`1px solid ${C.border}`,paddingTop:10}}>
              📊 {t.marketSource} {marketData.live ? 'Live' : 'Données de référence'}
            </div>
          </div>
        )}
        {/* Result */}
        {result&&(
          <div>
            <ResultCard data={result} url={url} t={t}/>
            <button onClick={reset} style={{width:'100%',marginTop:18,padding:'18px',borderRadius:14,background:'transparent',border:`1px solid ${C.border2}`,color:C.muted,fontSize:18,cursor:'pointer',fontWeight:600,transition:'all 0.2s'}}
              onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent}}
              onMouseLeave={e=>{e.target.style.borderColor=C.border2;e.target.style.color=C.muted}}>
              {t.newAnalysis}
            </button>
          </div>
        )}

        {/* History */}
        {history.length>1&&!result&&(
          <div style={{marginTop:40}}>
            <div style={{fontSize:18,letterSpacing:3,color:C.muted,textTransform:'uppercase',marginBottom:14,fontWeight:600}}>{t.recentTitle}</div>
            {history.slice(1).map((h,i)=>{
              const cityColor = CITY_COLORS[h.result.ville] || C.accent;
              return (
                <div key={i} onClick={()=>{setResult(h.result);setUrl(h.url);}}
                  style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:14,padding:'16px 22px',cursor:'pointer',display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10,transition:'all 0.2s',boxShadow:'0 2px 8px rgba(0,0,0,0.04)'}}
                  onMouseEnter={e=>{e.currentTarget.style.borderColor=C.accent;e.currentTarget.style.boxShadow='0 4px 16px rgba(180,83,9,0.1)'}}
                  onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border;e.currentTarget.style.boxShadow='0 2px 8px rgba(0,0,0,0.04)'}}>
                  <div>
                    <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:3}}>
                      {h.result.ville&&<span style={{fontSize:18,color:cityColor,fontWeight:700}}>● {h.result.ville}</span>}
                      <span style={{fontSize:18,fontWeight:700,color:C.text}}>{h.result.titre}</span>
                    </div>
                    <div style={{fontSize:18,color:C.muted}}>{h.result.prix?.toLocaleString('fr')} {'€'} — {h.result.loyer_estime_median?.toLocaleString('fr')} €/mois</div>
                  </div>
                  <div style={{width:42,height:42,borderRadius:'50%',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,
                    border:`2px solid ${h.result.note_globale>=7?C.green:h.result.note_globale>=5?'#d97706':C.red}`,
                    fontSize:18,fontWeight:800,color:h.result.note_globale>=7?C.green:h.result.note_globale>=5?'#d97706':C.red}}>
                    {h.result.note_globale?.toFixed(1)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{textAlign:'center',marginTop:64,fontSize:18,color:C.muted}}>
          buy2rent.io — 2026
        </div>
      </div>
    </>
  );
}
