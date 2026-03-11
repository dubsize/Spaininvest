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

const VARIANT_PASS_24H   = '1390809';
const VARIANT_PRO        = '1390815';
const WEBHOOK_SECRET     = process.env.LEMONSQUEEZY_WEBHOOK_SECRET;

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const rawBody = await getRawBody(req);
  const signature = req.headers['x-signature'];

  // ── Verify webhook signature ───────────────────────────
  const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
  hmac.update(rawBody);
  const digest = hmac.digest('hex');

  if (signature !== digest) {
    console.error('Invalid webhook signature');
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const payload = JSON.parse(rawBody.toString());
  const eventName = payload.meta?.event_name;
  const data = payload.data?.attributes;
  const variantId = String(data?.first_order_item?.variant_id || data?.variant_id || '');
  const email = data?.user_email || payload.meta?.custom_data?.email;

  if (!email) return res.status(400).json({ error: 'No email in payload' });

  const normalizedEmail = email.toLowerCase().trim();

  // ── order_created → Pass 24h ───────────────────────────
  if (eventName === 'order_created' && variantId === VARIANT_PASS_24H) {
    const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    const { error } = await supabase
      .from('users')
      .update({ pass_expires_at: expires })
      .eq('email', normalizedEmail);

    if (error) console.error('Supabase Pass 24h update error:', error);
    return res.status(200).json({ ok: true, type: 'pass_24h' });
  }

  // ── subscription_created / subscription_updated → Pro ──
  if ((eventName === 'subscription_created' || eventName === 'subscription_updated') && variantId === VARIANT_PRO) {
    const isActive = data?.status === 'active';
    const lemonSubId = String(payload.data?.id || '');
    const lemonCustomerId = String(data?.customer_id || '');

    const { error } = await supabase
      .from('users')
      .update({
        is_subscribed: isActive,
        lemon_subscription_id: lemonSubId,
        lemon_customer_id: lemonCustomerId,
      })
      .eq('email', normalizedEmail);

    if (error) console.error('Supabase Pro update error:', error);
    return res.status(200).json({ ok: true, type: 'pro', active: isActive });
  }

  return res.status(200).json({ ok: true, ignored: true });
}
