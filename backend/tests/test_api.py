from fastapi.testclient import TestClient


def test_health_public(client):
    assert client.get("/api/health").json()["database"] is True


def test_auth_required_and_bad_login(seeded_db):
    from arbscan.api.main import create_app

    with TestClient(create_app()) as c:
        assert c.get("/api/dashboard").status_code == 401
        assert c.post("/api/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401


def test_csrf_required_for_mutations(client):
    token = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/watchlists", json={"name": "x", "keyword": "x"}).status_code == 403
    client.headers["X-CSRF-Token"] = token


def test_security_headers(client):
    r = client.get("/api/auth/me")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_dashboard(client):
    d = client.get("/api/dashboard").json()
    assert d["kpis"]["active_opportunities"] > 0
    for key in ("deploy_now", "hottest", "newest", "highest_profit", "highest_roi", "highest_liquidity", "cross_border", "price_reduced", "negotiation"):
        assert key in d
    assert d["hottest"]


def test_opportunities_filters_and_sorting(client):
    r = client.get("/api/opportunities", params={"sort": "net_profit", "order": "desc", "page_size": 20}).json()
    profits = [o["net_profit_quick_eur"] for o in r["items"] if o["net_profit_quick_eur"] is not None]
    assert profits == sorted(profits, reverse=True)
    r = client.get("/api/opportunities", params={"country": "FR", "risk": ["LOW", "MEDIUM"]}).json()
    assert all(o["listing"]["country"] == "FR" and o["risk_level"] != "HIGH" for o in r["items"])
    r = client.get("/api/opportunities", params={"type": "NEGOTIATION"}).json()
    assert r["total"] > 0 and all(o["target_offer_eur"] for o in r["items"])
    r = client.get("/api/opportunities", params={"min_score": 60, "max_age_hours": 48, "min_roi": 0.1}).json()
    assert all(o["score"] >= 60 for o in r["items"])
    assert client.get("/api/opportunities/facets").json()["marketplaces"]


def test_opportunity_detail_offer_status_purchase_sell(client):
    opp = client.get("/api/opportunities", params={"type": "FLIP", "page_size": 1}).json()["items"][0]
    offer = client.post(f"/api/opportunities/{opp['id']}/offer", json={"target_roi": 0.25}).json()
    assert offer["ideal_offer"] <= offer["max_acceptable_offer"]
    assert client.post(f"/api/opportunities/{opp['id']}/status", json={"status": "WATCHING"}).json()["status"] == "WATCHING"
    assert client.post(f"/api/opportunities/{opp['id']}/status", json={"status": "SOLD"}).status_code == 400
    deal_id = client.post(f"/api/opportunities/{opp['id']}/purchase", json={"purchase_price_eur": opp["purchase_price_eur"] * 0.95, "purchase_shipping_eur": 5}).json()["deal_id"]
    sold = client.post(f"/api/deals/{deal_id}/sell", json={"sale_price_eur": opp["quick_sale_eur"], "sale_fees_eur": 10}).json()
    assert sold["status"] == "SOLD" and sold["metrics"]["profit"] is not None
    assert client.get("/api/portfolio").json()["deals_sold"] >= 6


def test_listing_detail_has_comparables_and_history(client):
    opp = client.get("/api/opportunities", params={"price_dropped": True, "page_size": 1}).json()["items"][0]
    d = client.get(f"/api/listings/{opp['listing_id']}").json()
    assert d["comparables"] and d["opportunities"]
    assert len(d["listing"]["price_history"]) >= 2


def test_product_crud_and_detail(client):
    body = {"name": "Leica Q2", "brand": "Leica", "model": "Q2", "category_code": "cameras", "aliases": ["leica q2"], "variant_attributes": {}}
    p = client.post("/api/products", json=body)
    assert p.status_code == 201, p.text
    pid = p.json()["id"]
    assert client.post("/api/products", json=body).status_code == 409
    body["popularity"] = 0.8
    assert client.put(f"/api/products/{pid}", json=body).json()["popularity"] == 0.8
    assert client.post("/api/products", json={**body, "slug": "bad", "patterns": ["(unclosed"]}).status_code == 422
    t = client.post("/api/products/normalize/test", json={"title": "Leica Q2 como nueva"}).json()
    assert t["product_slug"] == "leica-q2"
    assert client.delete(f"/api/products/{pid}").json()["ok"]
    tm6 = next(x for x in client.get("/api/products").json() if x["slug"] == "thermomix-tm6")
    detail = client.get(f"/api/products/{tm6['id']}").json()
    assert detail["variants"][0]["valuation"]["n_comparables"] > 0
    assert detail["variants"][0]["max_buy_price_eur"] > 0
    assert detail["price_distribution"] and detail["marketplace_comparison"]


def test_watchlist_crud(client):
    w = client.post("/api/watchlists", json={"name": "Dyson Airwrap", "keyword": "Dyson Airwrap", "countries": ["es"], "min_score": 50, "priority": "high"}).json()
    assert w["countries"] == ["ES"]
    w2 = client.put(f"/api/watchlists/{w['id']}", json={**{k: w[k] for k in ("name", "keyword", "countries", "priority")}, "min_roi": 0.2}).json()
    assert w2["min_roi"] == 0.2
    assert "items" in client.get(f"/api/watchlists/{w['id']}/matches").json()
    assert client.delete(f"/api/watchlists/{w['id']}").json()["ok"]
    assert client.post("/api/watchlists", json={"name": "empty"}).status_code == 400


def test_manual_entry_without_connector(client):
    r = client.post("/api/listings/manual", json={
        "url": "https://www.vinted.fr/items/4567891234-sac-louis-vuitton", "title": "Sac Louis Vuitton Neverfull MM monogram",
        "price": 790, "description": "Très bon état, avec facture.", "city": "Lyon", "seller_rating": 4.9, "seller_rating_count": 54,
    })
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["listing"]["marketplace_code"] == "vinted_fr" and d["listing"]["country"] == "FR"
    assert d["product"]["slug"] == "lv-neverfull"
    assert d["opportunities"][0]["requires_authentication"] is True
    lid = d["listing"]["id"]
    fixed = client.patch(f"/api/listings/{lid}", json={"price": 700}).json()
    assert len(fixed["listing"]["price_history"]) == 2
    assert client.delete(f"/api/listings/{lid}").json()["ok"]


def test_scanner_status_and_demo_scan(client):
    mps = client.get("/api/scanner/marketplaces").json()
    wallapop = next(m for m in mps if m["code"] == "wallapop")
    assert wallapop["is_stub"] and "Alternative" in wallapop["compliance_notes"]
    assert client.patch("/api/scanner/marketplaces/wallapop", json={"enabled": True}).status_code == 400
    run = client.post("/api/scanner/marketplaces/demo_feed/run").json()
    assert run["queued"] is False and run["run"]["status"] == "success"
    ebay = client.post("/api/scanner/marketplaces/ebay_es/run").json()
    assert ebay["run"]["status"] == "skipped"
    assert client.get("/api/scanner/runs").json()


def test_csv_export_import(client):
    r = client.get("/api/io/export/opportunities.csv")
    assert r.status_code == 200 and "opportunity_id" in r.text.splitlines()[0]
    assert "price_eur" in client.get("/api/io/export/price-history.csv").text
    csv_text = "url,title,price,currency,country,city,description\nhttps://www.milanuncios.com/x/thermomix-tm6-555666777.htm,Thermomix TM6,480,EUR,ES,Valencia,Buen estado\n,Missing price,,EUR,ES,,\n"
    res = client.post("/api/io/import/listings", files={"file": ("l.csv", csv_text, "text/csv")}).json()
    assert res["created"] == 1 and len(res["errors"]) == 1
    wl = "name;keyword;countries;min_roi_pct;priority\nSonos Sub;Sonos Sub;ES | FR;20;standard\n"
    res = client.post("/api/io/import/watchlists", files={"file": ("w.csv", wl, "text/csv")}).json()
    assert res["created"] == 1, res
    assert "Sonos Sub" in client.get("/api/io/export/watchlists.csv").text


def test_settings_roundtrip(client):
    s = client.get("/api/settings/app").json()
    assert "weights" in s["scoring"]
    upd = client.put("/api/settings/app/business", json={"target_roi": 0.3}).json()
    assert upd["target_roi"] == 0.3
    assert client.put("/api/settings/app/business", json={"nope": 1}).status_code == 400
    client.put("/api/settings/app/business", json={"target_roi": 0.25})
    fees = client.get("/api/settings/fees").json()
    f = fees[0]
    f["notes"] = "checked"
    assert client.put(f"/api/settings/fees/{f['id']}", json=f).json()["notes"] == "checked"
