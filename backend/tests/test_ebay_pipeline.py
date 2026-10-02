"""Phase 2: eBay Browse API -> normalisation -> valuation -> scoring -> alerts, end to end
through the real scanner, with eBay's HTTP API mocked from stored fixtures."""

import copy
import json
from functools import partial

import httpx
from sqlalchemy import select

from arbscan.alerts.channels import Channel
from arbscan.connectors import ebay as ebay_mod
from arbscan.connectors.ebay import EbayBrowseConnector
from arbscan.core.http import PoliteClient, RetryPolicy
from arbscan.db.models import AlertEvent, AlertRule, Listing, Opportunity, Watchlist
from arbscan.services import scanner as scanner_mod

from .conftest import load_fixture


class Recorder(Channel):
    name = "recorder"

    def __init__(self):
        self.sent = []

    def is_configured(self):
        return True

    def send(self, msg):
        self.sent.append(msg)


def make_transport(payload_ref):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth2/token"):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 7200})
        assert request.url.path == "/buy/browse/v1/item_summary/search"
        assert request.headers["x-ebay-c-marketplace-id"] == "EBAY_ES"
        return httpx.Response(200, json=payload_ref["payload"])

    return httpx.MockTransport(handler)


def test_ebay_scan_end_to_end(db, monkeypatch):
    settings = ebay_mod.get_settings()
    monkeypatch.setattr(settings, "ebay_client_id", "id")
    monkeypatch.setattr(settings, "ebay_client_secret", "secret")
    ebay_mod._token_cache.clear()

    payload = json.loads(load_fixture("ebay_search_es.json"))
    # make the first item an obvious bargain from an established seller
    payload["itemSummaries"][0]["price"]["value"] = "430.00"
    ref = {"payload": payload}
    transport = make_transport(ref)

    def build(key, code, config):
        client = PoliteClient("t", requests_per_minute=100000, enforce_robots=False, transport=transport, retry=RetryPolicy(max_attempts=1))
        return EbayBrowseConnector(code, config, client=client)

    monkeypatch.setattr(scanner_mod, "build_connector", build)
    rec = Recorder()
    monkeypatch.setattr(scanner_mod, "AlertDispatcher", partial(scanner_mod.AlertDispatcher, channels={"recorder": rec}))
    db.add(AlertRule(name="e2e", conditions={"any": [{"all": [{"field": "net_profit", "op": ">=", "value": 50}]}]}, channels=["recorder"]))
    for w in db.scalars(select(Watchlist)):
        w.enabled = False
    db.add(Watchlist(name="TM6 eBay", keyword="thermomix tm6", marketplaces=["ebay_es"], priority="high"))
    db.flush()

    run = scanner_mod.run_marketplace_scan(db, "ebay_es", force=True)
    assert run.status == "success", run.error
    assert run.listings_found == 3 and run.listings_new == 3

    listings = {l.external_id: l for l in db.scalars(select(Listing).where(Listing.marketplace_code == "ebay_es", Listing.is_demo.is_(False)))}
    bargain = listings["v1|186512345678|0"]
    assert bargain.canonical_product.slug == "thermomix-tm6"
    assert bargain.seller_rating_count == 312 and bargain.shipping_cost_eur == 9.9
    jar = listings["v1|186500000001|0"]  # "Vaso Thermomix TM6" - spare part, must not be valued as a TM6
    assert jar.canonical_product_id is None

    opp = db.scalars(select(Opportunity).where(Opportunity.listing_id == bargain.id)).one()
    assert opp.opportunity_type == "FLIP" and opp.net_profit_quick_eur > 50
    assert opp.cost_breakdown["lines"] and opp.score > 0
    assert len(rec.sent) >= 1 and "Thermomix" in rec.sent[0].text

    # second scan, same data -> no duplicate alert
    n_before = len(rec.sent)
    db.get(scanner_mod.Marketplace, "ebay_es").next_run_at = None
    scanner_mod.run_marketplace_scan(db, "ebay_es", force=True)
    assert len(rec.sent) == n_before

    # price drop -> history appended + new alert
    payload2 = copy.deepcopy(payload)
    payload2["itemSummaries"][0]["price"]["value"] = "399.00"
    ref["payload"] = payload2
    run3 = scanner_mod.run_marketplace_scan(db, "ebay_es", force=True)
    assert run3.price_changes == 1
    assert [h.change_type for h in bargain.price_history] == ["initial", "drop"]
    assert len(rec.sent) == n_before + 1 and "PRICE DROP" in rec.sent[-1].text
    kinds = {e.kind for e in db.scalars(select(AlertEvent).where(AlertEvent.listing_id == bargain.id))}
    assert kinds == {"deal", "price_drop"}
