import pytest

from arbscan.fees.engine import (
    CategoryCosts,
    CostProfileData,
    FeeEngine,
    FeeRuleData,
    TradeContext,
    max_buy_price_simple,
)


@pytest.fixture
def engine():
    rules = [
        FeeRuleData(side="sell", marketplace_code=None, percent=0.05),
        FeeRuleData(side="sell", marketplace_code="ebay_es", percent=0.12, fixed_eur=0.35),
        FeeRuleData(side="sell", marketplace_code="ebay_es", category_code="luxury_watches", percent=0.06),
        FeeRuleData(side="sell", marketplace_code="vestiaire", percent=0.15, payment_percent=0.03, min_fee_eur=15),
        FeeRuleData(side="buy", marketplace_code="wallapop", percent=0.05, fixed_eur=0.99),
        FeeRuleData(side="sell", marketplace_code="wallapop", percent=0.0),
    ]
    profiles = [
        CostProfileData(route="domestic", shipping_class="parcel_m", inbound_shipping_eur=6),
        CostProfileData(route="intra_eu", shipping_class="parcel_m", inbound_shipping_eur=18),
        CostProfileData(route="domestic", inbound_shipping_eur=8),
        CostProfileData(route="import", inbound_shipping_eur=40, import_duty_pct=0.03, import_vat_pct=0.21, misc_eur=20),
        CostProfileData(route="intra_eu", category_code="luxury_jewelry", inbound_shipping_eur=35, insurance_pct=0.01),
    ]
    return FeeEngine(rules, profiles)


def cat(code="kitchen_appliances", **kw):
    return CategoryCosts(code=code, shipping_class=kw.pop("shipping_class", "parcel_m"), **kw)


def test_most_specific_rule_wins(engine):
    assert engine.fee_rule("sell", "ebay_es", "ES", "luxury_watches").percent == 0.06
    assert engine.fee_rule("sell", "ebay_es", "ES", "cameras").percent == 0.12
    assert engine.fee_rule("sell", "unknown", "ES", None).percent == 0.05


def test_min_fee_applies(engine):
    fee, pay = engine.fee_rule("sell", "vestiaire", None, None).compute(50)
    assert fee == 15 and pay == 1.5


def test_routes(engine):
    assert engine.route("ES", "ES") == "domestic"
    assert engine.route("FR", "ES") == "intra_eu"
    assert engine.route("GB", "ES") == "import"


def test_economics_domestic_flip(engine):
    ctx = TradeContext("wallapop", "ES", "wallapop", "ES", cat(refurbishment_eur=15))
    e = engine.economics(450, 625, ctx)
    # buyer fee 0.05*450+0.99 = 23.49, shipping 6, refurb 15
    assert e.capital == pytest.approx(450 + 23.49 + 6 + 15, abs=0.01)
    assert e.net_profit == pytest.approx(625 - e.capital, abs=0.01)
    assert e.roi == pytest.approx(e.net_profit / e.capital, abs=1e-3)


def test_cross_border_costs(engine):
    ctx = TradeContext("leboncoin", "FR", "wallapop", "ES", cat("luxury_jewelry", authentication_required=True, authentication_eur=80, shipping_class="insured_small"))
    e = engine.economics(1800, 2500, ctx)
    labels = {line.label for line in e.costs.lines}
    assert {"Inbound shipping", "Transport insurance", "Authentication"} <= labels
    assert e.net_profit < 700


def test_import_vat_and_duty(engine):
    ctx = TradeContext("manual", "GB", "wallapop", "ES", cat())
    bd = engine.costs(1000, 1500, ctx)
    vat = next(line for line in bd.lines if line.label == "Import VAT")
    duty = next(line for line in bd.lines if line.label == "Import duty")
    assert duty.amount == pytest.approx(1040 * 0.03, abs=0.01)
    assert vat.amount == pytest.approx((1040 + 31.2) * 0.21, abs=0.05)


def test_listing_shipping_overrides_profile(engine):
    ctx = TradeContext("ebay_es", "ES", "wallapop", "ES", cat(), listing_shipping_eur=4.99)
    line = next(l for l in engine.costs(100, 200, ctx).lines if l.label == "Inbound shipping")
    assert line.amount == 4.99


def test_max_buy_price_satisfies_target_roi(engine):
    ctx = TradeContext("wallapop", "ES", "ebay_es", "ES", cat(refurbishment_eur=10))
    mbp = engine.max_buy_price(1000, ctx, target_roi=0.25)
    e = engine.economics(mbp, 1000, ctx)
    assert e.roi >= 0.25 - 1e-3
    assert engine.economics(mbp + 10, 1000, ctx).roi < 0.25


def test_max_buy_price_with_min_profit(engine):
    ctx = TradeContext("wallapop", "ES", "wallapop", "ES", cat())
    mbp = engine.max_buy_price(300, ctx, target_roi=0.05, min_profit_eur=100)
    assert engine.economics(mbp, 300, ctx).net_profit >= 99


def test_spec_example_closed_form():
    # quick resale 1000, ROI 25 %, costs 100 -> 720
    assert max_buy_price_simple(1000, 100, 0.25) == pytest.approx(720)
