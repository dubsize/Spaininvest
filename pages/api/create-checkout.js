export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { variantId, email } = req.body;
  if (!variantId || !email) return res.status(400).json({ error: 'Missing variantId or email' });

  const LS_API_KEY = process.env.LEMONSQUEEZY_API_KEY;
  const STORE_ID = process.env.LEMONSQUEEZY_STORE_ID;

  try {
    const response = await fetch('https://api.lemonsqueezy.com/v1/checkouts', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LS_API_KEY}`,
        'Content-Type': 'application/vnd.api+json',
        'Accept': 'application/vnd.api+json',
      },
      body: JSON.stringify({
        data: {
          type: 'checkouts',
          attributes: {
            checkout_data: {
              email,
              custom: { email },
            },
            product_options: {
              redirect_url: 'https://buy2rent.io/?payment=success',
            },
          },
          relationships: {
            store: { data: { type: 'stores', id: String(STORE_ID) } },
            variant: { data: { type: 'variants', id: String(variantId) } },
          },
        },
      }),
    });

    const data = await response.json();
    if (!response.ok) return res.status(500).json({ error: 'LS checkout error', detail: data });

    const checkoutUrl = data?.data?.attributes?.url;
    return res.status(200).json({ url: checkoutUrl });
  } catch (err) {
    return res.status(500).json({ error: 'Checkout failed', detail: err.message });
  }
}
