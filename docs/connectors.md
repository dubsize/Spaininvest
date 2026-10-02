# Marketplace connectors & compliance

Every marketplace is an independent connector (`backend/arbscan/connectors/`) implementing

```python
search(query) -> list[RawListing]          # collect
get_listing(external_id) -> RawListing      # refresh one item
normalize_listing(payload) -> RawListing    # pure parser, unit-tested with stored fixtures
health_check() -> HealthStatus
search_sold(query) -> list[RawListing]      # only where sold data is compliantly available
```

Connectors never value, score or alert: they emit marketplace-agnostic `RawListing`s and
the pipeline does the rest. Marketplace rows in the DB (`marketplaces`) bind a connector
key to configuration (e.g. eBay ES/FR/DE share one implementation with different
`ebay_marketplace_id`), a polling floor and a request budget.

**Ground rules:** use official APIs, public feeds or permitted integrations; respect
`robots.txt`, rate limits and terms; never bypass logins, CAPTCHAs, anti-bot systems or
use undocumented private endpoints. Where that leaves no automated route, the connector
is a documented stub and the marketplace is covered by **manual entry** and **CSV import**.

## Status

| Marketplace | Connector | Method | Status |
|---|---|---|---|
| eBay ES / FR / DE (/ IT) | `ebay` | Official **Buy › Browse API** (OAuth client credentials) | ✅ implemented — add keys to enable |
| eBay sold prices | `ebay.search_sold` | **Marketplace Insights API** (limited release; requires eBay approval) | ⏸ code path ready, disabled until approved (`marketplace_insights_enabled` in marketplace config) |
| Wallapop | `wallapop` | none public | 🟡 stub → manual entry / CSV |
| Leboncoin | `leboncoin` | none public for search (pro API is for publishing ads) | 🟡 stub → manual entry / CSV |
| Vinted ES/FR/DE/IT | `vinted` | none public | 🟡 stub |
| Kleinanzeigen | `kleinanzeigen` | none public | 🟡 stub |
| Milanuncios | `milanuncios` | none public | 🟡 stub |
| Vestiaire Collective | `vestiaire` | none public | 🟡 stub (used as resale channel in fee rules) |
| Chrono24 | `chrono24` | none public for third parties | 🟡 stub |
| Catawiki | `catawiki` | none public | 🟡 stub (record hammer prices as SOLD via CSV) |
| Facebook Marketplace | `facebook` | no API, automated collection prohibited | ⛔ disabled |
| Amazon ES/FR/DE/IT | `amazon` | Product Advertising API (needs approved Associates account) | 🟡 stub — implement when credentials exist; check current API status/successor |
| Any other site | `manual` | Manual entry / CSV | ✅ |
| Demo feed | `demo` | Synthetic data | ✅ (disable in Settings › Scanner or by purging demo data) |

## eBay setup (Phase 2)

1. Create a developer account at <https://developer.ebay.com>, create an application and
   copy the **Production** keyset (App ID = client id, Cert ID = client secret).
2. Put them in `.env`: `EBAY_CLIENT_ID=…`, `EBAY_CLIENT_SECRET=…` and restart
   (`docker compose up -d`).
3. Scanner page → eBay España → *Health check* (should say `OK: token acquired`) → *Scan now*.
4. Watchlists drive the queries. Each eBay marketplace searches `itemLocationCountry`
   of its own country, newest first, fixed-price/best-offer items, capped at the
   watchlist max price.

Calls: `POST /identity/v1/oauth2/token` (scope `https://api.ebay.com/oauth/api_scope`,
token cached until expiry) and `GET /buy/browse/v1/item_summary/search` with
`X-EBAY-C-MARKETPLACE-ID`. Default budget 30 requests/min per marketplace and a 10-minute
polling floor — well inside eBay's default Browse API quota; raise only if your quota
allows. Optional `EBAY_AFFILIATE_CAMPAIGN_ID` adds the documented
`X-EBAY-C-ENDUSERCTX` header.

## Best compliant alternatives for the stubbed marketplaces

1. **Their own alerts + manual entry (works today).** Create saved searches with push or
   e-mail alerts in Wallapop / Leboncoin / Vinted / Kleinanzeigen; when one looks
   interesting, paste the URL into *Add listing*. The scanner detects the marketplace,
   can make one user-initiated fetch of the page's public OpenGraph/schema.org metadata
   (only if robots.txt allows), and values it against the whole database.
2. **E-mail alert ingestion (planned Phase 3).** Parse the saved-search alert e-mails the
   marketplaces send *you* (IMAP, read-only mailbox). This is data addressed to you, at
   the cadence the platform chose, with no scraping.
3. **Partner / data agreements.** Ask the marketplace for API or partner access (several
   offer professional/business programmes). A new connector then only has to implement
   the interface above.
4. **CSV import** for anything collected by hand, including **sold** prices
   (`price_kind=sold`), which the valuation engine weights 3× higher than asks.

## Engineering features available to every connector (`core/http.py`)

* Per-host rate limiting (Redis-backed fixed window shared by all workers; in-process
  token bucket fallback).
* Retries with exponential backoff + jitter on network errors, 429 and 5xx, honouring
  `Retry-After`; scheduler-level exponential back-off after repeated failures.
* `robots.txt` enforcement for page fetches (cached 1 h; 5xx on robots → treated as
  disallow). Official APIs are governed by their API terms instead.
* Identifying User-Agent (`HTTP_CONTACT`), optional proxy (`OUTBOUND_PROXY_URL`) — only
  for networks you are entitled to use, never to evade blocks.
* Layout-change detection: parsers raise `LayoutChanged` when a page has content but
  none of the expected structure, which surfaces as a connector error instead of silently
  returning nothing.
* Structured logs and `scan_runs` metrics (duration, found/new/updated/price changes,
  opportunities, alerts, errors).

## Adding a connector

1. Create `connectors/<name>.py` with a `Connector` subclass (`key`, `display_name`,
   `countries`, `compliance`, the four methods). Keep `normalize_listing` a pure function.
2. Store a real (anonymised) API response under `tests/fixtures/` and write parser tests.
3. Register it in `connectors/registry.py` (`CONNECTORS` + `MARKETPLACE_SEED`).
4. Add fee rules for the marketplace in Settings › Fees (or `seed/data/fees.yaml`).
