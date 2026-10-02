import pytest

from arbscan.normalization.engine import detect_accessories, detect_condition, make_variant_key
from arbscan.normalization.text import detect_language, fold, sanitize_text


@pytest.mark.parametrize("title", ["Thermomix TM6", "TM6 Vorwerk", "Robot Thermomix 6", "Vorwerk Thermomix TM-6 comme neuf"])
def test_thermomix_variants_map_to_same_product(normalizer, title):
    r = normalizer.normalize(title)
    assert r.product_slug == "thermomix-tm6"
    assert r.brand == "Vorwerk"
    assert r.model == "Thermomix TM6"
    assert r.confidence >= 0.8


@pytest.mark.parametrize(
    "title",
    ["Cartier Love or jaune taille 17", "LOVE Bracelet Yellow Gold 17", "Pulsera Cartier Love T17 oro amarillo", "Cartier Love Armband Gelbgold Größe 17"],
)
def test_cartier_love_normalizes_brand_collection_material_size(normalizer, title):
    r = normalizer.normalize(title)
    assert r.product_slug == "cartier-love-bracelet"
    assert r.brand == "Cartier"
    assert r.collection == "Love"
    assert r.product_type == "bracelet"
    assert r.attributes["material"] == "yellow_gold"
    assert r.attributes["size"] == "17"
    assert r.variant_key == "material=yellow_gold"


def test_brand_present_gives_higher_confidence_than_alias_only(normalizer):
    with_brand = normalizer.normalize("Cartier Love bracelet yellow gold 17")
    without = normalizer.normalize("LOVE Bracelet Yellow Gold 17")
    assert with_brand.confidence > without.confidence


def test_reference_number_is_highest_confidence(normalizer):
    r = normalizer.normalize("Rolex Datejust 41 126334 full set")
    assert r.product_slug == "rolex-datejust"
    assert r.attributes["reference"] == "126334"
    assert r.confidence >= 0.95
    assert any("reference" in x for x in r.reasons)


@pytest.mark.parametrize(
    "title,slug",
    [
        ("Omega Speedmaster 310.30.42.50.01.002", "omega-speedmaster-moonwatch"),
        ("Tudor Black Bay 58 M79030N", "tudor-black-bay"),
        ("Bolso Louis Vuitton Neverfull MM monogram", "lv-neverfull"),
        ("MacBook Pro 14\" M3 Pro 18GB 512GB", "apple-macbook-pro"),
        ("LEGO 10221 Super Star Destroyer precintado", "lego-10221-super-star-destroyer"),
        ("Bugaboo Fox 3 completo", "bugaboo-fox"),
        ("Sony A7 IV cuerpo", "sony-a7-iv"),
        ("PS5 slim con lector + 2 mandos", "ps5"),
        ("Pendentif Van Cleef & Arpels Vintage Alhambra onyx", "vca-vintage-alhambra-pendant"),
    ],
)
def test_catalog_matches(normalizer, title, slug):
    assert normalizer.normalize(title).product_slug == slug


@pytest.mark.parametrize(
    "title",
    ["Vaso Thermomix TM6", "Mando PS5 DualSense", "Bague Cartier Love or blanc", "Funda para MacBook Pro 14", "Sonos Arc Ultra"],
)
def test_accessories_and_other_products_are_not_matched_as_product(normalizer, title):
    r = normalizer.normalize(title)
    assert r.product_slug not in ("thermomix-tm6", "ps5", "cartier-love-bracelet", "sonos-arc") or r.confidence < 0.35


def test_tm5_not_confused_with_tm6(normalizer):
    assert normalizer.normalize("Thermomix TM5 con chip").product_slug == "thermomix-tm5"


def test_variant_attributes_templates(normalizer):
    r = normalizer.normalize("Apple MacBook Pro 16 pulgadas M1 Pro 16GB 1TB")
    assert r.attributes["chip"] == "m1_pro"
    assert r.attributes["screen"] == "16"
    assert r.variant_key == "chip=m1_pro;screen=16"


def test_flag_attributes_absent_do_not_penalize(normalizer):
    r = normalizer.normalize("Cartier Love bracelet or jaune 17")
    assert not any("model_size" in x or "diamonds" in x for x in r.reasons)
    small = normalizer.normalize("Cartier Love bracelet small model or rose")
    assert small.attributes.get("model_size") == "small"


def test_accessory_only_detection(normalizer):
    r = normalizer.normalize("Funda para MacBook Pro 14")
    assert r.accessory_only
    assert r.confidence < 0.35


@pytest.mark.parametrize(
    "text,expected",
    [
        ("como nuevo, apenas usado", "like_new"),
        ("comme neuf", "like_new"),
        ("wie neu", "like_new"),
        ("nuevo precintado", "new"),
        ("très bon état", "very_good"),
        ("buen estado", "good"),
        ("gebraucht", "good"),
        ("para piezas, no funciona", "for_parts"),
        ("defekt", "for_parts"),
        ("come nuovo", "like_new"),
        ("bom estado", "good"),
        ("", "unknown"),
    ],
)
def test_condition_multilingual(text, expected):
    assert detect_condition(fold(text)) == expected


def test_structured_condition_wins():
    assert detect_condition(fold("descripción: nuevo"), "Usado - Como nuevo") == "like_new"


def test_accessories_negation_before_positive():
    acc = detect_accessories(fold("Vendido sin caja pero con factura y certificado"))
    assert acc["box"] is False
    assert acc["receipt"] is True
    assert acc["papers"] is True
    assert detect_accessories(fold("ohne Box, ohne Papiere"))["box"] is False


def test_authenticity_info_is_reported_as_claim(normalizer):
    r = normalizer.normalize("Cartier Love T17", "Totalmente auténtica, comprada en Cartier Madrid con factura.")
    assert r.authenticity_info and "factura" in r.authenticity_info
    # normalisation never sets an "authentic" verdict
    assert "authentic" not in r.as_dict()


def test_language_detection():
    assert detect_language("Vendo pulsera en muy buen estado con caja") == "es"
    assert detect_language("Je vends ce sac en très bon état avec facture") == "fr"
    assert detect_language("Verkaufe Uhr in sehr gutem Zustand mit Box") == "de"
    assert detect_language("Vendo borsa usata in ottime condizioni") == "it"


def test_sanitize_strips_markup():
    assert sanitize_text("<script>alert(1)</script>Hola &amp; adiós") == "alert(1) Hola & adiós"


def test_variant_key_only_critical():
    assert make_variant_key({"material": "yellow_gold", "size": "17"}, {"material": 1.0, "size": 0.3}) == "material=yellow_gold"
