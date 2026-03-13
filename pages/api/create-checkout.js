// pages/api/create-checkout.js — Paddle integration

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
        checkout: {
          success_url: 'https://buy2rent.io/app?payment=success',
        },
        custom_data: { email },
      }),
    });

    const data = await response.json();
    console.log('Paddle response status:', response.status);
    console.log('Paddle response body:', JSON.stringify(data));
    if (!response.ok) return res.status(500).json({ error: 'Paddle checkout error', detail: data });

    const checkoutUrl = data?.data?.checkout?.url;
    if (!checkoutUrl) return res.status(500).json({ error: 'No checkout URL returned', detail: data });

    return res.status(200).json({ url: checkoutUrl });
  } catch (err) {
    return res.status(500).json({ error: 'Checkout failed', detail: err.message });
  }
}
