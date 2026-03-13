// pages/api/create-checkout.js — Paddle, returns txnId for client-side overlay

const PADDLE_API_KEY = process.env.PADDLE_API_KEY;

const PRICE_IDS = {
  pass_24h: 'pri_01kkkae7wf33f486mpm01afz2w',
  pro:      'pri_01kkkacrfq1jpkj7kbtqkz9w7y',
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { priceId, email } = req.body;
  if (!priceId || !email) return res.status(400).json({ error: 'Missing priceId or email' });

  const paddlePriceId = PRICE_IDS[priceId] || priceId;

  try {
    const response = await fetch('https://api.paddle.com/transactions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${PADDLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        items: [{ price_id: paddlePriceId, quantity: 1 }],
        customer: { email },
        custom_data: { email },
      }),
    });

    const data = await response.json();
    if (!response.ok) return res.status(500).json({ error: 'Paddle error', detail: data });

    const txnId = data?.data?.id;
    if (!txnId) return res.status(500).json({ error: 'No transaction ID', detail: data });

    return res.status(200).json({ txnId });

  } catch (err) {
    return res.status(500).json({ error: 'Checkout failed', detail: err.message });
  }
}
