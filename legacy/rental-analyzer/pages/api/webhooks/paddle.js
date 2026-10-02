// pages/api/webhooks/paddle.js

import { createClient } from '@supabase/supabase-js';
import { Paddle, EventName } from '@paddle/paddle-node-sdk';

const paddle = new Paddle(process.env.PADDLE_API_KEY);

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SECRET_KEY
);

export const config = { api: { bodyParser: false } };

async function getRawBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

const PRICE_PASS_24H = 'pri_01kkkae7wf33f486mpm01afz2w';
const PRICE_PRO      = 'pri_01kkkacrfq1jpkj7kbtqkz9w7y';

async function sendMagicLinkEmail(email, actionLink, isPro) {
  const subject = isPro
    ? '🎉 Bienvenue sur buy2rent Pro !'
    : '✅ Ton Pass 24h buy2rent est activé !';

  const html = `
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"/></head>
    <body style="margin:0;padding:0;background:#f5f0e8;font-family:Arial,sans-serif;">
      <div style="max-width:560px;margin:40px auto;background:#fffdf8;border-radius:24px;overflow:hidden;border:1px solid #e8e0d0;">
        <div style="background:#b45309;padding:32px 40px;text-align:center;">
          <div style="color:#fff;font-size:28px;font-weight:900;">buy2rent.io</div>
          <div style="color:#fde68a;font-size:14px;margin-top:4px;">Analyse immobilière Espagne</div>
        </div>
        <div style="padding:40px;">
          <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#1a1a1a;">
            ${isPro ? 'Bienvenue dans Pro 🚀' : 'Ton accès est prêt ! 🔑'}
          </h1>
          <p style="margin:0 0 24px;font-size:16px;color:#6b6b6b;line-height:1.6;">
            ${isPro
              ? 'Ton abonnement Pro est activé. Accès illimité sur tous tes appareils.'
              : 'Ton Pass 24h est activé. Clique ci-dessous pour lancer tes analyses.'}
          </p>
          <div style="text-align:center;margin:32px 0;">
            <a href="${actionLink}" style="display:inline-block;background:#b45309;color:#fff;font-size:16px;font-weight:700;padding:16px 40px;border-radius:12px;text-decoration:none;">
              ${isPro ? 'Accéder à mon compte Pro' : 'Lancer mes analyses'}
            </a>
          </div>
          <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;text-align:center;line-height:1.6;">
            Ce lien te connecte automatiquement — valable 24h.<br/>
            Questions ? <a href="mailto:support@buy2rent.io" style="color:#b45309;">support@buy2rent.io</a>
          </p>
        </div>
      </div>
    </body>
    </html>
  `;

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'buy2rent <support@buy2rent.io>',
      to: email,
      subject,
      html,
    }),
  });

  const result = await response.json();
  if (!response.ok) console.error('Resend error:', JSON.stringify(result));
  else console.log('Magic link email sent to:', email);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const rawBody = await getRawBody(req);
  const signature = req.headers['paddle-signature'];

  // ── Verify signature via Paddle SDK ──────────────────────
  let event;
  try {
    event = paddle.webhooks.unmarshal(rawBody, process.env.PADDLE_WEBHOOK_SECRET, signature);
  } catch (err) {
    console.error('Paddle signature verification failed:', err.message);
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const eventType = event.eventType;
  const data = event.data;

  const email = data?.customer?.email || data?.customData?.email;
  if (!email) {
    console.error('No email in payload');
    return res.status(400).json({ error: 'No email' });
  }
  const normalizedEmail = email.toLowerCase().trim();
  const priceId = data?.items?.[0]?.price?.id || '';

  console.log(`Webhook: ${eventType} | email: ${normalizedEmail} | priceId: ${priceId}`);

  // ── transaction.completed → Pass 24h ─────────────────────
  if (eventType === EventName.TransactionCompleted && priceId === PRICE_PASS_24H) {
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    const { error } = await supabase.from('users').upsert(
      { email: normalizedEmail, pass_expires_at: expires },
      { onConflict: 'email' }
    );
    if (error) console.error('Supabase upsert error:', error);

    try {
      const { data: linkData, error: linkError } = await supabase.auth.admin.generateLink({
        type: 'magiclink',
        email: normalizedEmail,
        options: { redirectTo: 'https://buy2rent.io/app?payment=success' },
      });
      if (linkError) console.error('generateLink error:', linkError);
      else {
        const actionLink = linkData?.properties?.action_link;
        if (actionLink) await sendMagicLinkEmail(normalizedEmail, actionLink, false);
      }
    } catch (e) {
      console.error('Magic link error:', e.message);
    }

    return res.status(200).json({ ok: true, type: 'pass_24h' });
  }

  // ── subscription.activated / updated → Pro ────────────────
  if ((eventType === EventName.SubscriptionActivated || eventType === EventName.SubscriptionUpdated) && priceId === PRICE_PRO) {
    const isActive = data?.status === 'active';

    await supabase.from('users').upsert({
      email: normalizedEmail,
      is_subscribed: isActive,
      lemon_subscription_id: String(data?.id || ''),
      lemon_customer_id: String(data?.customerId || ''),
    }, { onConflict: 'email' });

    if (isActive) {
      try {
        const { data: linkData, error: linkError } = await supabase.auth.admin.generateLink({
          type: 'magiclink',
          email: normalizedEmail,
          options: { redirectTo: 'https://buy2rent.io/app?payment=success' },
        });
        if (!linkError) {
          const actionLink = linkData?.properties?.action_link;
          if (actionLink) await sendMagicLinkEmail(normalizedEmail, actionLink, true);
        }
      } catch (e) {
        console.error('Magic link Pro error:', e.message);
      }
    }

    return res.status(200).json({ ok: true, type: 'pro', active: isActive });
  }

  // ── subscription.canceled ─────────────────────────────────
  if (eventType === EventName.SubscriptionCanceled) {
    await supabase.from('users')
      .update({ is_subscribed: false })
      .eq('email', normalizedEmail);
    return res.status(200).json({ ok: true, type: 'canceled' });
  }

  return res.status(200).json({ ok: true, ignored: true });
}
