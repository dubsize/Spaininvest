from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from arbscan.connectors.base import RawListing
from arbscan.db.models import Listing, ListingPriceHistory, Opportunity
from arbscan.services.pipeline import Evaluator, ingest_raw_listing


def raw(**kw):
    d = dict(marketplace="wallapop", external_id="t-1", url="https://es.wallapop.com/item/t-1", title="Thermomix TM6 como nuevo",
             price=520.0, country="ES", city="Madrid", description="Con varoma. Envío disponible.", seller_rating=4.8,
             seller_rating_count=40, image_urls=["https://img.example/a.jpg", "https://img.example/b.jpg", "https://img.example/c.jpg", "https://img.example/d.jpg"])
    d.update(kw)
    return RawListing(**d)


def test_demo_data_is_rich(db):
    n = db.scalar(select(func.count(Listing.id)).where(Listing.is_demo.is_(True)))
    assert n >= 100
    mps = {m for (m,) in db.execute(select(Listing.marketplace_code).distinct())}
    assert {"wallapop", "leboncoin", "ebay_es", "ebay_fr", "ebay_de"} <= mps
    scenarios = {l.source_metadata.get("demo_scenario") for l in db.scalars(select(Listing).where(Listing.is_demo.is_(True)))}
    assert {"normal", "bargain", "overpriced", "scam", "negotiation", "price_drop"} <= scenarios
    types = {t for (t,) in db.execute(select(Opportunity.opportunity_type).distinct())}
    assert {"FLIP", "NEGOTIATION"} <= types
    assert db.scalar(select(func.count(Opportunity.id)).where(Opportunity.risk_level == "HIGH")) > 0


def test_ingest_and_price_history_append_only(db):
    t0 = datetime(2026, 9, 1, tzinfo=UTC)
    r1 = ingest_raw_listing(db, raw(price=1500.0, external_id="hist-1"), now=t0)
    assert r1.created and r1.listing.canonical_product_id is not None
    same = ingest_raw_listing(db, raw(price=1500.0, external_id="hist-1"), now=t0 + timedelta(days=1))
    assert not same.updated and not same.price_changed
    d20 = ingest_raw_listing(db, raw(price=1350.0, external_id="hist-1"), now=t0 + timedelta(days=20))
    d45 = ingest_raw_listing(db, raw(price=1150.0, external_id="hist-1"), now=t0 + timedelta(days=45))
    assert d20.price_changed and d45.price_changed
    assert round(d45.price_change_pct, 3) == round(1150 / 1350 - 1, 3)
    hist = db.scalars(select(ListingPriceHistory).where(ListingPriceHistory.listing_id == r1.listing.id).order_by(ListingPriceHistory.observed_at)).all()
    assert [h.price_eur for h in hist] == [1500, 1350, 1150]
    assert [h.change_type for h in hist] == ["initial", "drop", "drop"]
    assert r1.listing.price_drop_count == 2


def test_currency_normalisation(db):
    r = ingest_raw_listing(db, raw(external_id="gbp-1", price=1000.0, currency="GBP", country="GB"))
    l = r.listing
    assert l.currency == "GBP" and l.price_amount == 1000
    assert l.price_eur > 1000 and l.fx_rate > 1 and l.fx_timestamp is not None


def test_unknown_marketplace_maps_to_manual(db):
    r = ingest_raw_listing(db, raw(marketplace="some_new_site", external_id="x-1"))
    assert r.listing.marketplace_code == "manual"
    assert r.listing.source_metadata["declared_marketplace"] == "some_new_site"


def test_evaluate_produces_full_opportunity(db):
    r = ingest_raw_listing(db, raw(external_id="eval-1", price=430.0))
    opps = Evaluator(db).evaluate(r.listing)
    assert len(opps) == 1
    o = opps[0]
    assert o.resale_country == "ES"
    assert o.market_value_eur and o.quick_sale_eur and o.quick_sale_eur <= o.market_value_eur
    assert o.max_buy_price_eur is not None
    assert o.risk_level in ("LOW", "MEDIUM", "HIGH")
    assert set(o.score_components) >= {"discount", "profit", "roi", "liquidity", "freshness", "confidence", "velocity"}
    assert o.cost_breakdown["lines"]


def test_cross_border_detected(db):
    r = ingest_raw_listing(db, raw(marketplace="leboncoin", external_id="fr-1", country="FR", city="Paris",
                                   title="Thermomix TM6 comme neuf", description="Très bon état, avec facture.", price=380.0))
    o = Evaluator(db).evaluate(r.listing)[0]
    assert o.source_country == "FR" and o.resale_country == "ES"
    assert o.opportunity_type == "CROSS_BORDER"
    assert o.cost_breakdown["route"] == "intra_eu"


def test_html_in_scraped_content_is_sanitized(db):
    r = ingest_raw_listing(db, raw(external_id="xss-1", title="<img src=x onerror=alert(1)>Thermomix TM6", description="<script>alert(1)</script>ok"))
    assert "<" not in r.listing.title and "<script>" not in r.listing.description
