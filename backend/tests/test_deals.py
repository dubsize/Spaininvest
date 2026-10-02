from datetime import UTC, datetime, timedelta

import pytest

from arbscan.db.models import Deal
from arbscan.services.deals import TransitionError, deal_metrics, portfolio_summary, set_deal_status

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def test_deal_metrics_sold():
    d = Deal(title="x", status="SOLD", purchase_price_eur=1000, purchase_date=NOW - timedelta(days=40),
             purchase_shipping_eur=20, repair_cost_eur=30, authentication_cost_eur=50, other_purchase_cost_eur=0,
             sale_price_eur=1400, sale_date=NOW - timedelta(days=10), sale_fees_eur=40, sale_shipping_eur=10, sale_other_costs_eur=0)
    m = deal_metrics(d, NOW)
    assert m.total_cost == 1100
    assert m.proceeds == 1350
    assert m.profit == 250
    assert m.roi == pytest.approx(250 / 1100)
    assert m.holding_days == pytest.approx(30)
    assert m.annualized_return == pytest.approx(250 / 1100 * 365 / 30)


def test_deal_transitions(db):
    d = Deal(title="x", status="PURCHASED", purchase_price_eur=100, purchase_date=NOW, purchase_shipping_eur=0,
             repair_cost_eur=0, authentication_cost_eur=0, other_purchase_cost_eur=0, sale_fees_eur=0, sale_shipping_eur=0, sale_other_costs_eur=0)
    db.add(d)
    db.flush()
    set_deal_status(db, d, "RECEIVED")
    with pytest.raises(TransitionError):
        set_deal_status(db, d, "SOLD")  # sale price required
    set_deal_status(db, d, "SOLD", {"sale_price_eur": 150})
    assert d.status == "SOLD"
    with pytest.raises(TransitionError):
        set_deal_status(db, d, "PURCHASED")


def test_portfolio_summary_on_demo(db):
    p = portfolio_summary(db, NOW)
    assert p["deals_sold"] >= 5 and p["inventory_count"] >= 3
    assert p["realized_profit"] > 0
    assert p["annualized_return_on_capital"] is not None
    assert set(p["inventory_aging"]) == {"0_30", "30_60", "60_90", "90_plus"}
    assert p["profit_by_category"] and p["profit_by_marketplace"] and p["profit_by_country"]
