from datetime import UTC, datetime, timedelta

from arbscan.risk.engine import AUTH_WARNING, RiskEngine, RiskInput

NOW = datetime(2026, 10, 1, tzinfo=UTC)
engine = RiskEngine()


def codes(res):
    return {f.code for f in res.flags}


def legit(**kw):
    d = dict(
        title="Thermomix TM6", description="Muy buen estado, con factura. Envío disponible.", price_eur=640,
        market_value_eur=760, seller_rating=4.9, seller_rating_count=120, seller_account_created_at=NOW - timedelta(days=1500),
        image_urls=[f"https://img.example/{i}.jpg" for i in range(5)], country="ES", marketplace_country="ES", now=NOW,
    )
    d.update(kw)
    return RiskInput(**d)


def test_legit_listing_is_low_risk():
    res = engine.evaluate(legit())
    assert res.level == "LOW"
    assert "SELLER_ESTABLISHED" in codes(res) and "ORIGINAL_PHOTOS" in codes(res)


def test_classic_scam_is_high_risk_with_explanations():
    res = engine.evaluate(legit(
        title="Rolex Datejust 126334", price_eur=2900, market_value_eur=11500, is_luxury=True,
        description="Estoy en el extranjero, pago solo por Western Union. Escríbeme por WhatsApp.",
        seller_rating_count=0, seller_rating=None, seller_account_created_at=NOW - timedelta(days=3),
        image_urls=["https://www.rolex.com/stock.jpg"],
    ))
    assert res.level == "HIGH"
    assert {"PRICE_ABSURD", "OFF_PLATFORM_PAYMENT", "SELLER_NEW", "SELLER_NO_RATINGS", "STOCK_IMAGE_HOST"} <= codes(res)
    assert AUTH_WARNING in res.warnings
    assert res.reasons  # human-readable explanations


def test_never_called_fraud():
    res = engine.evaluate(legit(price_eur=100, description="western union whatsapp"))
    assert res.level in ("LOW", "MEDIUM", "HIGH")
    assert not any("fraud" in f.message.lower() for f in res.flags)


def test_counterfeit_wording_luxury():
    res = engine.evaluate(legit(title="Pulsera tipo Cartier Love AAA", is_luxury=True, market_value_eur=5000, price_eur=4000))
    assert "COUNTERFEIT_WORDING" in codes(res)
    assert res.level in ("MEDIUM", "HIGH")


def test_unprotected_payment_is_soft_signal():
    res = engine.evaluate(legit(description="Acepto Bizum o transferencia."))
    assert "UNPROTECTED_PAYMENT" in codes(res)
    assert res.level == "LOW"


def test_contact_details_in_text():
    res = engine.evaluate(legit(description="Llámame al 612 345 678 para más info"))
    assert "CONTACT_IN_TEXT" in codes(res)


def test_reference_numbers_not_mistaken_for_phone():
    res = engine.evaluate(legit(description="Ref 310.30.42.50.01.001 full set"))
    assert "CONTACT_IN_TEXT" not in codes(res)


def test_duplicate_images_and_cities():
    res = engine.evaluate(legit(duplicate_image_listings=2, duplicate_text_cities=3))
    assert {"DUPLICATE_IMAGES", "DUPLICATE_CITIES"} <= codes(res)
    assert res.level == "HIGH"


def test_luxury_without_provenance_and_auth_warning():
    res = engine.evaluate(legit(title="Cartier Love", is_luxury=True, market_value_eur=5000, price_eur=4300, accessories={}))
    assert "NO_PROVENANCE" in codes(res)
    assert res.requires_authentication


def test_unknown_reference():
    res = engine.evaluate(legit(attributes={"reference": "999999"}, known_references=["126300", "126334"]))
    assert "UNKNOWN_REFERENCE" in codes(res)


def test_private_seller_many_high_value_items():
    res = engine.evaluate(legit(seller_high_value_listings=8, seller_distinct_categories=4, seller_type="private"))
    assert "SELLER_MANY_HIGH_VALUE" in codes(res)
