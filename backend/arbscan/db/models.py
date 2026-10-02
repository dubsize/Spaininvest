"""SQLAlchemy ORM models.

Conventions
-----------
* All money columns hold EUR unless the column name says otherwise (``*_amount`` is the
  original-currency value, ``*_eur`` is the normalised value).
* Historical data (prices, valuations, scans, alerts, status changes) is append-only.
* Enum-like columns are strings; see :mod:`arbscan.db.enums`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

JSONType = JSON().with_variant(JSONB(), "postgresql")


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every backend (SQLite returns naive values)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value
Money = Numeric(12, 2, asdecimal=False)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONType, list[Any]: JSONType}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


class Marketplace(TimestampMixin, Base):
    __tablename__ = "marketplaces"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2))
    base_url: Mapped[str] = mapped_column(String(255), default="")
    connector_key: Mapped[str] = mapped_column(String(40))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="STUB")
    supports_sold_data: Mapped[bool] = mapped_column(Boolean, default=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=900)
    max_requests_per_minute: Mapped[int] = mapped_column(Integer, default=10)
    last_run_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_success_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_error_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_error: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    total_listings_collected: Mapped[int] = mapped_column(Integer, default=0)
    compliance_notes: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[dict[str, Any]] = mapped_column(default=dict)


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    group: Mapped[str] = mapped_column(String(40), default="other")  # luxury / electronics / ...
    is_luxury: Mapped[bool] = mapped_column(Boolean, default=False)
    authentication_required: Mapped[bool] = mapped_column(Boolean, default=False)
    target_roi: Mapped[float | None] = mapped_column(Float)  # overrides global default
    min_roi: Mapped[float | None] = mapped_column(Float)
    base_holding_days: Mapped[float] = mapped_column(Float, default=21)
    refurbishment_eur: Mapped[float] = mapped_column(Money, default=0)
    authentication_eur: Mapped[float] = mapped_column(Money, default=0)
    shipping_class: Mapped[str] = mapped_column(String(20), default="parcel_m")


class CanonicalProduct(TimestampMixin, Base):
    __tablename__ = "canonical_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(120))
    collection: Mapped[str | None] = mapped_column(String(120))
    product_type: Mapped[str | None] = mapped_column(String(80))
    category_code: Mapped[str] = mapped_column(ForeignKey("categories.code"), index=True)
    # attribute name -> importance (0..1). >=0.8 means a mismatch excludes the comparable.
    variant_attributes: Mapped[dict[str, Any]] = mapped_column(default=dict)
    brand_aliases: Mapped[list[Any]] = mapped_column(default=list)
    aliases: Mapped[list[Any]] = mapped_column(default=list)
    patterns: Mapped[list[Any]] = mapped_column(default=list)  # regexes (case-insensitive)
    # product-specific attribute extractors: {attr: [{"pattern": "...", "value": "..."}]}
    attribute_rules: Mapped[dict[str, Any]] = mapped_column(default=dict)
    reference_numbers: Mapped[list[Any]] = mapped_column(default=list)
    required_keywords: Mapped[list[Any]] = mapped_column(default=list)  # any-of
    excluded_keywords: Mapped[list[Any]] = mapped_column(default=list)
    retail_price_eur: Mapped[float | None] = mapped_column(Money)
    popularity: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1 prior
    typical_holding_days: Mapped[float | None] = mapped_column(Float)
    refurbishment_eur: Mapped[float | None] = mapped_column(Money)
    target_roi: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    category: Mapped[Category] = relationship(lazy="joined")


class Watchlist(TimestampMixin, Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    keyword: Mapped[str] = mapped_column(String(200), default="")
    canonical_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL")
    )
    category_code: Mapped[str | None] = mapped_column(ForeignKey("categories.code", ondelete="SET NULL"))
    brands: Mapped[list[Any]] = mapped_column(default=list)
    countries: Mapped[list[Any]] = mapped_column(default=list)
    marketplaces: Mapped[list[Any]] = mapped_column(default=list)
    max_price_eur: Mapped[float | None] = mapped_column(Money)
    min_discount: Mapped[float | None] = mapped_column(Float)
    min_profit_eur: Mapped[float | None] = mapped_column(Money)
    min_roi: Mapped[float | None] = mapped_column(Float)
    min_score: Mapped[float | None] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(20), default="standard")
    scan_interval_minutes: Mapped[int | None] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    next_scan_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    canonical_product: Mapped[CanonicalProduct | None] = relationship(lazy="joined")


# ---------------------------------------------------------------------------
# Listings & history
# ---------------------------------------------------------------------------


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("marketplace_code", "external_id", name="uq_listing_marketplace_external"),
        Index("ix_listings_product_status", "canonical_product_id", "status"),
        Index("ix_listings_country", "country"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_code: Mapped[str] = mapped_column(ForeignKey("marketplaces.code"), index=True)
    external_id: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str | None] = mapped_column(String(5))

    # price (original currency + normalised EUR)
    price_amount: Mapped[float] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    price_eur: Mapped[float] = mapped_column(Money, index=True)
    fx_rate: Mapped[float] = mapped_column(Float, default=1.0)  # EUR per unit of `currency`
    fx_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime())
    original_price_amount: Mapped[float | None] = mapped_column(Money)  # strike-through price
    original_price_eur: Mapped[float | None] = mapped_column(Money)
    price_kind: Mapped[str] = mapped_column(String(10), default="asking")  # asking | sold
    sold_price_eur: Mapped[float | None] = mapped_column(Money)
    sold_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    # location
    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2))

    # seller (only when publicly available)
    seller_id: Mapped[str | None] = mapped_column(String(120), index=True)
    seller_name: Mapped[str | None] = mapped_column(String(200))
    seller_rating: Mapped[float | None] = mapped_column(Float)  # normalised 0..5
    seller_rating_count: Mapped[int | None] = mapped_column(Integer)
    seller_account_created_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    seller_type: Mapped[str | None] = mapped_column(String(20))  # private | professional
    seller_listing_count: Mapped[int | None] = mapped_column(Integer)

    # item
    condition_raw: Mapped[str | None] = mapped_column(String(120))
    condition: Mapped[str] = mapped_column(String(20), default="unknown")
    category_raw: Mapped[str | None] = mapped_column(String(200))
    brand_raw: Mapped[str | None] = mapped_column(String(120))
    model_raw: Mapped[str | None] = mapped_column(String(200))
    shipping_available: Mapped[bool | None] = mapped_column(Boolean)
    shipping_cost_eur: Mapped[float | None] = mapped_column(Money)
    image_urls: Mapped[list[Any]] = mapped_column(default=list)
    image_hashes: Mapped[list[Any]] = mapped_column(default=list)

    # lifecycle
    status: Mapped[str] = mapped_column(String(12), default="active")
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    first_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    price_drop_count: Mapped[int] = mapped_column(Integer, default=0)
    last_price_change_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_price_change_pct: Mapped[float | None] = mapped_column(Float)

    # normalisation
    canonical_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL"), index=True
    )
    detected_brand: Mapped[str | None] = mapped_column(String(80))
    detected_model: Mapped[str | None] = mapped_column(String(160))
    variant: Mapped[dict[str, Any]] = mapped_column(default=dict)
    variant_key: Mapped[str] = mapped_column(String(255), default="")
    detected_size: Mapped[str | None] = mapped_column(String(40))
    detected_material: Mapped[str | None] = mapped_column(String(60))
    accessories: Mapped[dict[str, Any]] = mapped_column(default=dict)  # box, papers, receipt, ...
    authenticity_info: Mapped[str | None] = mapped_column(Text)
    normalization_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    normalization_method: Mapped[str | None] = mapped_column(String(40))
    normalization_details: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # provenance
    source: Mapped[str] = mapped_column(String(20), default="connector")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    marketplace: Mapped[Marketplace] = relationship(lazy="joined")
    canonical_product: Mapped[CanonicalProduct | None] = relationship(lazy="joined")
    price_history: Mapped[list[ListingPriceHistory]] = relationship(
        back_populates="listing", order_by="ListingPriceHistory.observed_at", cascade="all, delete-orphan"
    )


class ListingPriceHistory(Base):
    __tablename__ = "listing_price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    price_amount: Mapped[float] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3))
    price_eur: Mapped[float] = mapped_column(Money)
    fx_rate: Mapped[float] = mapped_column(Float, default=1.0)
    change_type: Mapped[str] = mapped_column(String(12), default="initial")  # initial|drop|increase
    change_pct: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)

    listing: Mapped[Listing] = relationship(back_populates="price_history")


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), index=True)
    eur_per_unit: Mapped[float] = mapped_column(Float)
    as_of: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    source: Mapped[str] = mapped_column(String(60), default="static")


# ---------------------------------------------------------------------------
# Valuations, opportunities
# ---------------------------------------------------------------------------


class Valuation(Base):
    """Append-only market value snapshot for (product, variant, market)."""

    __tablename__ = "valuations"
    __table_args__ = (Index("ix_valuations_lookup", "canonical_product_id", "variant_key", "market", "computed_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_product_id: Mapped[int] = mapped_column(ForeignKey("canonical_products.id", ondelete="CASCADE"))
    variant_key: Mapped[str] = mapped_column(String(255), default="")
    market: Mapped[str] = mapped_column(String(4))  # ISO country or "EU"
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    n_comparables: Mapped[int] = mapped_column(Integer)
    n_sold: Mapped[int] = mapped_column(Integer, default=0)
    n_outliers: Mapped[int] = mapped_column(Integer, default=0)
    median_eur: Mapped[float | None] = mapped_column(Money)
    trimmed_mean_eur: Mapped[float | None] = mapped_column(Money)
    p25_eur: Mapped[float | None] = mapped_column(Money)
    p75_eur: Mapped[float | None] = mapped_column(Money)
    lowest_reasonable_eur: Mapped[float | None] = mapped_column(Money)
    quick_sale_eur: Mapped[float | None] = mapped_column(Money)
    market_value_eur: Mapped[float | None] = mapped_column(Money)
    opportunistic_buy_eur: Mapped[float | None] = mapped_column(Money)
    dispersion: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_level: Mapped[str] = mapped_column(String(14), default="INSUFFICIENT")
    median_days_on_market: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict[str, Any]] = mapped_column(default=dict)


class Opportunity(TimestampMixin, Base):
    """Evaluation of one listing against one resale market. Recomputed in place;
    material changes are tracked through ``fingerprint`` (used for alert dedup)."""

    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("listing_id", "resale_country", name="uq_opportunity_listing_market"),
        Index("ix_opp_score", "score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    canonical_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL"), index=True
    )
    valuation_id: Mapped[int | None] = mapped_column(ForeignKey("valuations.id", ondelete="SET NULL"))
    opportunity_type: Mapped[str] = mapped_column(String(14), index=True)
    resale_country: Mapped[str] = mapped_column(String(2))
    source_country: Mapped[str] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="DISCOVERED", index=True)

    purchase_price_eur: Mapped[float] = mapped_column(Money)
    quick_sale_eur: Mapped[float | None] = mapped_column(Money)
    market_value_eur: Mapped[float | None] = mapped_column(Money)
    buy_costs_eur: Mapped[float] = mapped_column(Money, default=0)
    sell_costs_eur: Mapped[float] = mapped_column(Money, default=0)
    total_costs_eur: Mapped[float] = mapped_column(Money, default=0)
    cost_breakdown: Mapped[dict[str, Any]] = mapped_column(default=dict)
    net_profit_quick_eur: Mapped[float | None] = mapped_column(Money, index=True)
    net_profit_market_eur: Mapped[float | None] = mapped_column(Money)
    roi: Mapped[float | None] = mapped_column(Float, index=True)
    discount_pct: Mapped[float | None] = mapped_column(Float)
    max_buy_price_eur: Mapped[float | None] = mapped_column(Money)
    target_offer_eur: Mapped[float | None] = mapped_column(Money)
    profit_at_target_offer_eur: Mapped[float | None] = mapped_column(Money)

    expected_holding_days: Mapped[float | None] = mapped_column(Float)
    annualized_roi: Mapped[float | None] = mapped_column(Float)
    profit_velocity: Mapped[float | None] = mapped_column(Float)  # EUR / day
    capital_efficiency: Mapped[float | None] = mapped_column(Float)  # profit / cost / day
    profit_per_1000: Mapped[float | None] = mapped_column(Float)

    liquidity_score: Mapped[float | None] = mapped_column(Float)
    liquidity_label: Mapped[str | None] = mapped_column(String(10))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    confidence_level: Mapped[str | None] = mapped_column(String(14))
    normalization_confidence: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(8), default="LOW", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    risk_flags: Mapped[list[Any]] = mapped_column(default=list)
    requires_authentication: Mapped[bool] = mapped_column(Boolean, default=False)

    score: Mapped[float] = mapped_column(Float, default=0)
    score_components: Mapped[dict[str, Any]] = mapped_column(default=dict)
    explanation: Mapped[list[Any]] = mapped_column(default=list)
    fingerprint: Mapped[str] = mapped_column(String(64), default="")
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    listing: Mapped[Listing] = relationship(lazy="joined")
    canonical_product: Mapped[CanonicalProduct | None] = relationship(lazy="joined")


# ---------------------------------------------------------------------------
# Fees & costs (configuration, editable in UI)
# ---------------------------------------------------------------------------


class FeeRule(TimestampMixin, Base):
    """Marketplace fee rule. The most specific active rule wins
    (marketplace+category > marketplace > country default)."""

    __tablename__ = "fee_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_code: Mapped[str | None] = mapped_column(String(40), index=True)
    country: Mapped[str | None] = mapped_column(String(2))
    side: Mapped[str] = mapped_column(String(4))  # sell | buy
    category_code: Mapped[str | None] = mapped_column(String(40))
    seller_type: Mapped[str] = mapped_column(String(20), default="private")
    percent: Mapped[float] = mapped_column(Float, default=0)
    fixed_eur: Mapped[float] = mapped_column(Money, default=0)
    payment_percent: Mapped[float] = mapped_column(Float, default=0)
    payment_fixed_eur: Mapped[float] = mapped_column(Money, default=0)
    min_fee_eur: Mapped[float | None] = mapped_column(Money)
    max_fee_eur: Mapped[float | None] = mapped_column(Money)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")


class CostProfile(TimestampMixin, Base):
    """Logistics cost assumptions per route (domestic | intra_eu | import) and
    shipping class or category. Most specific match wins (category > shipping class > default)."""

    __tablename__ = "cost_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category_code: Mapped[str | None] = mapped_column(String(40))
    shipping_class: Mapped[str | None] = mapped_column(String(20))
    route: Mapped[str] = mapped_column(String(12), default="domestic")
    inbound_shipping_eur: Mapped[float] = mapped_column(Money, default=0)
    outbound_shipping_eur: Mapped[float] = mapped_column(Money, default=0)
    insurance_pct: Mapped[float] = mapped_column(Float, default=0)
    import_duty_pct: Mapped[float] = mapped_column(Float, default=0)
    import_vat_pct: Mapped[float] = mapped_column(Float, default=0)
    misc_eur: Mapped[float] = mapped_column(Money, default=0)
    misc_pct: Mapped[float] = mapped_column(Float, default=0)
    travel_eur: Mapped[float] = mapped_column(Money, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(default=dict)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


class AlertRule(TimestampMixin, Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # {"any": [ {"all": [{"field": "score", "op": ">=", "value": 80}]}, ...]}
    conditions: Mapped[dict[str, Any]] = mapped_column(default=dict)
    channels: Mapped[list[Any]] = mapped_column(default=list)
    include_price_drops: Mapped[bool] = mapped_column(Boolean, default=True)
    max_risk_level: Mapped[str] = mapped_column(String(8), default="HIGH")


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        UniqueConstraint("listing_id", "channel", "fingerprint", name="uq_alert_dedup"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("alert_rules.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20), default="deal")  # deal | price_drop
    fingerprint: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(12), default="sent")  # sent | failed | skipped
    error: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)


# ---------------------------------------------------------------------------
# Scanner observability
# ---------------------------------------------------------------------------


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_code: Mapped[str] = mapped_column(String(40), index=True)
    watchlist_id: Mapped[int | None] = mapped_column(ForeignKey("watchlists.id", ondelete="SET NULL"))
    query: Mapped[str] = mapped_column(String(300), default="")
    kind: Mapped[str] = mapped_column(String(20), default="search")  # search | refresh | analysis
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), default="running")  # running|success|error|skipped
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    listings_new: Mapped[int] = mapped_column(Integer, default=0)
    listings_updated: Mapped[int] = mapped_column(Integer, default=0)
    price_changes: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0)
    alerts_sent: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(default=dict)


# ---------------------------------------------------------------------------
# Deal tracker
# ---------------------------------------------------------------------------


class Deal(TimestampMixin, Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listings.id", ondelete="SET NULL"))
    canonical_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500))
    category_code: Mapped[str | None] = mapped_column(String(40))
    source_marketplace: Mapped[str | None] = mapped_column(String(40))
    source_country: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(20), default="PURCHASED", index=True)

    # purchase
    purchase_price_eur: Mapped[float | None] = mapped_column(Money)
    purchase_date: Mapped[datetime | None] = mapped_column(UTCDateTime())
    purchase_shipping_eur: Mapped[float] = mapped_column(Money, default=0)
    repair_cost_eur: Mapped[float] = mapped_column(Money, default=0)
    authentication_cost_eur: Mapped[float] = mapped_column(Money, default=0)
    other_purchase_cost_eur: Mapped[float] = mapped_column(Money, default=0)
    expected_sale_price_eur: Mapped[float | None] = mapped_column(Money)
    expected_profit_eur: Mapped[float | None] = mapped_column(Money)

    # sale
    sale_price_eur: Mapped[float | None] = mapped_column(Money)
    sale_marketplace: Mapped[str | None] = mapped_column(String(40))
    sale_date: Mapped[datetime | None] = mapped_column(UTCDateTime())
    sale_fees_eur: Mapped[float] = mapped_column(Money, default=0)
    sale_shipping_eur: Mapped[float] = mapped_column(Money, default=0)
    sale_other_costs_eur: Mapped[float] = mapped_column(Money, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class StatusEvent(Base):
    """Audit trail for opportunity/deal status transitions."""

    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(20))  # opportunity | deal
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
