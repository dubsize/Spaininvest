// Mémoria — notification e-mail des formulaires Netlify.
// Netlify appelle cette fonction pour chaque envoi vérifié (le spam est déjà écarté).
// Envoi via Resend depuis le domaine starallianceconsult.com.
// Variable d'environnement requise (secrète, portée Functions) : RESEND_API_KEY.
// Optionnelle : NOTIFY_TO (destinataire, par défaut info@starallianceconsult.com).

// Formulaires notifiés. Ajouter 'rdv', 'rdv-en', 'rdv-he' pour être prévenu aussi des demandes RDV.
const NOTIFIED_FORMS = ['corporate', 'proprietaires'];

const LABELS = {
  corporate: 'Devis entreprise',
  proprietaires: 'Proposition de bien (propriétaire)',
  rdv: 'Demande de RDV (FR)',
  'rdv-en': 'Demande de RDV (EN)',
  'rdv-he': 'Demande de RDV (HE)',
};

// Champs techniques ajoutés par Netlify, inutiles dans l'e-mail.
const SKIP = new Set(['form-name', 'bot-field', 'ip', 'user_agent', 'referrer']);

const escapeHtml = (v) =>
  String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

export default async (req) => {
  const { payload } = await req.json();
  const form = payload?.form_name;
  if (!NOTIFIED_FORMS.includes(form)) return new Response('ignored');

  const apiKey = Netlify.env.get('RESEND_API_KEY');
  if (!apiKey) {
    console.error('RESEND_API_KEY manquante : notification non envoyée pour', form);
    return new Response('missing key', { status: 500 });
  }

  const data = payload.data || {};
  const rows = Object.entries(data)
    .filter(([k, v]) => !SKIP.has(k) && v !== '' && v != null)
    .map(([k, v]) => {
      const value = Array.isArray(v) ? v.join(', ') : v;
      return `<tr><th align="left" style="padding:6px 12px 6px 0;vertical-align:top">${escapeHtml(k)}</th><td style="padding:6px 0">${escapeHtml(value).replace(/\n/g, '<br>')}</td></tr>`;
    })
    .join('');

  const who = data.societe || data.nom || data.name || data.email || 'sans nom';
  const subject = `[Mémoria] ${LABELS[form] || form} — ${who}`;
  const html = `<div style="font-family:Arial,sans-serif;font-size:14px;color:#20241F">
<p><strong>${escapeHtml(LABELS[form] || form)}</strong> reçu sur memoriamadrid.com le ${escapeHtml(payload.created_at || '')}.</p>
<table style="border-collapse:collapse">${rows}</table>
<p style="color:#5A6058;font-size:12px">Répondre à cet e-mail écrit directement à la personne. Toutes les demandes : Netlify → Forms.</p>
</div>`;

  const body = {
    from: 'Mémoria — site <site@starallianceconsult.com>',
    to: [Netlify.env.get('NOTIFY_TO') || 'info@starallianceconsult.com'],
    subject,
    html,
  };
  if (data.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) body.reply_to = data.email;

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    console.error('Resend a refusé la notification', res.status, await res.text());
    return new Response('send failed', { status: 502 });
  }
  return new Response('sent');
};
