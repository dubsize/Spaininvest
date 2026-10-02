"""eBay connector - official Buy > Browse API.

Docs:
* OAuth client-credentials grant: https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html
* Browse API search: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
* Browse API getItem: https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem
* Marketplace IDs: EBAY_ES, EBAY_FR, EBAY_DE, EBAY_IT ...

Completed/sold prices: eBay's Marketplace Insights API provides sold-item data but is a
*limited release* API that requires eBay approval. ``search_sold`` therefore returns
nothing unless ``marketplace_insights_enabled`` is set in the marketplace config (after
approval). Scraping eBay's sold-listing pages is not used.
"""

from __future__ import annotations

import base64
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from arbscan.connectors.base import (
    ComplianceInfo,
    Connector,
    ConnectorNotConfigured,
    HealthStatus,
    RawListing,
    SearchQuery,
)
from arbscan.core.config import get_settings
from arbscan.core.http import PoliteClient
from arbscan.core.logging import get_logger
from arbscan.normalization.text import sanitize_text

log = get_logger(__name__)

API_BASE = {"production": "https://api.ebay.com", "sandbox": "https://api.sandbox.ebay.com"}
SCOPE = "https://api.ebay.com/oauth/api_scope"
INSIGHTS_SCOPE = "https://api.ebay.com/oauth/api_scope/buy.marketplace.insights"

_token_cache: dict[str, tuple[str, float]] = {}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _money(obj: dict[str, Any] | None) -> tuple[float | None, str | None]:
    if not obj or obj.get("value") in (None, ""):
        return None, None
    try:
        return float(obj["value"]), obj.get("currency")
    except (TypeError, ValueError):
        return None, None


class EbayBrowseConnector(Connector):
    key = "ebay"
    display_name = "eBay (Browse API)"
    countries = ["ES", "FR", "DE", "IT"]
    supports_sold_data = False
    default_poll_seconds = 600
    default_requests_per_minute = 30
    compliance = ComplianceInfo(
        method="official_api",
        summary="Official eBay Buy Browse API (OAuth client credentials). Subject to eBay API License Agreement and call limits.",
        docs_url="https://developer.ebay.com/api-docs/buy/browse/overview.html",
        alternative="Sold prices require the Marketplace Insights API (limited release, apply to eBay).",
        requires_credentials=True,
    )

    def __init__(self, marketplace_code: str, config: dict[str, Any] | None = None, client: PoliteClient | None = None):
        super().__init__(marketplace_code, config)
        self.settings = get_settings()
        self.ebay_marketplace_id = self.config.get("ebay_marketplace_id", "EBAY_ES")
        self.country = self.config.get("country", "ES")
        self.base = API_BASE.get(self.settings.ebay_environment, API_BASE["production"])
        self.client = client or PoliteClient(
            f"ebay:{self.ebay_marketplace_id}",
            requests_per_minute=int(self.config.get("requests_per_minute", self.default_requests_per_minute)),
            enforce_robots=False,  # official API, governed by API terms not robots.txt
        )

    # ------------------------------------------------------------------ auth
    def is_configured(self) -> bool:
        return bool(self.settings.ebay_client_id and self.settings.ebay_client_secret)

    def _token(self, scope: str = SCOPE) -> str:
        if not self.is_configured():
            raise ConnectorNotConfigured("EBAY_CLIENT_ID / EBAY_CLIENT_SECRET not set")
        cache_key = f"{self.base}:{scope}"
        cached = _token_cache.get(cache_key)
        if cached and cached[1] > time.time() + 60:
            return cached[0]
        basic = base64.b64encode(f"{self.settings.ebay_client_id}:{self.settings.ebay_client_secret}".encode()).decode()
        resp = self.client.post(
            f"{self.base}/identity/v1/oauth2/token",
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": scope},
        )
        data = resp.json()
        _token_cache[cache_key] = (data["access_token"], time.time() + int(data.get("expires_in", 7200)))
        return data["access_token"]

    def _headers(self) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self._token()}",
            "X-EBAY-C-MARKETPLACE-ID": self.ebay_marketplace_id,
            "Accept": "application/json",
        }
        if self.settings.ebay_affiliate_campaign_id:
            h["X-EBAY-C-ENDUSERCTX"] = f"affiliateCampaignId={self.settings.ebay_affiliate_campaign_id}"
        return h

    # ------------------------------------------------------------------ API
    def build_search_params(self, query: SearchQuery) -> dict[str, str]:
        filters = []
        if query.min_price is not None or query.max_price is not None:
            lo = "" if query.min_price is None else f"{query.min_price:.0f}"
            hi = "" if query.max_price is None else f"{query.max_price:.0f}"
            filters.append(f"price:[{lo}..{hi}]")
            filters.append("priceCurrency:EUR")
        filters.append(f"itemLocationCountry:{self.country}")
        filters.append("buyingOptions:{FIXED_PRICE|BEST_OFFER}")
        params = {
            "q": query.keywords,
            "limit": str(min(max(query.limit, 1), 200)),
            "filter": ",".join(filters),
        }
        if query.sort == "newly_listed":
            params["sort"] = "newlyListed"
        if query.extra.get("category_ids"):
            params["category_ids"] = str(query.extra["category_ids"])
        return params

    def search(self, query: SearchQuery) -> list[RawListing]:
        params = self.build_search_params(query)
        resp = self.client.get(f"{self.base}/buy/browse/v1/item_summary/search?{urlencode(params)}", headers=self._headers())
        payload = resp.json()
        return self.parse_search_response(payload)

    def parse_search_response(self, payload: dict[str, Any]) -> list[RawListing]:
        items = payload.get("itemSummaries") or []
        out = []
        for item in items:
            try:
                out.append(self.normalize_listing(item))
            except (KeyError, TypeError, ValueError) as exc:
                log.warning("ebay item skipped", extra={"err": str(exc), "item_id": item.get("itemId")})
        return out

    def get_listing(self, external_id: str) -> RawListing | None:
        resp = self.client.get(f"{self.base}/buy/browse/v1/item/{external_id}", headers=self._headers())
        return self.normalize_listing(resp.json())

    def search_sold(self, query: SearchQuery) -> list[RawListing]:
        if not self.config.get("marketplace_insights_enabled"):
            return []
        token = self._token(INSIGHTS_SCOPE)
        params = {"q": query.keywords, "limit": str(min(query.limit, 200))}
        resp = self.client.get(
            f"{self.base}/buy/marketplace_insights/v1_beta/item_sales/search?{urlencode(params)}",
            headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": self.ebay_marketplace_id},
        )
        out = []
        for item in resp.json().get("itemSales") or []:
            rl = self.normalize_listing(item)
            rl.status, rl.price_kind = "sold", "sold"
            price, _ = _money(item.get("lastSoldPrice"))
            rl.sold_price = price or rl.price
            rl.sold_at = _parse_dt(item.get("lastSoldDate"))
            out.append(rl)
        return out

    # ------------------------------------------------------------------ parsing
    def normalize_listing(self, payload: dict[str, Any]) -> RawListing:
        price, currency = _money(payload.get("price") or payload.get("lastSoldPrice"))
        if price is None:
            # auctions without BIN expose currentBidPrice
            price, currency = _money(payload.get("currentBidPrice"))
        if price is None:
            raise ValueError("no price")
        original, _ = _money((payload.get("marketingPrice") or {}).get("originalPrice"))
        seller = payload.get("seller") or {}
        rating = None
        if seller.get("feedbackPercentage") not in (None, ""):
            try:
                rating = round(float(seller["feedbackPercentage"]) / 20, 2)
            except ValueError:
                rating = None
        loc = payload.get("itemLocation") or {}
        images = []
        if (payload.get("image") or {}).get("imageUrl"):
            images.append(payload["image"]["imageUrl"])
        for extra in payload.get("additionalImages") or []:
            if extra.get("imageUrl"):
                images.append(extra["imageUrl"])
        shipping_cost = None
        shipping_available = None
        for opt in payload.get("shippingOptions") or []:
            cost, _ = _money(opt.get("shippingCost"))
            shipping_available = True
            if cost is not None:
                shipping_cost = cost if shipping_cost is None else min(shipping_cost, cost)
        cats = payload.get("categories") or []
        aspects = {a.get("name"): a.get("value") for a in payload.get("localizedAspects") or [] if a.get("name")}
        description = payload.get("description") or payload.get("shortDescription") or ""
        item_id = str(payload["itemId"])
        return RawListing(
            marketplace=self.marketplace_code,
            external_id=item_id,
            url=payload.get("itemWebUrl") or payload.get("itemAffiliateWebUrl") or "",
            title=sanitize_text(payload.get("title", ""), 500),
            description=sanitize_text(description),
            price=price,
            currency=currency or "EUR",
            original_price=original,
            country=loc.get("country") or self.country,
            city=loc.get("city"),
            region=loc.get("stateOrProvince"),
            postal_code=loc.get("postalCode"),
            seller_id=seller.get("username"),
            seller_name=seller.get("username"),
            seller_rating=rating,
            seller_rating_count=seller.get("feedbackScore"),
            seller_type=None,
            condition_raw=payload.get("condition"),
            category_raw=" > ".join(c.get("categoryName", "") for c in cats) or payload.get("categoryPath"),
            brand_raw=payload.get("brand") or aspects.get("Marca") or aspects.get("Marque") or aspects.get("Marke") or aspects.get("Brand"),
            model_raw=payload.get("mpn") or aspects.get("Modelo") or aspects.get("Modèle") or aspects.get("Modell") or aspects.get("Model"),
            published_at=_parse_dt(payload.get("itemCreationDate") or payload.get("itemOriginDate")),
            shipping_available=shipping_available,
            shipping_cost=shipping_cost,
            image_urls=images[:12],
            status="active",
            raw=payload,
            source_metadata={
                "ebay_marketplace_id": self.ebay_marketplace_id,
                "buying_options": payload.get("buyingOptions"),
                "condition_id": payload.get("conditionId"),
                "item_end_date": payload.get("itemEndDate"),
                "aspects": aspects or None,
            },
        )

    def health_check(self) -> HealthStatus:
        if not self.is_configured():
            return HealthStatus("NOT_CONFIGURED", "Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET (developer.ebay.com).")
        start = time.monotonic()
        try:
            self._token()
        except Exception as exc:  # noqa: BLE001
            return HealthStatus("ERROR", f"OAuth failed: {exc}")
        return HealthStatus("OK", "token acquired", int((time.monotonic() - start) * 1000))
