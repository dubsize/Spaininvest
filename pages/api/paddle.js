// pages/api/webhooks/paddle.js — Paddle webhook handler

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

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const rawBody = await getRawBody(req);

  // ── Verify Paddle webhook signature ───────────────────────
  const signature = req.headers['paddle-signature'];
  const webhookSecret = process.env.PADDLE_WEBHOOK_SECRET;

  if (signature && webhookSecret) {
    // Paddle signature format: ts=timestamp;h1=hash
    const parts = Object.fromEntries(signature.split(';').map(p => p.split('=')));
    const ts = parts['ts'];
    const h1 = parts['h1'];
    const signed = `${ts}:${rawBody.toString()}`;
    const expected = crypto.createHmac('sha256', webhookSecret).update(signed).digest('hex');
    if (expected !== h1) {
      console.error('Invalid Paddle webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  const payload = JSON.parse(rawBody.toString());
  const eventType = payload.event_type;
  const data = payload.data;

  // Extract email from customer or custom_data
  const email = data?.customer?.email || data?.custom_data?.email;
  if (!email) return res.status(400).json({ error: 'No email in payload' });
  const normalizedEmail = email.toLowerCase().trim();

  // Extract price ID from items
  const priceId = data?.items?.[0]?.price?.id || data?.items?.[0]?.price_id || '';

  // ── transaction.completed → Pass 24h ──────────────────────
  if (eventType === 'transaction.completed' && priceId === PRICE_PASS_24H) {
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    const { error } = await supabase
      .from('users')
      .upsert({ email: normalizedEmail, pass_expires_at: expires }, { onConflict: 'email' });

    if (error) console.error('Supabase Pass 24h error:', error);
    return res.status(200).json({ ok: true, type: 'pass_24h' });
  }

  // ── subscription.activated / subscription.updated → Pro ───
  if ((eventType === 'subscription.activated' || eventType === 'subscription.updated') && priceId === PRICE_PRO) {
    const isActive = data?.status === 'active';
    const paddleSubId = String(data?.id || '');
    const paddleCustomerId = String(data?.customer_id || '');

    const { error } = await supabase
      .from('users')
      .upsert({
        email: normalizedEmail,
        is_subscribed: isActive,
        lemon_subscription_id: paddleSubId,   // reusing existing column
        lemon_customer_id: paddleCustomerId,   // reusing existing column
      }, { onConflict: 'email' });

    if (error) console.error('Supabase Pro error:', error);
    return res.status(200).json({ ok: true, type: 'pro', active: isActive });
  }

  // ── subscription.canceled ──────────────────────────────────
  if (eventType === 'subscription.canceled' && priceId === PRICE_PRO) {
    const { error } = await supabase
      .from('users')
      .update({ is_subscribed: false })
      .eq('email', normalizedEmail);

    if (error) console.error('Supabase cancel error:', error);
    return res.status(200).json({ ok: true, type: 'canceled' });
  }

  return res.status(200).json({ ok: true, ignored: true });
}
