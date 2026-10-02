# Spain Invest 🏠🇪🇸

AI-powered rental investment analyzer for Spain.
Covers Madrid, Barcelona, Valencia and Málaga — EN / FR / ES.

---

## 🚀 Deploy on Vercel (15 min, free)

1. Upload this folder to a GitHub repo named `spaininvest`
2. Go to vercel.com → "Add New Project" → select the repo → Deploy
3. In Vercel Settings → Environment Variables → add `ANTHROPIC_API_KEY`
4. Get your key at https://console.anthropic.com (€5 = ~500 analyses)
5. Redeploy → live at spaininvest.vercel.app ✅

## 📁 Structure
pages/index.js        ← Main app
pages/api/analyze.js  ← Secure Claude proxy
components/translations.js ← EN/FR/ES
styles/globals.css

## 💰 API costs: ~€0.01/analysis
