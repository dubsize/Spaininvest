"""API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ORM = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------- generic
class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class LoginIn(BaseModel):
    username: str = Field(max_length=120)
    password: str = Field(max_length=500)


# ---------------------------------------------------------------------------- products
class ProductSummary(BaseModel):
    model_config = ORM
    id: int
    slug: str
    name: str
    brand: str
    model: str
    category_code: str


class ProductIn(BaseModel):
    slug: str | None = Field(default=None, max_length=120)
    name: str = Field(max_length=200)
    brand: str = Field(max_length=80)
    model: str = Field(max_length=120)
    collection: str | None = None
    product_type: str | None = None
    category_code: str
    brand_aliases: list[str] = []
    aliases: list[str] = []
    patterns: list[str] = []
    reference_numbers: list[str] = []
    required_keywords: list[str] = []
    excluded_keywords: list[str] = []
    variant_attributes: dict[str, float] = {}
    attribute_rules: dict[str, list[dict[str, str]]] = {}
    retail_price_eur: float | None = None
    popularity: float = Field(default=0.5, ge=0, le=1)
    typical_holding_days: float | None = None
    refurbishment_eur: float | None = None
    target_roi: float | None = None
    is_active: bool = True
    notes: str = ""

    @field_validator("patterns")
    @classmethod
    def _valid_regex(cls, v: list[str]) -> list[str]:
        import re

        for p in v:
            try:
                re.compile(p)
            except re.error as exc:
                raise ValueError(f"invalid regex '{p}': {exc}") from exc
        return v


class ProductOut(ProductIn):
    model_config = ORM
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------- marketplaces
class MarketplaceOut(BaseModel):
    model_config = ORM
    code: str
    name: str
    country: str
    connector_key: str
    enabled: bool
    status: str
    supports_sold_data: bool
    poll_interval_seconds: int
    max_requests_per_minute: int
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
    next_run_at: datetime | None
    consecutive_failures: int
    total_listings_collected: int
    compliance_notes: str
    config: dict[str, Any]


class MarketplaceUpdate(BaseModel):
    enabled: bool | None = None
    poll_interval_seconds: int | None = Field(default=None, ge=120, le=86400)
    max_requests_per_minute: int | None = Field(default=None, ge=1, le=120)
    config: dict[str, Any] | None = None


class ScanRunOut(BaseModel):
    model_config = ORM
    id: int
    marketplace_code: str
    query: str
    kind: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    status: str
    listings_found: int
    listings_new: int
    listings_updated: int
    price_changes: int
    opportunities_created: int
    alerts_sent: int
    error: str | None


# ---------------------------------------------------------------------------- listings
class ListingSummary(BaseModel):
    model_config = ORM
    id: int
    marketplace_code: str
    external_id: str
    url: str
    title: str
    price_amount: float
    currency: str
    price_eur: float
    city: str | None
    country: str
    condition: str
    image_urls: list[str]
    published_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    status: str
    price_drop_count: int
    last_price_change_pct: float | None
    last_price_change_at: datetime | None
    seller_rating: float | None
    seller_rating_count: int | None
    normalization_confidence: float
    variant: dict[str, Any]
    is_demo: bool
    source: str


class PricePoint(BaseModel):
    model_config = ORM
    price_amount: float
    currency: str
    price_eur: float
    change_type: str
    change_pct: float | None
    observed_at: datetime


class ListingDetail(ListingSummary):
    description: str
    language: str | None
    original_price_amount: float | None
    original_price_eur: float | None
    fx_rate: float
    fx_timestamp: datetime | None
    price_kind: str
    sold_price_eur: float | None
    region: str | None
    postal_code: str | None
    seller_id: str | None
    seller_name: str | None
    seller_account_created_at: datetime | None
    seller_type: str | None
    seller_listing_count: int | None
    condition_raw: str | None
    category_raw: str | None
    brand_raw: str | None
    model_raw: str | None
    shipping_available: bool | None
    shipping_cost_eur: float | None
    ended_at: datetime | None
    canonical_product_id: int | None
    detected_brand: str | None
    detected_model: str | None
    variant_key: str
    detected_size: str | None
    detected_material: str | None
    accessories: dict[str, Any]
    authenticity_info: str | None
    normalization_method: str | None
    normalization_details: dict[str, Any]
    source_metadata: dict[str, Any]
    price_history: list[PricePoint] = []


class ListingPatch(BaseModel):
    """Manual corrections (e.g. wrong product match)."""

    canonical_product_id: int | None = None
    variant: dict[str, str] | None = None
    condition: str | None = None
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    city: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    seller_rating: float | None = Field(default=None, ge=0, le=5)
    seller_rating_count: int | None = Field(default=None, ge=0)
    shipping_cost_eur: float | None = None
    status: str | None = None


class ManualListingIn(BaseModel):
    url: str = Field(max_length=1024)
    title: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    currency: str = "EUR"
    marketplace: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = None
    description: str = ""
    condition: str | None = None
    seller_name: str | None = None
    seller_rating: float | None = Field(default=None, ge=0, le=5)
    seller_rating_count: int | None = Field(default=None, ge=0)
    seller_account_created_at: datetime | None = None
    published_at: datetime | None = None
    shipping_available: bool | None = None
    shipping_cost: float | None = None
    image_urls: list[str] = []
    canonical_product_id: int | None = None
    price_kind: str = "asking"
    fetch_metadata: bool = False


# ---------------------------------------------------------------------------- opportunities
class OpportunityOut(BaseModel):
    model_config = ORM
    id: int
    listing_id: int
    canonical_product_id: int | None
    opportunity_type: str
    resale_country: str
    source_country: str
    is_active: bool
    status: str
    purchase_price_eur: float
    quick_sale_eur: float | None
    market_value_eur: float | None
    buy_costs_eur: float
    sell_costs_eur: float
    total_costs_eur: float
    cost_breakdown: dict[str, Any]
    net_profit_quick_eur: float | None
    net_profit_market_eur: float | None
    roi: float | None
    discount_pct: float | None
    max_buy_price_eur: float | None
    target_offer_eur: float | None
    profit_at_target_offer_eur: float | None
    expected_holding_days: float | None
    annualized_roi: float | None
    profit_velocity: float | None
    capital_efficiency: float | None
    profit_per_1000: float | None
    liquidity_score: float | None
    liquidity_label: str | None
    confidence_score: float | None
    confidence_level: str | None
    normalization_confidence: float | None
    risk_level: str
    risk_score: float
    risk_flags: list[dict[str, Any]]
    requires_authentication: bool
    score: float
    score_components: dict[str, Any]
    explanation: list[Any]
    computed_at: datetime
    listing: ListingSummary
    canonical_product: ProductSummary | None


class StatusIn(BaseModel):
    status: str
    note: str = ""


class OfferIn(BaseModel):
    target_roi: float | None = Field(default=None, ge=0, le=5)
    target_profit_eur: float = Field(default=0, ge=0)
    expected_resale: float | None = Field(default=None, gt=0)
    expected_costs_eur: float | None = Field(default=None, ge=0)
    asking_price: float | None = Field(default=None, gt=0)


# ---------------------------------------------------------------------------- watchlists
class WatchlistIn(BaseModel):
    name: str = Field(max_length=160)
    keyword: str = Field(default="", max_length=200)
    canonical_product_id: int | None = None
    category_code: str | None = None
    brands: list[str] = []
    countries: list[str] = []
    marketplaces: list[str] = []
    max_price_eur: float | None = Field(default=None, ge=0)
    min_discount: float | None = Field(default=None, ge=0, le=1)
    min_profit_eur: float | None = None
    min_roi: float | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)
    priority: str = Field(default="standard", pattern="^(high|standard|background)$")
    scan_interval_minutes: int | None = Field(default=None, ge=2, le=10080)
    enabled: bool = True


class WatchlistOut(WatchlistIn):
    model_config = ORM
    id: int
    last_scanned_at: datetime | None
    next_scan_at: datetime | None
    created_at: datetime
    canonical_product: ProductSummary | None = None


# ---------------------------------------------------------------------------- deals
class PurchaseIn(BaseModel):
    purchase_price_eur: float = Field(gt=0)
    purchase_date: datetime | None = None
    purchase_shipping_eur: float = Field(default=0, ge=0)
    repair_cost_eur: float = Field(default=0, ge=0)
    authentication_cost_eur: float = Field(default=0, ge=0)
    other_purchase_cost_eur: float = Field(default=0, ge=0)
    expected_sale_price_eur: float | None = None
    notes: str = ""


class DealIn(PurchaseIn):
    title: str = Field(max_length=500)
    category_code: str | None = None
    canonical_product_id: int | None = None
    source_marketplace: str | None = None
    source_country: str | None = None


class SaleIn(BaseModel):
    sale_price_eur: float = Field(gt=0)
    sale_marketplace: str | None = None
    sale_date: datetime | None = None
    sale_fees_eur: float = Field(default=0, ge=0)
    sale_shipping_eur: float = Field(default=0, ge=0)
    sale_other_costs_eur: float = Field(default=0, ge=0)
    note: str = ""


class DealPatch(BaseModel):
    status: str | None = None
    purchase_price_eur: float | None = None
    purchase_date: datetime | None = None
    purchase_shipping_eur: float | None = None
    repair_cost_eur: float | None = None
    authentication_cost_eur: float | None = None
    other_purchase_cost_eur: float | None = None
    expected_sale_price_eur: float | None = None
    sale_price_eur: float | None = None
    sale_marketplace: str | None = None
    sale_date: datetime | None = None
    sale_fees_eur: float | None = None
    sale_shipping_eur: float | None = None
    sale_other_costs_eur: float | None = None
    notes: str | None = None


class DealOut(BaseModel):
    model_config = ORM
    id: int
    opportunity_id: int | None
    listing_id: int | None
    canonical_product_id: int | None
    title: str
    category_code: str | None
    source_marketplace: str | None
    source_country: str | None
    status: str
    purchase_price_eur: float | None
    purchase_date: datetime | None
    purchase_shipping_eur: float
    repair_cost_eur: float
    authentication_cost_eur: float
    other_purchase_cost_eur: float
    expected_sale_price_eur: float | None
    expected_profit_eur: float | None
    sale_price_eur: float | None
    sale_marketplace: str | None
    sale_date: datetime | None
    sale_fees_eur: float
    sale_shipping_eur: float
    sale_other_costs_eur: float
    notes: str
    created_at: datetime
    metrics: dict[str, Any] = {}


# ---------------------------------------------------------------------------- config
class CategoryIO(BaseModel):
    model_config = ORM
    code: str = Field(max_length=40)
    name: str
    group: str = "other"
    is_luxury: bool = False
    authentication_required: bool = False
    target_roi: float | None = None
    min_roi: float | None = None
    base_holding_days: float = 21
    refurbishment_eur: float = 0
    authentication_eur: float = 0
    shipping_class: str = "parcel_m"


class FeeRuleIO(BaseModel):
    model_config = ORM
    id: int | None = None
    marketplace_code: str | None = None
    country: str | None = None
    side: str = Field(pattern="^(buy|sell)$")
    category_code: str | None = None
    seller_type: str = "private"
    percent: float = Field(default=0, ge=0, le=1)
    fixed_eur: float = 0
    payment_percent: float = Field(default=0, ge=0, le=1)
    payment_fixed_eur: float = 0
    min_fee_eur: float | None = None
    max_fee_eur: float | None = None
    active: bool = True
    verified: bool = False
    source: str = ""
    notes: str = ""


class CostProfileIO(BaseModel):
    model_config = ORM
    id: int | None = None
    name: str
    category_code: str | None = None
    shipping_class: str | None = None
    route: str = Field(default="domestic", pattern="^(domestic|intra_eu|import)$")
    inbound_shipping_eur: float = 0
    outbound_shipping_eur: float = 0
    insurance_pct: float = 0
    import_duty_pct: float = 0
    import_vat_pct: float = 0
    misc_eur: float = 0
    misc_pct: float = 0
    travel_eur: float = 0
    active: bool = True
    notes: str = ""


class AlertRuleIO(BaseModel):
    model_config = ORM
    id: int | None = None
    name: str
    enabled: bool = True
    conditions: dict[str, Any]
    channels: list[str] = ["telegram", "email", "log"]
    include_price_drops: bool = True
    max_risk_level: str = Field(default="HIGH", pattern="^(LOW|MEDIUM|HIGH)$")


class AlertEventOut(BaseModel):
    model_config = ORM
    id: int
    listing_id: int
    opportunity_id: int | None
    rule_id: int | None
    channel: str
    kind: str
    status: str
    error: str | None
    message: str
    created_at: datetime


class ValuationOut(BaseModel):
    model_config = ORM
    id: int
    canonical_product_id: int
    variant_key: str
    market: str
    computed_at: datetime
    n_comparables: int
    n_sold: int
    n_outliers: int
    median_eur: float | None
    trimmed_mean_eur: float | None
    p25_eur: float | None
    p75_eur: float | None
    lowest_reasonable_eur: float | None
    quick_sale_eur: float | None
    market_value_eur: float | None
    opportunistic_buy_eur: float | None
    dispersion: float | None
    confidence_score: float
    confidence_level: str
    median_days_on_market: float | None
    details: dict[str, Any]
