import pytest

from arbscan.scoring.engine import (
    LiquidityInput,
    ScoreInput,
    ScoringConfig,
    achievable_discount,
    classify_opportunity,
    compute_score,
    estimate_liquidity,
    nice_round,
    velocity_metrics,
)
from arbscan.scoring.offer import OfferInput, calculate_offer


def base_input(**kw):
    d = dict(
        purchase_price=2850, market_value=4050, quick_sale=3750, net_profit=720, roi=0.238, liquidity_score=80,
        listing_age_hours=0.2, valuation_confidence_score=0.9, valuation_confidence_level="HIGH",
        normalization_confidence=0.96, risk_score=20, risk_level="MEDIUM", annualized_roi=4.0,
    )
    d.update(kw)
    return ScoreInput(**d)


def test_score_components_returned():
    r = compute_score(base_input())
    assert 0 <= r.score <= 100
    for k in ("discount", "profit", "roi", "liquidity", "freshness", "confidence", "velocity", "risk_penalty"):
        assert k in r.components
    assert r.score > 60


def test_fresh_listing_ranks_above_old_equivalent():
    fresh = compute_score(base_input(listing_age_hours=5 / 60))
    old = compute_score(base_input(listing_age_hours=21 * 24))
    assert fresh.score > old.score


def test_exact_match_ranks_above_uncertain():
    sure = compute_score(base_input(normalization_confidence=0.97))
    unsure = compute_score(base_input(normalization_confidence=0.4))
    assert sure.score > unsure.score


def test_caps():
    assert compute_score(base_input(risk_level="HIGH", risk_score=10)).score <= 60
    assert compute_score(base_input(valuation_confidence_level="LOW")).score <= 72
    assert compute_score(base_input(valuation_confidence_level="INSUFFICIENT")).score <= 35
    assert compute_score(base_input(net_profit=-10)).score <= 25


def test_risk_penalizes():
    assert compute_score(base_input(risk_score=0, risk_level="LOW")).score > compute_score(base_input(risk_score=40)).score


def test_weights_configurable():
    cfg = ScoringConfig.from_dict({"weights": {"discount": 1.0, "profit": 0, "roi": 0, "liquidity": 0, "freshness": 0, "confidence": 0, "velocity": 0}})
    r = compute_score(base_input(risk_score=0), cfg)
    assert r.score == pytest.approx(r.components["discount"], abs=0.2)


def test_velocity_prefers_fast_small_capital():
    small_fast = velocity_metrics(100, 300, 5)
    big_slow = velocity_metrics(600, 5000, 180)
    assert small_fast.annualized_roi > big_slow.annualized_roi
    assert small_fast.capital_efficiency > big_slow.capital_efficiency
    assert small_fast.profit_velocity == pytest.approx(20)
    assert small_fast.profit_per_1000 == pytest.approx(333.33, abs=0.01)
    s1 = compute_score(base_input(net_profit=100, roi=0.333, annualized_roi=small_fast.annualized_roi, purchase_price=300, market_value=450, quick_sale=420))
    s2 = compute_score(base_input(net_profit=600, roi=0.12, annualized_roi=big_slow.annualized_roi, purchase_price=5000, market_value=5800, quick_sale=5650))
    assert s1.components["velocity"] > s2.components["velocity"]


def test_liquidity_labels():
    high = estimate_liquidity(LiquidityInput(n_active_comparables=30, n_sold_recent=12, median_days_on_market=5, popularity=0.95))
    low = estimate_liquidity(LiquidityInput(n_active_comparables=2, n_sold_recent=0, median_days_on_market=80, popularity=0.3))
    assert high.label == "High" and low.label == "Low"
    assert high.expected_holding_days_quick < low.expected_holding_days_quick


def test_negotiation_opportunity_spec_example():
    # market 1500, seller asks 1650, 70 days old
    kind, target, reason = classify_opportunity(
        asking=1650, max_buy_price=1190, market_value=1500, net_profit_at_ask=-150, roi_at_ask=-0.1, min_roi=0.15,
        source_country="ES", resale_country="ES", listing_age_days=70, price_drops=1,
    )
    assert kind == "NEGOTIATION"
    assert target is not None and target <= 1190
    assert "70 days" in reason


def test_classification_flip_and_cross_border():
    common = dict(asking=500, max_buy_price=560, market_value=700, net_profit_at_ask=120, roi_at_ask=0.24, min_roi=0.15, listing_age_days=0.1, price_drops=0)
    assert classify_opportunity(source_country="ES", resale_country="ES", **common)[0] == "FLIP"
    assert classify_opportunity(source_country="FR", resale_country="ES", **common)[0] == "CROSS_BORDER"


def test_fresh_overpriced_listing_is_not_negotiation():
    kind, _, _ = classify_opportunity(
        asking=2000, max_buy_price=1100, market_value=1500, net_profit_at_ask=-400, roi_at_ask=-0.2, min_roi=0.15,
        source_country="ES", resale_country="ES", listing_age_days=2, price_drops=0,
    )
    assert kind == "NONE"


def test_achievable_discount_grows_with_age():
    assert achievable_discount(90, 2) > achievable_discount(5, 0)
    assert achievable_discount(1000, 10) <= ScoringConfig().negotiation_max_discount


def test_nice_round():
    assert nice_round(2987) == 2980
    assert nice_round(6123) == 6100
    assert nice_round(437) == 430
    assert nice_round(52) == 50
    assert nice_round(47) == 47


def test_offer_calculator_simple_costs():
    r = calculate_offer(OfferInput(asking_price=3500, expected_resale=3850, target_roi=0.20, expected_costs_eur=180))
    assert r.max_acceptable_offer <= (3850 - 180) / 1.2
    assert r.ideal_offer <= r.max_acceptable_offer
    assert not r.deal_at_ask
    assert r.expected_profit_at_max >= 0


def test_offer_calculator_target_profit_binds():
    r = calculate_offer(OfferInput(asking_price=500, expected_resale=700, target_roi=0.05, target_profit_eur=200, expected_costs_eur=20))
    assert r.max_acceptable_offer <= 480
