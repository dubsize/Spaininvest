import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

// pages/terms.js

const C = {
  bg: '#f5f0e8', card: '#fffdf8', border: '#e8e0d0',
  text: '#1c1917', muted: '#78716c', accent: '#b45309',
};

const CONTENT = {
  en: {
    lang: 'English',
    title: 'Terms of Service',
    updated: 'Last updated: March 11, 2026',
    sections: [
      {
        h: '1. Acceptance of Terms',
        p: 'By accessing and using buy2rent.io ("the Service"), you accept and agree to be bound by these Terms of Service. If you do not agree, please do not use the Service. The Service is operated by Nicolas Salmon, an individual entrepreneur based in Spain.'
      },
      {
        h: '2. Description of Service',
        p: 'buy2rent.io is a property investment analysis tool that provides rental yield estimates and investment scoring for real estate properties in Spain. Analyses are generated using artificial intelligence and publicly available market data. All results are indicative and for informational purposes only.'
      },
      {
        h: '3. No Financial Advice',
        p: 'The information provided by buy2rent.io does not constitute financial, legal, or investment advice. You should consult a qualified professional before making any investment decision. buy2rent.io and its operator accept no liability for any loss or damage resulting from reliance on the information provided.'
      },
      {
        h: '4. Free and Paid Plans',
        p: 'The Service offers a free tier limited to 2 analyses. Additional analyses require a Pass 24h (one-time payment of €9 for unlimited analyses for 24 hours) or a Pro subscription (€19/month for unlimited analyses). Payments are processed by Lemon Squeezy. All prices include applicable taxes.'
      },
      {
        h: '5. Refund Policy',
        p: 'Due to the digital and immediate nature of the service, Pass 24h purchases are non-refundable once the analyses have been used. Pro subscriptions may be cancelled at any time; cancellation takes effect at the end of the current billing period. If you experience a technical issue preventing you from using the service, contact us at support@buy2rent.io within 48 hours for a resolution.'
      },
      {
        h: '6. Acceptable Use',
        p: 'You agree not to: (a) use the Service for any unlawful purpose; (b) attempt to reverse-engineer, scrape, or extract data from the Service at scale; (c) resell or redistribute analyses without written permission; (d) use automated tools to abuse the free tier.'
      },
      {
        h: '7. Intellectual Property',
        p: 'The Service, including its design, algorithms, and content, is the exclusive property of Nicolas Salmon. The buy2rent.io brand and logo are proprietary. You may not reproduce or use them without prior written consent.'
      },
      {
        h: '8. Limitation of Liability',
        p: 'To the maximum extent permitted by applicable law, buy2rent.io shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or indirectly.'
      },
      {
        h: '9. Governing Law',
        p: 'These Terms are governed by Spanish law. Any disputes shall be subject to the exclusive jurisdiction of the courts of Spain.'
      },
      {
        h: '10. Contact',
        p: 'For any questions regarding these Terms, contact: support@buy2rent.io'
      },
    ]
  },
  es: {
    lang: 'Español',
    title: 'Términos de Servicio',
    updated: 'Última actualización: 11 de marzo de 2026',
    sections: [
      {
        h: '1. Aceptación de los Términos',
        p: 'Al acceder y utilizar buy2rent.io ("el Servicio"), aceptas quedar vinculado por estos Términos de Servicio. Si no estás de acuerdo, por favor no utilices el Servicio. El Servicio es operado por Nicolas Salmon, empresario individual con base en España.'
      },
      {
        h: '2. Descripción del Servicio',
        p: 'buy2rent.io es una herramienta de análisis de inversión inmobiliaria que proporciona estimaciones de rentabilidad por alquiler y puntuaciones de inversión para propiedades inmobiliarias en España. Los análisis se generan utilizando inteligencia artificial y datos de mercado disponibles públicamente. Todos los resultados son orientativos y tienen carácter meramente informativo.'
      },
      {
        h: '3. Sin Asesoramiento Financiero',
        p: 'La información proporcionada por buy2rent.io no constituye asesoramiento financiero, legal ni de inversión. Debes consultar a un profesional cualificado antes de tomar cualquier decisión de inversión. buy2rent.io y su operador no aceptan ninguna responsabilidad por pérdidas o daños derivados de la confianza en la información proporcionada.'
      },
      {
        h: '4. Planes Gratuitos y de Pago',
        p: 'El Servicio ofrece un nivel gratuito limitado a 2 análisis. Los análisis adicionales requieren un Pass 24h (pago único de 9€ por análisis ilimitados durante 24 horas) o una suscripción Pro (19€/mes por análisis ilimitados). Los pagos son procesados por Lemon Squeezy. Todos los precios incluyen los impuestos aplicables.'
      },
      {
        h: '5. Política de Reembolso',
        p: 'Debido a la naturaleza digital e inmediata del servicio, las compras del Pass 24h no son reembolsables una vez utilizados los análisis. Las suscripciones Pro pueden cancelarse en cualquier momento; la cancelación tiene efecto al final del período de facturación en curso. Si experimentas un problema técnico que te impide usar el servicio, contacta con nosotros en support@buy2rent.io en un plazo de 48 horas.'
      },
      {
        h: '6. Uso Aceptable',
        p: 'Aceptas no: (a) utilizar el Servicio para ningún fin ilegal; (b) intentar realizar ingeniería inversa, scraping o extracción masiva de datos del Servicio; (c) revender o redistribuir análisis sin permiso escrito; (d) utilizar herramientas automatizadas para abusar del nivel gratuito.'
      },
      {
        h: '7. Propiedad Intelectual',
        p: 'El Servicio, incluyendo su diseño, algoritmos y contenido, es propiedad exclusiva de Nicolas Salmon. La marca buy2rent.io y su logotipo son propietarios. No puedes reproducirlos ni utilizarlos sin consentimiento previo por escrito.'
      },
      {
        h: '8. Limitación de Responsabilidad',
        p: 'En la máxima medida permitida por la ley aplicable, buy2rent.io no será responsable de ningún daño indirecto, incidental, especial, consecuente o punitivo, ni de pérdida de beneficios o ingresos.'
      },
      {
        h: '9. Ley Aplicable',
        p: 'Estos Términos se rigen por la legislación española. Cualquier disputa estará sujeta a la jurisdicción exclusiva de los tribunales de España.'
      },
      {
        h: '10. Contacto',
        p: 'Para cualquier pregunta sobre estos Términos: support@buy2rent.io'
      },
    ]
  },
  fr: {
    lang: 'Français',
    title: "Conditions Générales d'Utilisation",
    updated: 'Dernière mise à jour : 11 mars 2026',
    sections: [
      {
        h: '1. Acceptation des CGU',
        p: 'En accédant et en utilisant buy2rent.io (« le Service »), vous acceptez d\'être lié par les présentes Conditions Générales d\'Utilisation. Si vous n\'acceptez pas ces conditions, veuillez ne pas utiliser le Service. Le Service est opéré par Nicolas Salmon, entrepreneur individuel basé en Espagne.'
      },
      {
        h: '2. Description du Service',
        p: 'buy2rent.io est un outil d\'analyse d\'investissement immobilier qui fournit des estimations de rendement locatif et des scores d\'investissement pour des biens immobiliers en Espagne. Les analyses sont générées par intelligence artificielle et des données de marché publiquement disponibles. Tous les résultats sont indicatifs et fournis à titre informatif uniquement.'
      },
      {
        h: '3. Absence de Conseil Financier',
        p: 'Les informations fournies par buy2rent.io ne constituent pas un conseil financier, juridique ou en investissement. Vous devez consulter un professionnel qualifié avant de prendre toute décision d\'investissement. buy2rent.io et son opérateur déclinent toute responsabilité pour toute perte ou dommage résultant de l\'utilisation des informations fournies.'
      },
      {
        h: '4. Offres Gratuites et Payantes',
        p: 'Le Service propose un accès gratuit limité à 2 analyses. Les analyses supplémentaires nécessitent un Pass 24h (paiement unique de 9€ pour des analyses illimitées pendant 24h) ou un abonnement Pro (19€/mois pour des analyses illimitées). Les paiements sont traités par Lemon Squeezy. Tous les prix sont TTC.'
      },
      {
        h: '5. Politique de Remboursement',
        p: 'En raison de la nature numérique et immédiate du service, les achats de Pass 24h ne sont pas remboursables une fois les analyses utilisées. Les abonnements Pro peuvent être résiliés à tout moment ; la résiliation prend effet à la fin de la période de facturation en cours. En cas de problème technique vous empêchant d\'utiliser le service, contactez-nous à support@buy2rent.io dans les 48 heures.'
      },
      {
        h: '6. Utilisation Acceptable',
        p: 'Vous vous engagez à ne pas : (a) utiliser le Service à des fins illégales ; (b) tenter de procéder à de la rétro-ingénierie, du scraping ou de l\'extraction massive de données ; (c) revendre ou redistribuer des analyses sans autorisation écrite ; (d) utiliser des outils automatisés pour abuser du niveau gratuit.'
      },
      {
        h: '7. Propriété Intellectuelle',
        p: 'Le Service, notamment son design, ses algorithmes et son contenu, est la propriété exclusive de Nicolas Salmon. La marque buy2rent.io et son logo sont protégés. Vous ne pouvez pas les reproduire ou les utiliser sans consentement écrit préalable.'
      },
      {
        h: '8. Limitation de Responsabilité',
        p: 'Dans la limite maximale autorisée par la loi applicable, buy2rent.io ne pourra être tenu responsable de dommages indirects, accessoires, spéciaux, consécutifs ou punitifs, ni de pertes de bénéfices ou de revenus.'
      },
      {
        h: '9. Droit Applicable',
        p: 'Les présentes CGU sont régies par le droit espagnol. Tout litige sera soumis à la juridiction exclusive des tribunaux espagnols.'
      },
      {
        h: '10. Contact',
        p: 'Pour toute question concernant ces CGU : support@buy2rent.io'
      },
    ]
  }
};

export default function Terms() {
  const [lang, setLang] = useState('fr');
  const c = CONTENT[lang];

  return (
    <>
      <Head>
        <title>Terms of Service — buy2rent.io</title>
        <meta name="robots" content="noindex"/>
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
      </Head>
      <div style={{minHeight:'100vh',background:C.bg,fontFamily:"'DM Sans', sans-serif",color:C.text}}>
        {/* Header */}
        <div style={{borderBottom:`1px solid ${C.border}`,background:C.card,padding:'16px 24px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <Link href="/" style={{textDecoration:'none'}}>
            <span style={{fontFamily:'Georgia,serif',fontSize:20,fontWeight:800,color:C.text}}>
              buy2rent<span style={{color:C.accent}}>.io</span>
            </span>
          </Link>
          {/* Lang switcher */}
          <div style={{display:'flex',gap:8}}>
            {['en','es','fr'].map(l => (
              <button key={l} onClick={()=>setLang(l)} style={{
                padding:'6px 14px',borderRadius:8,border:`1px solid ${lang===l?C.accent:C.border}`,
                background:lang===l?C.accent:'transparent',color:lang===l?'#fff':C.muted,
                fontSize:13,fontWeight:600,cursor:'pointer',transition:'all 0.2s'
              }}>{l.toUpperCase()}</button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div style={{maxWidth:740,margin:'0 auto',padding:'48px 24px 80px'}}>
          <h1 style={{fontSize:32,fontWeight:800,marginBottom:8}}>{c.title}</h1>
          <p style={{fontSize:14,color:C.muted,marginBottom:48}}>{c.updated}</p>

          {c.sections.map((s, i) => (
            <div key={i} style={{marginBottom:32}}>
              <h2 style={{fontSize:18,fontWeight:700,marginBottom:10,color:C.text}}>{s.h}</h2>
              <p style={{fontSize:15,lineHeight:1.8,color:'#44403c'}}>{s.p}</p>
            </div>
          ))}

          <div style={{marginTop:48,paddingTop:24,borderTop:`1px solid ${C.border}`,display:'flex',gap:24,fontSize:14,color:C.muted}}>
            <Link href="/privacy" style={{color:C.accent,textDecoration:'none'}}>Privacy Policy</Link>
            <Link href="/" style={{color:C.muted,textDecoration:'none'}}>← Back to buy2rent.io</Link>
          </div>
        </div>
      </div>
    </>
  );
}
