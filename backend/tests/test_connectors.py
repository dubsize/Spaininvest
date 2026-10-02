import json

import httpx
import pytest

from arbscan.connectors.base import ConnectorDisabled, SearchQuery
from arbscan.connectors.ebay import EbayBrowseConnector
from arbscan.connectors.page_metadata import detect_marketplace, external_id_from_url, parse_metadata
from arbscan.connectors.registry import CONNECTORS, MARKETPLACE_SEED, build_connector
from arbscan.core.http import PoliteClient, RetryPolicy, RobotsDisallowed

from .conftest import load_fixture


def ebay(code="ebay_es", mid="EBAY_ES", country="ES", transport=None):
    client = PoliteClient("t", requests_per_minute=10000, enforce_robots=False, transport=transport, retry=RetryPolicy(max_attempts=2, base_delay=0.01))
    return EbayBrowseConnector(code, {"ebay_marketplace_id": mid, "country": country}, client=client)


def test_ebay_search_fixture_parsing():
    items = ebay().parse_search_response(json.loads(load_fixture("ebay_search_es.json")))
    assert len(items) == 3
    a = items[0]
    assert a.external_id == "v1|186512345678|0"
    assert a.price == 595.0 and a.currency == "EUR"
    assert a.country == "ES" and a.postal_code == "280**"
    assert a.seller_name == "cocina_madrid" and a.seller_rating_count == 312
    assert a.seller_rating == pytest.approx(4.98)
    assert a.shipping_cost == 9.9 and a.shipping_available
    assert len(a.image_urls) == 2
    assert a.published_at.year == 2026
    assert a.condition_raw == "Usado"
    assert items[1].original_price == 750.0
    assert items[2].image_urls == []


def test_ebay_item_fixture_sanitizes_html():
    item = ebay("ebay_de", "EBAY_DE", "DE").normalize_listing(json.loads(load_fixture("ebay_item_de.json")))
    assert "<" not in item.description and "Full Set" in item.description
    assert item.city == "München"
    assert item.brand_raw == "Omega" and item.model_raw == "Speedmaster Professional"
    assert item.source_metadata["aspects"]["Referenznummer"] == "310.30.42.50.01.001"


def test_ebay_search_params():
    params = ebay().build_search_params(SearchQuery(keywords="thermomix tm6", max_price=700, limit=500))
    assert params["limit"] == "200"
    assert params["sort"] == "newlyListed"
    assert "price:[..700]" in params["filter"] and "itemLocationCountry:ES" in params["filter"]


def test_ebay_end_to_end_with_mock_transport(monkeypatch):
    from arbscan.connectors import ebay as ebay_mod

    monkeypatch.setattr(ebay_mod.get_settings(), "ebay_client_id", "id")
    monkeypatch.setattr(ebay_mod.get_settings(), "ebay_client_secret", "secret")
    ebay_mod._token_cache.clear()
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/oauth2/token"):
            assert request.headers["authorization"].startswith("Basic ")
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 7200, "token_type": "Application Access Token"})
        if len(calls) == 2:
            return httpx.Response(503, text="busy")  # retried
        assert request.headers["x-ebay-c-marketplace-id"] == "EBAY_ES"
        assert request.headers["authorization"] == "Bearer tok"
        return httpx.Response(200, json=json.loads(load_fixture("ebay_search_es.json")))

    c = ebay(transport=httpx.MockTransport(handler))
    c.settings = ebay_mod.get_settings()
    items = c.search(SearchQuery(keywords="thermomix tm6"))
    assert len(items) == 3
    assert c.health_check().status == "OK"


def test_ebay_not_configured_health():
    assert ebay().health_check().status == "NOT_CONFIGURED"


def test_stub_connectors_refuse_search():
    for code in ("wallapop", "leboncoin", "vinted", "kleinanzeigen", "milanuncios", "vestiaire", "chrono24", "catawiki", "facebook", "amazon"):
        c = build_connector(code, code)
        assert c.is_stub
        assert c.compliance.summary
        with pytest.raises(ConnectorDisabled):
            c.search(SearchQuery(keywords="x"))
        assert c.health_check().status == "STUB"


def test_every_seeded_marketplace_has_a_connector():
    assert all(m["connector_key"] in CONNECTORS for m in MARKETPLACE_SEED)


def test_page_metadata_parsing_fixture():
    md = parse_metadata(load_fixture("listing_page.html"), "https://example.com/item/123456789")
    assert md.title == "Thermomix TM6 con Varoma & recetario"
    assert md.price == 625.0 and md.currency == "EUR"
    assert md.brand == "Vorwerk" and md.condition == "UsedCondition"
    assert md.image_urls[0] == "https://cdn.example.com/img/tm6-1.jpg"


def test_layout_change_detected():
    from arbscan.connectors.base import LayoutChanged

    with pytest.raises(LayoutChanged):
        parse_metadata("<html><body>" + "x" * 6000 + "</body></html>", "https://example.com")


def test_detect_marketplace_from_url():
    assert detect_marketplace("https://es.wallapop.com/item/thermomix-tm6-1234567") == ("wallapop", "ES")
    assert detect_marketplace("https://www.leboncoin.fr/ad/electromenager/2456789012") == ("leboncoin", "FR")
    assert detect_marketplace("https://www.ebay.de/itm/405512340000") == ("ebay_de", "DE")
    assert detect_marketplace("https://unknown.example/x") == ("manual", None)
    assert external_id_from_url("https://www.leboncoin.fr/ad/electromenager/2456789012") == "2456789012"


def test_robots_txt_respected():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private/\n")
        return httpx.Response(200, text="<html><title>ok</title></html>")

    client = PoliteClient("robots-test", requests_per_minute=1000, transport=httpx.MockTransport(handler))
    client.enforce_robots = True
    assert client.get("https://robots.example/public/page").status_code == 200
    with pytest.raises(RobotsDisallowed):
        client.get("https://robots.example/private/page")


def test_retry_after_and_backoff(monkeypatch):
    import arbscan.core.http as http_mod

    sleeps = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: sleeps.append(s))
    n = {"i": 0}

    def handler(request):
        n["i"] += 1
        return httpx.Response(429, headers={"Retry-After": "2"}) if n["i"] < 3 else httpx.Response(200, text="ok")

    client = PoliteClient("retry-test", requests_per_minute=1000, enforce_robots=False, transport=httpx.MockTransport(handler))
    assert client.get("https://api.example/x").text == "ok"
    assert sleeps[:2] == [2.0, 2.0]


def test_ssrf_guard():
    from arbscan.connectors.page_metadata import fetch_metadata

    assert "non-public" in (fetch_metadata("http://127.0.0.1/admin").error or "")
    assert fetch_metadata("file:///etc/passwd").error
