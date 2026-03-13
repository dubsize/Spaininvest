// pages/api/webhooks/paddle.js — Paddle webhook + Resend magic link

import crypto from 'crypto';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SECRET_KEY
);

export const config = { api: { bodyParser: false } };

async function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
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
    <body style="margin:0;padding:0;background:#f5f0e8;font-family:'DM Sans',Arial,sans-serif;">
      <div style="max-width:560px;margin:40px auto;background:#fffdf8;border-radius:24px;overflow:hidden;border:1px solid #e8e0d0;">
        <div style="background:#b45309;padding:32px 40px;text-align:center;">
          <div style="color:#fff;font-size:28px;font-weight:900;letter-spacing:-0.5px;">buy2rent.io</div>
          <div style="color:#fde68a;font-size:14px;margin-top:4px;">Analyse immobilière Espagne</div>
        </div>
        <div style="padding:40px;">
          <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#1a1a1a;">
            ${isPro ? 'Bienvenue dans Pro 🚀' : 'Ton accès est prêt ! 🔑'}
          </h1>
          <p style="margin:0 0 24px;font-size:16px;color:#6b6b6b;line-height:1.6;">
            ${isPro
              ? 'Ton abonnement Pro est activé. Tu as maintenant accès à des analyses illimitées sur tous tes appareils.'
              : 'Ton Pass 24h est activé. Clique sur le bouton ci-dessous pour accéder immédiatement à tes analyses illimitées.'}
          </p>
          <div style="text-align:center;margin:32px 0;">
            <a href="${actionLink}" style="display:inline-block;background:#b45309;color:#fff;font-size:16px;font-weight:700;padding:16px 40px;border-radius:12px;text-decoration:none;">
              ${isPro ? 'Accéder à mon compte Pro' : 'Lancer mes analyses'}
            </a>
          </div>
          <p style="margin:24px 0 0;font-size:13px;color:#9ca3af;text-align:center;line-height:1.6;">
            Ce lien est valable 24h et te connecte automatiquement.<br/>
            Si tu n'es pas à l'origine de cet achat, contacte-nous : <a href="mailto:support@buy2rent.io" style="color:#b45309;">support@buy2rent.io</a>
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
  if (!response.ok) console.error('Resend error:', result);
  else console.log('Email sent to:', email);
  return result;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const rawBody = await getRawBody(req);

  // ── Verify Paddle signature ───────────────────────────────
  const signature = req.headers['paddle-signature'];
  const webhookSecret = process.env.PADDLE_WEBHOOK_SECRET;

  if (signature && webhookSecret) {
    const parts = Object.fromEntries(signature.split(';').map(p => p.split('=')));
    const ts = parts['ts'];
    const h1 = parts['h1'];
    const signed = `${ts}:${rawBody.toString()}`;
    const expected = crypto.createHmac('sha256', webhookSecret).update(signed).digest('hex');
    if (expected !== h1) {
      console.error('Invalid Paddle signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  const payload = JSON.parse(rawBody.toString());
  const eventType = payload.event_type;
  const data = payload.data;

  const email = data?.customer?.email || data?.custom_data?.email;
  if (!email) return res.status(400).json({ error: 'No email in payload' });
  const normalizedEmail = email.toLowerCase().trim();

  const priceId = data?.items?.[0]?.price?.id || data?.items?.[0]?.price_id || '';

  // ── transaction.completed → Pass 24h ─────────────────────
  if (eventType === 'transaction.completed' && priceId === PRICE_PASS_24H) {
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

    // Upsert user in Supabase
    await supabase.from('users').upsert(
      { email: normalizedEmail, pass_expires_at: expires },
      { onConflict: 'email' }
    );

    // Create/get Supabase auth user and generate magic link
    try {
      const { data: linkData, error: linkError } = await supabase.auth.admin.generateLink({
        type: 'magiclink',
        email: normalizedEmail,
        options: { redirectTo: 'https://buy2rent.io/app?payment=success' },
      });

      if (linkError) {
        console.error('generateLink error:', linkError);
      } else {
        const actionLink = linkData?.properties?.action_link;
        if (actionLink) await sendMagicLinkEmail(normalizedEmail, actionLink, false);
      }
    } catch (e) {
      console.error('Magic link error:', e.message);
    }

    return res.status(200).json({ ok: true, type: 'pass_24h' });
  }

  // ── subscription.activated / updated → Pro ────────────────
  if ((eventType === 'subscription.activated' || eventType === 'subscription.updated') && priceId === PRICE_PRO) {
    const isActive = data?.status === 'active';
    const paddleSubId = String(data?.id || '');
    const paddleCustomerId = String(data?.customer_id || '');

    await supabase.from('users').upsert({
      email: normalizedEmail,
      is_subscribed: isActive,
      lemon_subscription_id: paddleSubId,
      lemon_customer_id: paddleCustomerId,
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
  if (eventType === 'subscription.canceled') {
    await supabase.from('users')
      .update({ is_subscribed: false })
      .eq('email', normalizedEmail);
    return res.status(200).json({ ok: true, type: 'canceled' });
  }

  return res.status(200).json({ ok: true, ignored: true });
}
