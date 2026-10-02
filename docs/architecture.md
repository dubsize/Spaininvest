# ArbScan — technical design

ArbScan continuously collects second-hand listings, maps each one to a canonical product,
values it against comparable listings, subtracts every cost of doing the trade, scores
the result on **net profit × capital velocity**, flags risk, and alerts. It is built so
marketplaces are plug-ins and every business rule (fees, ROI targets, weights, alert
rules) is data, not code.

## 1. Repository layout

```
apps/web/                Next.js 15 + TypeScript + Tailwind + shadcn-style UI (dashboard)
backend/                 Python 3.11+ package `arbscan` (FastAPI, SQLAlchemy 2, Alembic, Celery)
  arbscan/
    core/                settings, structured logging, polite HTTP client (rate limit, retries, robots.txt)
    db/                  ORM models, enums, session
    connectors/          one module per marketplace + registry (eBay, stubs, demo feed, page metadata)
    normalization/       multilingual dictionaries, rule engine, catalogue loader, optional AI layer
    valuation/           weighted robust statistics + market value engine
    fees/                fee & cost engine, max-buy-price solver
    scoring/             opportunity score, liquidity, capital velocity, negotiation, offer calculator
    risk/                rules-based risk engine
    alerts/              channels (Telegram, e-mail, log) + rule evaluation & de-duplication
    services/            pipeline (ingest → evaluate), scanner orchestration, deals/portfolio, CSV, FX, settings
    workers/             Celery app + tasks (tick, scan, analysis, housekeeping)
    api/                 FastAPI app, security, schemas, routers
    seed/                catalogue & fee YAML, demo-data generator, loader
  alembic/               migrations
  tests/                 pytest suite (+ stored connector fixtures)
docs/                    this file, connectors & compliance
legacy/rental-analyzer/  the previous Spain Invest app (untouched, see its README)
docker-compose.yml       db, redis, api, worker, beat, web
```

*Why one Python package instead of top-level `/normalization`, `/valuation`… folders?*
The requested domains exist as sub-packages, but living in one installable package means
the API, the workers and the tests import them identically, with no `sys.path` tricks,
and every engine stays a pure, independently testable module.

## 2. Runtime components

| Component | Tech | Role |
|---|---|---|
| `web` | Next.js (standalone) | UI; proxies `/api/*` to the API so cookies are same-origin |
| `api` | FastAPI + Uvicorn | REST API, auth, CSRF, migrations + seeding on start |
| `worker` | Celery | scans, re-scoring, valuation snapshots, housekeeping |
| `beat` | Celery beat | fires `tick` every `SCANNER_TICK_SECONDS`, `analysis` every 30 min, `housekeeping` every 6 h |
| `db` | PostgreSQL 16 | system of record (JSONB for flexible attributes) |
| `redis` | Redis 7 | broker, shared rate limiting across workers, scan locks |

## 3. Data flow

```
connector.search()  ──►  RawListing (marketplace-agnostic)
        │
        ▼
ingest_raw_listing   upsert by (marketplace, external_id); FX → EUR (rate + timestamp stored);
                     sanitise text; append-only price history (initial/drop/increase);
                     content-hash change detection; normalisation
        │
        ▼
Evaluator.evaluate   per resale market (default ES):
   comparables (same product, as-of time, confidence ≥ 0.55)
   → ValuationEngine (weighted, outlier-robust)
   → FeeEngine (buy + prep + sell costs for the trade route)
   → max buy price (bisection over real fee rules)
   → liquidity + expected holding days → velocity metrics
   → RiskEngine (rules, explained)
   → classify FLIP / CROSS_BORDER / NEGOTIATION / NONE
   → compute_score (components + caps) → Opportunity row (one per listing × market)
        │
        ▼
AlertDispatcher      rules (any-of / all-of clauses) → channels; de-dup on
                     (listing, channel, fingerprint=price|type)
```

Every listing is evaluated, not only bargains: listings that are not deals are stored as
`NONE` opportunities so the listing page can still explain the maths.

## 4. Product normalisation

Deterministic first (`normalization/engine.py`):

1. **Fold** text (lower-case, accents removed, `ß→ss`) and detect the language
   (ES/FR/DE/IT/PT/EN stop words). Listings are never translated.
2. **Accessory-only detection** ("caja vacía", "funda para…", "box only", "compatible con"…)
   → confidence heavily penalised so boxes/cases never value as the product.
3. **Candidate scoring** per catalogue entry:
   reference/SKU in text (0.93) > alias/regex in title (0.72) > in description only (0.45),
   + brand in title (+0.15) / description (+0.07). *Required keywords* gate weak patterns
   ("love" counts only with "cartier"), unless an explicit alias such as "love bracelet"
   or a reference matched. *Excluded keywords* (rings vs bracelets, controllers vs
   consoles, TM5 vs TM6) reject in the title and penalise in the description.
4. **Attributes**: product-specific rules (regex → literal value, captured group or a
   template such as `m{0}_pro`), then generic multilingual detectors for material, size,
   colour, condition, accessories (with negations: "sin caja", "ohne Papiere").
5. **Confidence** 0–1, adjusted for ambiguity (runner-up close), missing critical
   attributes (flag attributes like `diamonds=yes` are never "missing"), accessory-only
   and conflicting marketplace brand fields. Human-readable reasons are stored.
6. **Variant key** = only critical attributes (importance ≥ 0.8), e.g.
   `material=yellow_gold`. Minor attributes (size, colour) are handled by comparable
   weighting, so valuations don't fragment.
7. **Optional AI layer** (`normalization/ai.py`): only consulted when rule confidence is
   below `AI_MIN_RULE_CONFIDENCE`, only allowed to pick a product that already exists in
   the catalogue, and its answer is capped below rule-based certainty. Off by default.

Authenticity statements are extracted verbatim as *seller claims*; nothing in the system
ever marks an item authentic.

## 5. Market value engine

`valuation/engine.py` — never a plain average:

* critical-attribute mismatches excluded; minor mismatches down-weighted (1 − importance);
  unknown attributes partially weighted;
* prices normalised to a "good condition, no accessories" baseline and re-scaled to the
  target listing (condition factors; luxury box/papers premiums);
* evidence weights: **sold ×3**, ended listings (probable sales) ×1.5, active asks ×1 with
  an ask-to-sale discount (0.93); stale asks (>60/120 days) down-weighted; other countries
  ×0.5 for the resale market; professional sellers ×0.8;
* outliers removed with a MAD z-score on log prices (ratio band when n < 5);
* outputs: n, sold count, median, trimmed mean, p10 ("lowest reasonable"), p25, p75,
  quick-sale (35th percentile, capped by 95 % of the sold median), normal market value
  (weighted median), opportunistic buy, dispersion (IQR/median), median days on market,
  per-country/marketplace medians;
* **confidence** from Kish effective sample size, dispersion and sold share →
  HIGH / MEDIUM / LOW / INSUFFICIENT (< 3 comparables). Scores are capped for LOW and
  INSUFFICIENT so poor data never looks reliable.

Valuation snapshots are appended (`valuations` table) for price history and trends; the
analysis job adds one per (product, variant, market) every `analysis_minutes`.

## 6. Fees, costs and returns

All fees live in `fee_rules` (per marketplace, side buy/sell, optional category/country,
percent + fixed + payment + min/max) and logistics in `cost_profiles` (route ×
shipping class / category: inbound/outbound shipping, insurance %, import duty %, import
VAT %, misc, pickup travel). Categories hold refurbishment, authentication cost, ROI
targets and base holding time; products may override. Seeded values are flagged
*unverified approximations*.

```
capital     = price + buy-side costs + preparation (authentication, refurbishment)
net profit  = sale price − sell-side costs − capital
ROI         = net profit / capital
MAX BUY     = largest price with ROI ≥ target AND profit ≥ min profit (bisection)
```
Routes: `domestic`, `intra_eu` (no customs between EU states), `import` (duty + 21 % IVA on
goods + shipping, placeholder duty rate — check TARIC).

## 7. Scoring (0–100)

Components (each 0–100): discount, net profit (saturating), ROI, liquidity, freshness
(half-life 72 h, price drops refresh it), confidence (valuation + match), velocity
(log-scaled annualised ROI). Final = weighted mean − risk penalty, then caps:
unprofitable ≤ 25, INSUFFICIENT data ≤ 35, LOW confidence ≤ 72, HIGH risk ≤ 60,
negotiation × 0.75. Weights and scales are editable in Settings → Scoring.

Velocity metrics stored per opportunity: holding-period ROI, annualised ROI, profit
velocity (€/day), capital efficiency (ROI/day), profit per €1,000, capital turnover.
The dashboard's "deploy capital now" ranking uses annualised ROI × confidence ×
(1 − risk) and excludes HIGH risk.

**Negotiation opportunities**: old (≥ 21 days) or price-reduced listings priced above max
buy but within 30 % of market, where the required discount is within 1.5× of the
heuristically achievable discount (5 % + 0.25 %/day + 3 %/price drop, max 30 %). The
target offer is 97 % of max buy, rounded to human numbers.

## 8. Risk engine

Independent rules returning explained, weighted flags: price vs market, seller account
age, ratings, off-platform/payment-outside language (multilingual), unprotected payment
methods, contact details in text, counterfeit wording, stock-photo text/hosts, single or
no photos, duplicate images across listings, same listing in several cities, private
seller with many unrelated high-value items, missing provenance (luxury), unknown
references, conflicting materials/brand, location mismatch, urgency language, thin
descriptions, accessory-only. Score → LOW / MEDIUM / HIGH. The engine never says
"fraud". Luxury items always carry: *"Authentication required before purchase. The
scanner does not certify authenticity."*

## 9. Scheduling

`tick` (every minute) enqueues scans for enabled marketplaces whose `next_run_at` passed.
`poll_interval_seconds` per marketplace is a floor; failures back off exponentially
(×2 up to ×32). Inside a scan only due watchlists are searched (intervals by priority:
high 5 min, standard 30 min, background 3 h, or per watchlist). Redis locks prevent
overlapping scans. `analysis` (30 min) re-scores active listings and appends valuation
snapshots on the slower cadence; `housekeeping` expires listings unseen for 7 days and
refreshes ECB FX rates when enabled.

## 10. Security

Single-user login (bcrypt hash or dev plaintext from env), signed JWT in an HttpOnly
SameSite=Lax cookie, double-submit CSRF token for every mutating request, login and API
rate limits, security headers + CSP on web and API, scraped text sanitised on ingest and
always rendered as text (React escaping, no `dangerouslySetInnerHTML`), image URLs limited
to http(s), external links `rel="noopener noreferrer nofollow"`, SSRF guard for the
manual-entry page fetcher, secrets only via environment, containers run as non-root.

## 11. Observability

JSON logs (stdlib) for API requests (method, path, status, latency, request id), scans
(duration, found/new/updated/price changes/opportunities), connector errors and alerts.
`scan_runs` stores every run; `marketplaces` keeps last run/success/error, consecutive
failures and next run — all shown on the Scanner page.

## 12. Phases

| Phase | Scope | State |
|---|---|---|
| 1 | Architecture, DB, engines, demo data, dashboard, Docker | done |
| 2 | eBay Browse API connector through the full pipeline, alerts | done (needs your eBay keys) |
| 3 | Other marketplaces via compliant methods (partner APIs, e-mail alert ingestion) | stubs + manual entry/CSV |
| 4 | AI normalisation, richer cross-market arbitrage | AI layer scaffolded (optional) |
| 5 | Learn from deal outcomes (calibrate quick-sale/holding time per category) | data captured in deal tracker |
