// pages/api/auth/callback.js
// Handles Supabase magic link + OAuth redirects
export default function handler(req, res) {
  // Supabase handles the token exchange client-side via the JS client
  // Just redirect to /app — the Supabase client will pick up the session from the URL hash
  res.redirect(302, '/app');
}
