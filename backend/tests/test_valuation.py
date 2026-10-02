from datetime import UTC, datetime, timedelta

import pytest

from arbscan.valuation.engine import Comparable, ValuationConfig, ValuationEngine
from arbscan.valuation.stats import (
    robust_outlier_mask,
    weighted_median,
    weighted_quantile,
    weighted_trimmed_mean,
)

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def comps(prices, **kw):
    return [Comparable(price_eur=p, listing_id=i, **kw) for i, p in enumerate(prices)]


def test_weighted_quantiles():
    assert weighted_median([1, 2, 3], [1, 1, 1]) == 2
    assert weighted_median([1, 2, 3], [1, 1, 10]) == pytest.approx(3, abs=0.6)
    assert weighted_quantile([10, 20, 30, 40], [1, 1, 1, 1], 0.0) == 10
    assert weighted_trimmed_mean([1, 100, 101, 102, 1000], [1] * 5, 0.2) == pytest.approx(101, abs=1)


def test_outlier_mask_removes_extremes():
    mask = robust_outlier_mask([100, 102, 98, 101, 99, 103, 97, 10, 1000])
    assert mask[-1] is False and mask[-2] is False
    assert all(mask[:7])


def test_not_a_simple_average():
    engine = ValuationEngine()
    res = engine.value(comps([1000, 1010, 990, 1005, 995, 1002, 998, 100, 9000], condition="good"), now=NOW)
    assert res.n_outliers == 2
    assert 900 < res.market_value_eur < 960  # ~1000 * ask_to_sale, outliers ignored
    assert res.quick_sale_eur <= res.market_value_eur
    assert res.p25_eur <= res.median_eur <= res.p75_eur
    assert res.lowest_reasonable_eur <= res.p25_eur


def test_sold_data_weighs_more_than_asks():
    engine = ValuationEngine()
    asks = comps([1200] * 6, kind="asking", condition="good")
    sold = [Comparable(price_eur=900, kind="sold", condition="good", listing_id=100 + i, observed_at=NOW) for i in range(4)]
    res = engine.value(asks + sold, now=NOW)
    # 4 sold x weight 3 = 12 > 6 asks -> median follows sold prices
    assert res.market_value_eur == pytest.approx(900, abs=1)
    assert res.n_sold == 4
    assert res.quick_sale_eur <= 900 * 0.95 + 1


def test_critical_attribute_mismatch_excluded_minor_downweighted():
    engine = ValuationEngine()
    yg = [Comparable(price_eur=5000, attributes={"material": "yellow_gold", "size": "17"}, listing_id=i) for i in range(5)]
    wg = [Comparable(price_eur=9000, attributes={"material": "white_gold"}, listing_id=10 + i) for i in range(5)]
    res = engine.value(yg + wg, target_attrs={"material": "yellow_gold", "size": "18"}, variant_importance={"material": 1.0, "size": 0.3}, now=NOW)
    assert res.n_excluded == 5
    assert res.n_comparables == 5
    assert res.market_value_eur < 5000


def test_condition_normalization():
    engine = ValuationEngine()
    base = comps([1000] * 8, condition="good")
    new_target = engine.value(base, target_condition="new", now=NOW)
    fair_target = engine.value(base, target_condition="fair", now=NOW)
    assert new_target.market_value_eur > fair_target.market_value_eur


def test_stale_asks_downweighted():
    engine = ValuationEngine()
    fresh = [Comparable(price_eur=1000, days_on_market=5, listing_id=i) for i in range(5)]
    stale = [Comparable(price_eur=1400, days_on_market=150, listing_id=10 + i) for i in range(5)]
    res = engine.value(fresh + stale, now=NOW)
    assert res.market_value_eur < 1000 * 0.93 * 1.2


def test_other_country_downweighted():
    engine = ValuationEngine(ValuationConfig(other_country_weight=0.2))
    es = [Comparable(price_eur=1000, country="ES", listing_id=i) for i in range(4)]
    fr = [Comparable(price_eur=800, country="FR", listing_id=10 + i) for i in range(4)]
    res = engine.value(es + fr, market="ES", now=NOW)
    assert res.market_value_eur > 0.93 * 900
    assert set(res.by_country) == {"ES", "FR"}


def test_confidence_levels_reflect_data_quality():
    engine = ValuationEngine()
    few = engine.value(comps([1000, 1050]), now=NOW)
    assert few.confidence_level == "INSUFFICIENT"
    low = engine.value(comps([1000, 1500, 700, 1200]), now=NOW)
    assert low.confidence_level in ("LOW", "MEDIUM")
    many = engine.value(comps([1000 + (i % 7) * 10 for i in range(37)]), now=NOW)
    assert many.confidence_level == "HIGH"
    assert many.n_comparables == 37
    assert many.confidence_score > low.confidence_score


def test_excludes_target_listing_itself():
    engine = ValuationEngine()
    res = engine.value(comps([1000, 1000, 1000, 100]), exclude_listing_id=3, now=NOW)
    assert res.n_comparables == 3


def test_for_parts_excluded():
    engine = ValuationEngine()
    res = engine.value(comps([1000] * 3) + [Comparable(price_eur=200, condition="for_parts", listing_id=99)], now=NOW)
    assert res.n_excluded == 1


def test_median_days_on_market_from_ended_listings():
    engine = ValuationEngine()
    cs = [Comparable(price_eur=1000, kind="ended", is_active=False, days_on_market=d, listing_id=i, observed_at=NOW - timedelta(days=d)) for i, d in enumerate([3, 5, 7, 9, 11])]
    res = engine.value(cs, now=NOW)
    assert res.median_days_on_market == 7
