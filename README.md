# ArbScan — second-hand deal & arbitrage scanner

ArbScan monitors second-hand marketplaces, maps every listing to a canonical product (in
Spanish, French, German, Italian, Portuguese or English), estimates its market value from
comparable listings, subtracts **all** costs of the trade, and ranks opportunities by
**net profit × capital velocity**, adjusted for confidence and risk. It answers one
question: *where can I deploy €1 today for the best risk-adjusted return?*

* **Opportunity types:** local flips (buy & resell in Spain), cross-border arbitrage
  (buy in FR/DE/IT, resell in Spain) and negotiation targets (old or price-reduced
  listings, with a target offer).
* **Per opportunity:** quick-sale and market value with a confidence level and the number
  of comparables, full cost breakdown, net profit, ROI, MAX BUY PRICE, annualised ROI,
  profit velocity, liquidity, explained risk flags, a 0–100 Opportunity Score with
  component breakdown, and a "what should I offer?" calculator.
* **Operations:** watchlists, a scanner with per-marketplace polling floors, Telegram
  and e-mail alerts with de-duplication, price-drop tracking, manual entry for any URL,
  CSV import/export, a deal tracker (PURCHASED → SOLD with actual costs) and a
  portfolio/capital dashboard.

> The scanner never certifies authenticity and never labels a listing as fraud. It
> surfaces signals for you to check. Luxury items always carry the warning
> *"Authentication required before purchase."*

![stack](https://img.shields.io/badge/stack-FastAPI%20·%20PostgreSQL%20·%20Redis%20·%20Celery%20·%20Next.js-informational)

---

## Quick start (Docker)

```bash
cp .env.example .env          # then edit ADMIN_PASSWORD and JWT_SECRET at least
docker compose up --build     # first start: migrations + ~600 demo listings are created
```

Open **http://localhost:3000** and log in as `admin` with the `ADMIN_PASSWORD` from `.env`
(`change-me` in the example file). API docs: http://localhost:8000/api/docs.

Services: `db` (PostgreSQL 16), `redis`, `api` (FastAPI; runs migrations and seeding on
start), `worker` + `beat` (Celery scans and re-scoring), `web` (Next.js). Ports are bound
to `127.0.0.1` only.

**Behind a corporate TLS proxy?** If `docker compose build` fails with certificate
errors, drop your proxy's CA certificate (PEM, `*.crt`) into `backend/certs/` and
`apps/web/certs/` and build again.

### What you see immediately

Demo data covers all 39 seeded products across Wallapop, Leboncoin and eBay ES/FR/DE:
normal listings, bargains, overpriced ones, scam-like ones (HIGH risk), old negotiable
listings, price-reduced listings with history, ended listings (for liquidity), and nine
tracked deals for the portfolio page. A **demo feed** connector adds a few fresh
synthetic listings every 5 minutes so you can watch the pipeline run. Demo listings are
marked `DEMO DATA`, never send Telegram or e-mail alerts, and can be deleted in
**Settings → Purge demo data** (or start with `SEED_DEMO_DATA=false`).

## Connecting real marketplaces

| Marketplace | How |
|---|---|
| **eBay ES / FR / DE** | Official Browse API. Create a keyset at <https://developer.ebay.com/my/keys>, set `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` in `.env`, restart, then use *Scanner → Health check / Scan now*. |
| Wallapop, Leboncoin, Vinted, Kleinanzeigen, Milanuncios, Vestiaire, Chrono24, Catawiki | No compliant public search API → **stub connectors**. Use their own saved-search alerts and paste interesting URLs into **Add listing**, or import CSV. |
| Facebook Marketplace | Disabled (no API; automated collection prohibited). Manual entry only. |
| Amazon | Product Advertising API needs an approved Associates account — stub for now. |

Details, rationale and the plan for e-mail-alert ingestion: [docs/connectors.md](docs/connectors.md).

## Alerts

* **Telegram:** create a bot with @BotFather, message it once, read your chat id from
  `https://api.telegram.org/bot<TOKEN>/getUpdates`, set `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID`.
* **E-mail:** set the `SMTP_*` variables and `ALERT_EMAIL_TO`.
* Test from **Settings → Alerts**. Default rule: score ≥ 80, **or** net profit ≥ €250
  and ROI ≥ 20 %, **or** price ≤ 70 % of quick-sale value. Rules are editable JSON
  (any-of groups of all-of clauses) with a max-risk filter. An unchanged listing never
  re-alerts; a price drop does (as "📉 PRICE DROP").
* New channels (WhatsApp, Discord, Slack, push) = one `Channel` subclass in
  `backend/arbscan/alerts/channels.py`.

## Using it

| Page | Purpose |
|---|---|
| Dashboard | KPIs, *deploy capital now* ranking, hottest / newest / highest profit / ROI / liquidity / cross-border / negotiation / price-reduced |
| Opportunities | Sortable table with every filter (marketplace, country, city, brand, category, condition, price, discount, profit, ROI, score, risk, age, seller rating, status), CSV export |
| Listing | Details, seller, normalisation (with manual re-match), score breakdown, cost breakdown, risk flags, comparables, price history, status workflow, PURCHASED, offer calculator |
| Products | Canonical catalogue CRUD (aliases, regexes, SKUs, variant attributes), matcher tester; product page with value estimate, MAX BUY PRICE, distribution, marketplace comparison, historical value, listings |
| Watchlists | What to search, where, how often (priority) and deal thresholds |
| Add listing | Manual entry for any URL/marketplace; optional single public-metadata fetch |
| Deal tracker / Portfolio | Actual purchase & sale costs → realised profit, ROI, holding period, annualised return; capital deployed, inventory ageing, profit by category/marketplace/country |
| Scanner | Connector status, schedules, health checks, scan runs, errors |
| Settings | Business defaults (resale market, ROI targets), score weights, valuation knobs, fee rules, logistics costs, categories, alert rules |

Statuses: DISCOVERED → WATCHING → CONTACTED → NEGOTIATING → PURCHASED → RECEIVED →
LISTED_FOR_RESALE → SOLD, plus REJECTED, SCAM_RISK and EXPIRED.

**Fees are approximations.** Seeded marketplace fees are flagged *unverified*. Check each
marketplace's fee page and update **Settings → Fees** before trusting profit numbers.

## Local development (without Docker)

```bash
# backend (Python 3.11+, PostgreSQL; Redis optional for dev)
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
export DATABASE_URL=postgresql+psycopg://arbscan:arbscan@localhost:5432/arbscan ADMIN_PASSWORD=dev JWT_SECRET=dev-secret-dev-secret-dev-secret-00
python -m arbscan.cli migrate && python -m arbscan.cli seed --demo
uvicorn arbscan.api.main:app --reload --port 8000
celery -A arbscan.workers.celery_app:celery_app worker -B   # optional: scheduled scans

# frontend
cd apps/web && npm install && npm run dev      # http://localhost:3000 (proxies /api to :8000)
```

CLI: `python -m arbscan.cli migrate | seed [--demo] | demo-purge | scan <marketplace> | analysis | hash-password`.

Production login: generate a bcrypt hash with `python -m arbscan.cli hash-password` (in Docker:
`docker compose run --rm api python -m arbscan.cli hash-password`), put it in
`ADMIN_PASSWORD_HASH` (double every `$` in `.env`), clear `ADMIN_PASSWORD`, set a long
`JWT_SECRET`, `COOKIE_SECURE=true` behind HTTPS, and `ENVIRONMENT=production`.

## Tests

```bash
cd backend && pytest                       # 139 tests, SQLite, no services needed
TEST_DATABASE_URL=postgresql+psycopg://arbscan:arbscan@localhost:5432/arbscan_test pytest   # against PostgreSQL
ruff check arbscan tests
cd apps/web && npm run typecheck && npm run lint
```

Coverage: normalisation (multilingual, SKUs, exclusions, accessories, conditions),
valuation (weighting, outliers, sold data, confidence), fees & max buy price, ROI and
scoring (caps, freshness, velocity, negotiation, offer calculator), risk rules, alert
rules & de-duplication, ingest/price history/FX, eBay parser fixtures + a mocked
end-to-end eBay scan (collection → normalisation → valuation → scoring → alerts →
price-drop alert), page-metadata parsing, robots.txt, retries, SSRF guard, the optional
AI normaliser (mocked), and the HTTP API (auth, CSRF, filters, CRUD, manual entry,
deals, CSV).

## Optional AI normalisation

Rules handle matching on their own. To let Claude resolve the *uncertain* cases
(rule confidence < `AI_MIN_RULE_CONFIDENCE`), set `AI_NORMALIZER=anthropic` and
`ANTHROPIC_API_KEY` (the Docker image already includes the SDK; for local installs use
`pip install 'arbscan[ai]'`). Default model: `claude-opus-5-5` (`ANTHROPIC_MODEL`). The model may only choose products that exist in your
catalogue, and its confidence is capped below exact rule matches.

## Architecture & roadmap

See [docs/architecture.md](docs/architecture.md) for the full design (data model,
normalisation, valuation maths, fee model, scoring, risk, scheduling, security,
observability).

| Phase | Scope | Status |
|---|---|---|
| 1 | Architecture, DB, engines, demo data, dashboard, Docker | ✅ |
| 2 | eBay Browse API through the full pipeline, alerts | ✅ needs your eBay keys |
| 3 | Other marketplaces via compliant routes (e-mail alert ingestion, partner APIs) | stubs + manual/CSV today |
| 4 | Advanced AI normalisation, richer cross-market arbitrage | optional AI layer in place |
| 5 | Learn from your deals (calibrate quick-sale price & holding time per category) | data captured by the deal tracker |

## Repository

```
apps/web        Next.js dashboard
backend         FastAPI / Celery / SQLAlchemy package `arbscan` + tests + Alembic
docs            architecture & connector documentation
legacy/rental-analyzer   previous "Spain Invest" rental analyser (unchanged)
```

The previous Vercel app now lives in `legacy/rental-analyzer/`. If it is still deployed
on Vercel, set the project's **Root Directory** to `legacy/rental-analyzer`.
