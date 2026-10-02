import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

// pages/privacy.js

const C = {
  bg: '#f5f0e8', card: '#fffdf8', border: '#e8e0d0',
  text: '#1c1917', muted: '#78716c', accent: '#b45309',
};

const CONTENT = {
  en: {
    lang: 'English',
    title: 'Privacy Policy',
    updated: 'Last updated: March 11, 2026',
    intro: 'buy2rent.io is committed to protecting your personal data in accordance with the General Data Protection Regulation (GDPR) and Spanish data protection law (LOPDGDD). This policy explains what data we collect, why, and how we protect it.',
    sections: [
      {
        h: '1. Data Controller',
        p: 'The data controller is Nicolas Salmon, operating buy2rent.io, based in Spain. Contact: support@buy2rent.io'
      },
      {
        h: '2. Data We Collect',
        p: 'We collect: (a) Email address — when you create an account or purchase a plan, for authentication and sending receipts. (b) IP address — to prevent abuse of the free tier, stored anonymously. (c) Anonymous usage identifier — a random ID stored in your browser (localStorage) to track your free analysis quota. (d) Payment data — processed exclusively by Lemon Squeezy; we never store your card details. (e) Google account data (name and email) — only if you choose to sign in with Google.'
      },
      {
        h: '3. Legal Basis for Processing',
        p: 'We process your data on the following legal bases: (a) Performance of a contract — to provide you with the Service you have subscribed to. (b) Legitimate interest — to prevent abuse of the free tier via IP and anonymous tracking. (c) Consent — for marketing communications, if applicable.'
      },
      {
        h: '4. How We Use Your Data',
        p: 'Your data is used solely to: provide and improve the Service; manage your account and subscription; send transactional emails (receipts, magic links); prevent fraud and abuse. We do not sell your personal data to third parties. We do not use your data for advertising profiling.'
      },
      {
        h: '5. Data Retention',
        p: 'Email addresses and account data are retained for as long as your account is active. Anonymous usage identifiers (localStorage) expire when you clear your browser data. IP usage records are retained for a maximum of 90 days. Payment records are retained as required by Spanish tax law (5 years).'
      },
      {
        h: '6. Third-Party Services',
        p: 'We use the following third-party processors: Supabase (database hosting, EU region) — supabase.com; Lemon Squeezy (payment processing) — lemonsqueezy.com; Anthropic (AI analysis engine) — anthropic.com; Vercel (website hosting, EU region) — vercel.com; Google (OAuth authentication) — google.com. Each processor has its own privacy policy and GDPR compliance.'
      },
      {
        h: '7. Cookies and Local Storage',
        p: 'We use localStorage (not cookies) to store your anonymous usage identifier. We use Google Tag Manager for analytics. No advertising cookies are set. You can clear your localStorage at any time via your browser settings.'
      },
      {
        h: '8. Your Rights (GDPR)',
        p: 'Under GDPR, you have the right to: access your personal data; rectify inaccurate data; erase your data ("right to be forgotten"); restrict or object to processing; data portability. To exercise any of these rights, contact support@buy2rent.io. You also have the right to lodge a complaint with the Spanish data protection authority (AEPD) at aepd.es.'
      },
      {
        h: '9. Data Security',
        p: 'We implement appropriate technical and organizational measures to protect your data, including encrypted connections (HTTPS), access controls, and regular security reviews. However, no method of transmission over the Internet is 100% secure.'
      },
      {
        h: '10. Contact',
        p: 'For any privacy-related questions or to exercise your rights: support@buy2rent.io'
      },
    ]
  },
  es: {
    lang: 'Español',
    title: 'Política de Privacidad',
    updated: 'Última actualización: 11 de marzo de 2026',
    intro: 'buy2rent.io se compromete a proteger tus datos personales de conformidad con el Reglamento General de Protección de Datos (RGPD) y la Ley Orgánica de Protección de Datos y Garantía de los Derechos Digitales (LOPDGDD). Esta política explica qué datos recopilamos, por qué y cómo los protegemos.',
    sections: [
      {
        h: '1. Responsable del Tratamiento',
        p: 'El responsable del tratamiento es Nicolas Salmon, operador de buy2rent.io, con sede en España. Contacto: support@buy2rent.io'
      },
      {
        h: '2. Datos que Recopilamos',
        p: 'Recopilamos: (a) Dirección de correo electrónico — cuando creas una cuenta o adquieres un plan, para autenticación y envío de recibos. (b) Dirección IP — para prevenir el abuso del nivel gratuito, almacenada de forma anónima. (c) Identificador de uso anónimo — un ID aleatorio almacenado en tu navegador (localStorage) para rastrear tu cuota de análisis gratuitos. (d) Datos de pago — procesados exclusivamente por Lemon Squeezy; nunca almacenamos los datos de tu tarjeta. (e) Datos de cuenta Google (nombre y email) — solo si eliges iniciar sesión con Google.'
      },
      {
        h: '3. Base Legal del Tratamiento',
        p: 'Tratamos tus datos sobre las siguientes bases legales: (a) Ejecución de un contrato — para proporcionarte el Servicio al que te has suscrito. (b) Interés legítimo — para prevenir el abuso del nivel gratuito mediante seguimiento de IP e identificadores anónimos. (c) Consentimiento — para comunicaciones de marketing, si procede.'
      },
      {
        h: '4. Uso de tus Datos',
        p: 'Tus datos se utilizan únicamente para: proporcionar y mejorar el Servicio; gestionar tu cuenta y suscripción; enviar correos transaccionales (recibos, magic links); prevenir fraudes y abusos. No vendemos tus datos personales a terceros. No utilizamos tus datos para perfilado publicitario.'
      },
      {
        h: '5. Conservación de Datos',
        p: 'Las direcciones de correo electrónico y los datos de cuenta se conservan mientras tu cuenta esté activa. Los identificadores de uso anónimos (localStorage) expiran cuando borras los datos de tu navegador. Los registros de uso por IP se conservan un máximo de 90 días. Los registros de pago se conservan según lo exigido por la legislación fiscal española (5 años).'
      },
      {
        h: '6. Servicios de Terceros',
        p: 'Utilizamos los siguientes procesadores de datos: Supabase (base de datos, región UE) — supabase.com; Lemon Squeezy (procesamiento de pagos) — lemonsqueezy.com; Anthropic (motor de análisis IA) — anthropic.com; Vercel (alojamiento web, región UE) — vercel.com; Google (autenticación OAuth) — google.com. Cada procesador tiene su propia política de privacidad y cumplimiento del RGPD.'
      },
      {
        h: '7. Cookies y Almacenamiento Local',
        p: 'Utilizamos localStorage (no cookies) para almacenar tu identificador de uso anónimo. Usamos Google Tag Manager para análisis. No se establecen cookies publicitarias. Puedes borrar tu localStorage en cualquier momento desde la configuración de tu navegador.'
      },
      {
        h: '8. Tus Derechos (RGPD)',
        p: 'En virtud del RGPD, tienes derecho a: acceder a tus datos personales; rectificar datos inexactos; suprimir tus datos ("derecho al olvido"); limitar u oponerte al tratamiento; portabilidad de los datos. Para ejercer cualquiera de estos derechos, contacta con support@buy2rent.io. También tienes derecho a presentar una reclamación ante la Agencia Española de Protección de Datos (AEPD) en aepd.es.'
      },
      {
        h: '9. Seguridad de los Datos',
        p: 'Implementamos medidas técnicas y organizativas apropiadas para proteger tus datos, incluyendo conexiones cifradas (HTTPS), controles de acceso y revisiones de seguridad periódicas. No obstante, ningún método de transmisión por Internet es 100% seguro.'
      },
      {
        h: '10. Contacto',
        p: 'Para cualquier consulta relacionada con la privacidad o para ejercer tus derechos: support@buy2rent.io'
      },
    ]
  },
  fr: {
    lang: 'Français',
    title: 'Politique de Confidentialité',
    updated: 'Dernière mise à jour : 11 mars 2026',
    intro: 'buy2rent.io s\'engage à protéger vos données personnelles conformément au Règlement Général sur la Protection des Données (RGPD) et à la loi espagnole de protection des données (LOPDGDD). Cette politique explique quelles données nous collectons, pourquoi, et comment nous les protégeons.',
    sections: [
      {
        h: '1. Responsable du Traitement',
        p: 'Le responsable du traitement est Nicolas Salmon, opérateur de buy2rent.io, basé en Espagne. Contact : support@buy2rent.io'
      },
      {
        h: '2. Données Collectées',
        p: 'Nous collectons : (a) Adresse e-mail — lors de la création d\'un compte ou d\'un achat, pour l\'authentification et l\'envoi de reçus. (b) Adresse IP — pour prévenir les abus du niveau gratuit, stockée anonymement. (c) Identifiant d\'usage anonyme — un ID aléatoire stocké dans votre navigateur (localStorage) pour suivre votre quota d\'analyses gratuites. (d) Données de paiement — traitées exclusivement par Lemon Squeezy ; nous ne stockons jamais vos coordonnées bancaires. (e) Données de compte Google (nom et email) — uniquement si vous choisissez de vous connecter avec Google.'
      },
      {
        h: '3. Base Légale du Traitement',
        p: 'Nous traitons vos données sur les bases légales suivantes : (a) Exécution d\'un contrat — pour vous fournir le Service auquel vous avez souscrit. (b) Intérêt légitime — pour prévenir les abus du niveau gratuit via le suivi IP et les identifiants anonymes. (c) Consentement — pour les communications marketing, le cas échéant.'
      },
      {
        h: '4. Utilisation de vos Données',
        p: 'Vos données sont utilisées uniquement pour : fournir et améliorer le Service ; gérer votre compte et abonnement ; envoyer des e-mails transactionnels (reçus, liens magiques) ; prévenir les fraudes et abus. Nous ne vendons pas vos données personnelles à des tiers. Nous n\'utilisons pas vos données pour le profilage publicitaire.'
      },
      {
        h: '5. Conservation des Données',
        p: 'Les adresses e-mail et données de compte sont conservées tant que votre compte est actif. Les identifiants d\'usage anonymes (localStorage) expirent lorsque vous effacez les données de votre navigateur. Les enregistrements d\'usage par IP sont conservés 90 jours maximum. Les enregistrements de paiement sont conservés conformément à la législation fiscale espagnole (5 ans).'
      },
      {
        h: '6. Services Tiers',
        p: 'Nous utilisons les sous-traitants suivants : Supabase (hébergement base de données, région UE) — supabase.com ; Lemon Squeezy (traitement des paiements) — lemonsqueezy.com ; Anthropic (moteur d\'analyse IA) — anthropic.com ; Vercel (hébergement web, région UE) — vercel.com ; Google (authentification OAuth) — google.com. Chaque sous-traitant dispose de sa propre politique de confidentialité et conformité RGPD.'
      },
      {
        h: '7. Cookies et Stockage Local',
        p: 'Nous utilisons localStorage (pas de cookies) pour stocker votre identifiant d\'usage anonyme. Nous utilisons Google Tag Manager pour l\'analyse. Aucun cookie publicitaire n\'est déposé. Vous pouvez effacer votre localStorage à tout moment via les paramètres de votre navigateur.'
      },
      {
        h: '8. Vos Droits (RGPD)',
        p: 'En vertu du RGPD, vous avez le droit de : accéder à vos données personnelles ; rectifier des données inexactes ; effacer vos données (« droit à l\'oubli ») ; limiter ou vous opposer au traitement ; portabilité des données. Pour exercer ces droits, contactez support@buy2rent.io. Vous avez également le droit d\'introduire une réclamation auprès de l\'autorité espagnole de protection des données (AEPD) sur aepd.es.'
      },
      {
        h: '9. Sécurité des Données',
        p: 'Nous mettons en œuvre des mesures techniques et organisationnelles appropriées pour protéger vos données, notamment des connexions chiffrées (HTTPS), des contrôles d\'accès et des revues de sécurité régulières. Cependant, aucune méthode de transmission sur Internet n\'est sécurisée à 100%.'
      },
      {
        h: '10. Contact',
        p: 'Pour toute question relative à la confidentialité ou pour exercer vos droits : support@buy2rent.io'
      },
    ]
  }
};

export default function Privacy() {
  const [lang, setLang] = useState('fr');
  const c = CONTENT[lang];

  return (
    <>
      <Head>
        <title>Privacy Policy — buy2rent.io</title>
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
          <p style={{fontSize:14,color:C.muted,marginBottom:16}}>{c.updated}</p>
          <p style={{fontSize:15,lineHeight:1.8,color:'#44403c',marginBottom:48,padding:'16px 20px',background:C.card,borderRadius:12,border:`1px solid ${C.border}`}}>{c.intro}</p>

          {c.sections.map((s, i) => (
            <div key={i} style={{marginBottom:32}}>
              <h2 style={{fontSize:18,fontWeight:700,marginBottom:10,color:C.text}}>{s.h}</h2>
              <p style={{fontSize:15,lineHeight:1.8,color:'#44403c'}}>{s.p}</p>
            </div>
          ))}

          <div style={{marginTop:48,paddingTop:24,borderTop:`1px solid ${C.border}`,display:'flex',gap:24,fontSize:14,color:C.muted}}>
            <Link href="/terms" style={{color:C.accent,textDecoration:'none'}}>Terms of Service</Link>
            <Link href="/" style={{color:C.muted,textDecoration:'none'}}>← Back to buy2rent.io</Link>
          </div>
        </div>
      </div>
    </>
  );
}
