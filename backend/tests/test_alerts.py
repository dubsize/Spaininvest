from sqlalchemy import func, select

from arbscan.alerts.channels import AlertMessage, Channel
from arbscan.alerts.service import AlertDispatcher, format_alert, opportunity_fields, rule_matches
from arbscan.db.models import AlertEvent, AlertRule, Opportunity

DEFAULT = {
    "any": [
        {"all": [{"field": "score", "op": ">=", "value": 80}]},
        {"all": [{"field": "net_profit", "op": ">=", "value": 250}, {"field": "roi", "op": ">=", "value": 0.20}]},
        {"all": [{"field": "price_to_quick_sale", "op": "<=", "value": 0.70}]},
    ]
}


def test_default_rule_semantics():
    assert rule_matches(DEFAULT, {"score": 85})
    assert rule_matches(DEFAULT, {"score": 50, "net_profit": 300, "roi": 0.25})
    assert not rule_matches(DEFAULT, {"score": 50, "net_profit": 300, "roi": 0.10})
    assert rule_matches(DEFAULT, {"score": 10, "price_to_quick_sale": 0.65})
    assert not rule_matches(DEFAULT, {"score": None})


class Recorder(Channel):
    name = "recorder"

    def __init__(self):
        self.sent: list[AlertMessage] = []

    def is_configured(self):
        return True

    def send(self, msg):
        self.sent.append(msg)


def _alertable(db):
    opp = db.scalars(select(Opportunity).where(Opportunity.is_active.is_(True), Opportunity.opportunity_type.in_(["FLIP", "CROSS_BORDER"])).order_by(Opportunity.score.desc())).first()
    opp.listing.is_demo = False  # demo data only goes to the log channel
    opp.score = 90
    return opp


def test_alerts_deduplicated_and_price_drop_realerts(db):
    db.add(AlertRule(name="t", conditions=DEFAULT, channels=["recorder"], include_price_drops=True))
    db.flush()
    rec = Recorder()
    opp = _alertable(db)
    d = AlertDispatcher(db, channels={"recorder": rec})
    assert d.process(opp) == 1
    assert d.process(opp) == 0  # unchanged listing -> no repeat
    assert AlertDispatcher(db, channels={"recorder": rec}).process(opp) == 0
    opp.fingerprint = "new-price"  # a price change produces a new fingerprint
    assert d.process(opp, price_dropped=True) == 1
    assert "PRICE DROP" in rec.sent[-1].text
    n = db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.listing_id == opp.listing_id, AlertEvent.channel == "recorder"))
    assert n == 2


def test_demo_listings_never_leave_log_channel(db):
    db.add(AlertRule(name="t2", conditions=DEFAULT, channels=["recorder"]))
    db.flush()
    opp = _alertable(db)
    opp.listing.is_demo = True
    rec = Recorder()
    AlertDispatcher(db, channels={"recorder": rec}).process(opp)
    assert rec.sent == []


def test_alert_message_content(db):
    opp = _alertable(db)
    msg = format_alert(opp, opp.listing)
    for s in ("Marketplace:", "Price:", "Estimated quick-sale:", "Risk:", "Opportunity Score:", "[OPEN LISTING]"):
        assert s in msg.text
    if opp.requires_authentication:
        assert "Authentication required before purchase" in msg.text
    assert opportunity_fields(opp)["score"] == opp.score
