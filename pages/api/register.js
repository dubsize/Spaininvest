const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SECRET_KEY
);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { email } = req.body;
  if (!email || !email.includes('@')) return res.status(400).json({ error: 'Invalid email' });

  const normalizedEmail = email.toLowerCase().trim();

  // Upsert user (create if not exists)
  const { data, error } = await supabase
    .from('users')
    .upsert({ email: normalizedEmail }, { onConflict: 'email', ignoreDuplicates: false })
    .select()
    .single();

  if (error) return res.status(500).json({ error: error.message });

  return res.status(200).json({
    email: data.email,
    analyses_count: data.analyses_count,
    is_subscribed: data.is_subscribed,
    can_analyze: data.is_subscribed || data.analyses_count < 2,
  });
}
