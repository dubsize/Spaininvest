"""Deterministic, realistic demo data.

Generates listings for every catalogue product across Wallapop, Leboncoin and eBay
ES/FR/DE with a mix of scenarios: normal, bargain, overpriced, scam-like, old
(negotiable) and price-reduced listings, plus ended/sold history used for liquidity.
Everything produced here is flagged ``is_demo`` and can be purged from Settings.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from arbscan.connectors.base import RawListing
from arbscan.normalization.catalog import load_seed_yaml

MARKETPLACES = [
    # code, country, language, share
    ("wallapop", "ES", "es", 0.40),
    ("leboncoin", "FR", "fr", 0.24),
    ("ebay_es", "ES", "es", 0.12),
    ("ebay_fr", "FR", "fr", 0.10),
    ("ebay_de", "DE", "de", 0.14),
]
CITIES = {
    "ES": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Bilbao", "Zaragoza", "Alicante", "Palma", "Murcia", "Marbella", "San Sebastián"],
    "FR": ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse", "Nice", "Lille", "Nantes", "Montpellier", "Biarritz"],
    "DE": ["Berlin", "München", "Hamburg", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig"],
}
SELLERS = {
    "ES": ["lucia_m", "javi.rg", "carmen_vende", "pablo88", "martaa", "sergio_bcn", "ana.l", "dani_vlc", "elena_md", "rocio.s", "alvaro_t", "nuria_c"],
    "FR": ["claire.d", "mathieu75", "sophie_lyon", "julien.b", "camille_m", "nicolas_bdx", "chloe.r", "antoine_v"],
    "DE": ["jonas_hh", "lena.k", "max_muc", "sarah_b", "tobias.f", "anna_koeln", "felix_ber", "laura.s"],
}
VOCAB: dict[str, dict[str, str]] = {
    "yellow_gold": {"es": "oro amarillo", "fr": "or jaune", "en": "yellow gold", "de": "Gelbgold"},
    "rose_gold": {"es": "oro rosa", "fr": "or rose", "en": "rose gold", "de": "Roségold"},
    "white_gold": {"es": "oro blanco", "fr": "or blanc", "en": "white gold", "de": "Weißgold"},
    "onyx": {"es": "ónix", "fr": "onyx", "en": "onyx", "de": "Onyx"},
    "mother_of_pearl": {"es": "nácar", "fr": "nacre", "en": "mother of pearl", "de": "Perlmutt"},
    "malachite": {"es": "malaquita", "fr": "malachite", "en": "malachite", "de": "Malachit"},
    "carnelian": {"es": "cornalina", "fr": "cornaline", "en": "carnelian", "de": "Karneol"},
    "monogram_canvas": {"es": "Monogram", "fr": "Monogram", "en": "Monogram canvas", "de": "Monogram"},
    "damier_ebene": {"es": "Damier Ebene", "fr": "Damier Ébène", "en": "Damier Ebene", "de": "Damier Ebene"},
    "damier_azur": {"es": "Damier Azur", "fr": "Damier Azur", "en": "Damier Azur", "de": "Damier Azur"},
    "black": {"es": "negro", "fr": "noir", "en": "black", "de": "schwarz"},
    "beige": {"es": "beige", "fr": "beige", "en": "beige", "de": "beige"},
    "white": {"es": "blanca", "fr": "blanc", "en": "white", "de": "weiß"},
    "silver": {"es": "plata", "fr": "argent", "en": "silver", "de": "silber"},
    "caviar": {"es": "caviar", "fr": "caviar", "en": "caviar", "de": "Caviar"},
    "lambskin": {"es": "piel de cordero", "fr": "agneau", "en": "lambskin", "de": "Lammleder"},
    "disc": {"es": "con lector", "fr": "standard avec lecteur", "en": "disc edition", "de": "mit Laufwerk"},
    "digital": {"es": "digital", "fr": "digitale", "en": "digital edition", "de": "Digital Edition"},
    "slim": {"es": "Slim", "fr": "Slim", "en": "Slim", "de": "Slim"},
    "pro": {"es": "Pro", "fr": "Pro", "en": "Pro", "de": "Pro"},
    "sealed": {"es": "precintado", "fr": "scellé neuf", "en": "sealed MISB", "de": "neu ungeöffnet"},
    "yes": {"es": "en caja", "fr": "en boîte", "en": "boxed", "de": "OVP"},
    "small": {"es": "small", "fr": "small", "en": "small", "de": "small"},
    "mini": {"es": "mini", "fr": "mini", "en": "mini", "de": "mini"},
    "medium": {"es": "medium", "fr": "medium", "en": "medium", "de": "medium"},
}
CONDITION_TEXT = {
    "new": {"es": "Nuevo, sin estrenar.", "fr": "Neuf, jamais utilisé.", "de": "Neu und unbenutzt.", "en": "Brand new."},
    "like_new": {"es": "Como nuevo, apenas usado.", "fr": "Comme neuf, très peu servi.", "de": "Wie neu, kaum benutzt.", "en": "Like new."},
    "very_good": {"es": "Muy buen estado.", "fr": "Très bon état.", "de": "Sehr guter Zustand.", "en": "Very good condition."},
    "good": {"es": "Buen estado, marcas de uso normales.", "fr": "Bon état, quelques signes d'usure.", "de": "Guter Zustand, leichte Gebrauchsspuren.", "en": "Good condition."},
    "fair": {"es": "Estado aceptable, tiene arañazos.", "fr": "État correct, quelques rayures.", "de": "Akzeptabel, Kratzer vorhanden.", "en": "Fair condition, scratches."},
}
EXTRAS = {
    "luxury_docs": {"es": "Con caja, papeles y factura de compra.", "fr": "Avec boîte, papiers et facture d'achat.", "de": "Mit Box, Papieren und Rechnung.", "en": "Full set with box, papers and receipt."},
    "luxury_box": {"es": "Con caja original, sin factura.", "fr": "Avec boîte d'origine, sans facture.", "de": "Mit Originalbox, ohne Rechnung.", "en": "Original box, no receipt."},
    "luxury_none": {"es": "Sin caja ni papeles.", "fr": "Sans boîte ni papiers.", "de": "Ohne Box und Papiere.", "en": "No box, no papers."},
    "shipping": {"es": "Envío disponible.", "fr": "Envoi possible.", "de": "Versand möglich.", "en": "Shipping available."},
    "pickup": {"es": "Solo entrega en mano.", "fr": "Remise en main propre uniquement.", "de": "Nur Abholung.", "en": "Pickup only."},
    "reason": {"es": "Lo vendo porque no lo uso.", "fr": "Je le vends car je ne l'utilise plus.", "de": "Verkaufe, da ich es nicht mehr nutze.", "en": "Selling as I no longer use it."},
    "negotiable": {"es": "Precio negociable.", "fr": "Prix négociable.", "de": "Preis VB.", "en": "Price negotiable."},
}
SCAM_TEXT = {
    "es": [
        "Estoy en el extranjero, envío por correos. Pago solo por transferencia o Western Union. Escríbeme por WhatsApp.",
        "Precio de chollo, necesito el dinero urgente. Pago por adelantado y envío. Contacto por whatsapp.",
        "Fotos de internet. Original 100%. Pago PayPal amigos y familiares.",
    ],
    "fr": [
        "Je suis à l'étranger, envoi uniquement. Paiement par virement ou Western Union. Contactez-moi par WhatsApp.",
        "Prix sacrifié, urgent. Paiement d'avance par mandat cash. Photos non contractuelles.",
    ],
    "de": [
        "Bin im Ausland, nur Versand. Zahlung per Vorkasse oder Western Union. Schreiben Sie mir per WhatsApp.",
        "Dringend, brauche Geld. Nur Versand, PayPal Freunde.",
    ],
}
STOCK_HOSTS = {
    "luxury_jewelry": "https://www.cartier.com/dw/image/v2/stock/product.jpg",
    "luxury_bags": "https://www.louisvuitton.com/images/is/image/lv/stock.jpg",
    "luxury_watches": "https://www.omegawatches.com/media/catalog/product/stock.png",
}
LUXURY = {"luxury_jewelry", "luxury_bags", "luxury_watches"}
COUNTRY_PRICE_FACTOR = {
    # (country, category) -> factor vs Spain. Illustrative: luxury slightly cheaper in FR,
    # Thermomix cheaper in DE (large second-hand supply).
    ("FR", "luxury_jewelry"): 0.93, ("FR", "luxury_bags"): 0.92, ("FR", "luxury_watches"): 0.96,
    ("DE", "kitchen_appliances"): 0.86, ("DE", "cameras"): 0.95, ("DE", "lenses"): 0.95,
    ("DE", "luxury_watches"): 0.97, ("DE", "bicycles"): 0.92, ("DE", "ebikes"): 0.9, ("FR", "strollers"): 0.94,
}


@dataclass
class DemoListing:
    raw: RawListing
    scenario: str
    first_seen_at: datetime
    price_timeline: list[tuple[datetime, float]] = field(default_factory=list)
    ended_at: datetime | None = None


def _fill(template: str, attrs: dict[str, str], lang: str, size: str | None, rnd: random.Random) -> str:
    values: dict[str, str] = {}
    for key, val in attrs.items():
        values[key] = val
        values[f"{key}_upper"] = val.upper()
        for lg in ("es", "fr", "en", "de"):
            values[f"{key}_{lg}"] = VOCAB.get(val, {}).get(lg, val)
    if "chip" in attrs:
        values["chip_label"] = attrs["chip"].replace("_", " ").upper().replace("PRO", "Pro").replace("MAX", "Max")
    values["size"] = size or ""
    color = rnd.choice(["black", "beige", "white", "silver"])
    for lg in ("es", "fr", "en", "de"):
        values.setdefault(f"color_{lg}", VOCAB[color][lg])
        for k in ("state", "boxed", "edition", "model_variant", "leather_type", "material", "bag_size", "generation", "reference"):
            values.setdefault(f"{k}_{lg}", "")
            values.setdefault(k, "")
    try:
        text = template.format(**values)
    except (KeyError, IndexError):
        text = template
    return " ".join(text.replace('""', "").split())


_LANG_HINTS = {
    "es": ("bolso", "pulsera", "talla", " con ", "colgante", "consola", "aspirador", "bicicleta", "barra", "pulgadas", "cuerpo", "precintado", "completo", "clásica", "estrella", "eléctrica", "mediano", "negro", "_es}"),
    "fr": ("sac ", "bracelet cartier", "taille", "montre", "poussette", "vélo", "pendentif", "boitier", "objectif", "pouces", "comme neu", "aspirateur", "caisson", "barre de son", "display", "fonctionne", "_fr}"),
    "de": ("armband", "größe", " uhr", "tasche", "konsole", "zoll", "kinderwagen", "faltrad", "rennrad", "objektiv", "akkusauger", "küchenmaschine", "auslösungen", "todesstern", "_de}"),
    "en": ("_en}", " bracelet ", "booster box", "full set", "original game boy"),
}


def _template_lang(t: str) -> str | None:
    low = f" {t.lower()} "
    for lang, hints in _LANG_HINTS.items():
        if any(h in low for h in hints):
            return lang
    return None


def _pick_template(templates: list[str], lang: str, rnd: random.Random) -> str:
    same = [t for t in templates if _template_lang(t) == lang]
    neutral = [t for t in templates if _template_lang(t) is None]
    pool = same or neutral or templates
    return rnd.choice(pool)


def _pick_marketplace(rnd: random.Random) -> tuple[str, str, str]:
    r = rnd.random()
    acc = 0.0
    for code, country, lang, share in MARKETPLACES:
        acc += share
        if r <= acc:
            return code, country, lang
    return MARKETPLACES[0][:3]


def _pick_variant(product: dict[str, Any], rnd: random.Random) -> tuple[dict[str, str], float]:
    demo = product.get("demo") or {}
    variants = demo.get("variants")
    if variants:
        weights = [v.get("weight", 1) for v in variants]
        v = rnd.choices(variants, weights=weights, k=1)[0]
        return {k: str(val) for k, val in (v.get("attrs") or {}).items()}, float(v["price"])
    return {}, float(demo.get("base_price", 500))


def _scenario(rnd: random.Random, luxury: bool) -> str:
    table = [("normal", 0.52), ("bargain", 0.12), ("overpriced", 0.11), ("negotiation", 0.10), ("price_drop", 0.07), ("scam", 0.05 if luxury else 0.03)]
    total = sum(w for _, w in table)
    r = rnd.random() * total
    acc = 0.0
    for name, w in table:
        acc += w
        if r <= acc:
            return name
    return "normal"


def generate_demo_listings(seed: int = 42, per_product: int = 9, now: datetime | None = None) -> list[DemoListing]:
    rnd = random.Random(seed)
    now = now or datetime.now(UTC)
    catalog = load_seed_yaml()
    categories = {c["code"]: c for c in catalog["categories"]}
    out: list[DemoListing] = []
    counter = 0
    for product in catalog["products"]:
        cat = product["category"]
        luxury = cat in LUXURY
        popularity = float(product.get("popularity", 0.5))
        n_active = per_product + rnd.randint(-2, 3)
        n_ended = max(2, int(n_active * (0.35 + popularity * 0.4)))
        templates = (product.get("demo") or {}).get("titles") or [product["name"]]
        sizes = (product.get("demo") or {}).get("sizes")
        for idx in range(n_active + n_ended):
            counter += 1
            ended = idx >= n_active
            mp, country, lang = _pick_marketplace(rnd)
            attrs, base_price = _pick_variant(product, rnd)
            size = rnd.choice(sizes) if sizes else None
            scenario = "normal" if ended else _scenario(rnd, luxury)
            condition = rnd.choices(["new", "like_new", "very_good", "good", "fair"], weights=[10, 30, 30, 24, 6])[0]
            cond_factor = {"new": 1.1, "like_new": 1.04, "very_good": 1.0, "good": 0.95, "fair": 0.82}[condition]
            country_factor = COUNTRY_PRICE_FACTOR.get((country, cat), 1.0)
            fair_ask = base_price * cond_factor * country_factor
            if scenario == "bargain":
                price = fair_ask * rnd.uniform(0.60, 0.78)
            elif scenario == "overpriced":
                price = fair_ask * rnd.uniform(1.22, 1.5)
            elif scenario == "scam":
                price = fair_ask * rnd.uniform(0.28, 0.45)
            elif scenario == "negotiation":
                price = fair_ask * rnd.uniform(1.0, 1.14)
            elif scenario == "price_drop":
                price = fair_ask * rnd.uniform(0.80, 0.9)
            else:
                price = fair_ask * rnd.gauss(1.0, 0.07)
            price = max(5.0, round(price / (10 if price > 300 else 5)) * (10 if price > 300 else 5) - (0 if rnd.random() < 0.6 else 1))

            # timing
            if ended:
                dom = rnd.uniform(2, 14) if popularity >= 0.8 else rnd.uniform(6, 45)
                published = now - timedelta(days=rnd.uniform(dom + 1, 150))
                ended_at = published + timedelta(days=dom)
            else:
                ended_at = None
                if scenario in ("bargain", "scam"):
                    published = now - timedelta(minutes=rnd.uniform(4, 60 * 30))
                elif scenario == "negotiation":
                    published = now - timedelta(days=rnd.uniform(35, 130))
                elif scenario == "price_drop":
                    published = now - timedelta(days=rnd.uniform(20, 70))
                else:
                    published = now - timedelta(hours=rnd.uniform(1, 24 * 40))

            template = _pick_template(templates, lang, rnd)
            title = _fill(template, attrs, lang, size, rnd)
            if condition == "new" and cat not in LUXURY and rnd.random() < 0.5:
                title += {"es": " nuevo", "fr": " neuf", "de": " neu", "en": " new"}.get(lang, "")

            # description
            parts = [CONDITION_TEXT[condition].get(lang, CONDITION_TEXT[condition]["en"])]
            if luxury:
                doc = rnd.choices(["luxury_docs", "luxury_box", "luxury_none"], weights=[45, 35, 20])[0]
                parts.append(EXTRAS[doc][lang])
            parts.append(EXTRAS["reason"][lang])
            ships = cat not in ("bicycles", "ebikes", "strollers") or rnd.random() < 0.3
            parts.append(EXTRAS["shipping" if ships else "pickup"][lang])
            if scenario in ("negotiation", "price_drop") and rnd.random() < 0.6:
                parts.append(EXTRAS["negotiable"][lang])

            # seller
            seller_rc = rnd.choice([0, 1, 2, 3, 5, 8, 12, 20, 35, 60, 110, 240])
            seller_age_days = rnd.uniform(60, 3000)
            rating = round(rnd.uniform(4.2, 5.0), 1) if seller_rc else None
            images = [f"https://demo.arbscan.local/img/{product['slug']}/{counter}-{k}.jpg" for k in range(rnd.randint(3, 8))]
            if scenario == "scam":
                parts = [rnd.choice(SCAM_TEXT[lang])]
                seller_rc = rnd.choice([0, 0, 1])
                rating = 5.0 if seller_rc else None
                seller_age_days = rnd.uniform(1, 9)
                if luxury and rnd.random() < 0.6:
                    images = [STOCK_HOSTS.get(cat, images[0])]
                elif out and rnd.random() < 0.5:
                    images = list(out[-1].raw.image_urls[:2])  # re-used photos
            description = " ".join(parts)

            city = rnd.choice(CITIES[country])
            ext = f"demo-{mp}-{counter:05d}"
            url_base = {
                "wallapop": "https://es.wallapop.com/item/",
                "leboncoin": "https://www.leboncoin.fr/ad/",
                "ebay_es": "https://www.ebay.es/itm/",
                "ebay_fr": "https://www.ebay.fr/itm/",
                "ebay_de": "https://www.ebay.de/itm/",
            }[mp]
            shipping_cost = None
            if mp.startswith("ebay") and ships:
                shipping_cost = rnd.choice([0.0, 4.99, 6.95, 9.9, 14.9])
            raw = RawListing(
                marketplace=mp,
                external_id=ext,
                url=f"{url_base}{ext}",
                title=title,
                description=description,
                price=float(price),
                currency="EUR",
                country=country,
                city=city,
                seller_id=f"{mp}:{rnd.choice(SELLERS[country])}{counter % 97}",
                seller_name=rnd.choice(SELLERS[country]),
                seller_rating=rating,
                seller_rating_count=seller_rc,
                seller_account_created_at=now - timedelta(days=seller_age_days),
                seller_type="private" if rnd.random() > 0.08 else "professional",
                condition_raw=None,
                category_raw=categories[cat]["name"],
                published_at=published,
                shipping_available=ships,
                shipping_cost=shipping_cost,
                image_urls=images,
                status="ended" if ended else "active",
                source_metadata={"demo_scenario": scenario, "demo_product": product["slug"]},
            )
            timeline: list[tuple[datetime, float]] = []
            if scenario == "price_drop":
                p0 = round(price * rnd.uniform(1.18, 1.32), -1)
                p1 = round((p0 + price) / 2, -1)
                timeline = [
                    (published, p0),
                    (published + (now - published) * 0.45, p1),
                    (now - timedelta(hours=rnd.uniform(2, 60)), float(price)),
                ]
            elif scenario == "negotiation" and rnd.random() < 0.5:
                timeline = [(published, round(price * 1.08, -1)), (published + (now - published) * 0.6, float(price))]
            out.append(DemoListing(raw=raw, scenario=scenario, first_seen_at=published + timedelta(minutes=rnd.uniform(1, 20)), price_timeline=timeline, ended_at=ended_at))
    return out


def generate_live_listing(rnd: random.Random, now: datetime | None = None) -> DemoListing:
    """One fresh listing for the demo feed connector (simulates a live scan)."""
    now = now or datetime.now(UTC)
    items = generate_demo_listings(seed=rnd.randint(1, 10_000_000), per_product=1, now=now)
    active = [d for d in items if d.raw.status == "active"]
    d = rnd.choice(active)
    d.raw.published_at = now - timedelta(minutes=rnd.uniform(1, 25))
    d.first_seen_at = now
    d.price_timeline = []
    d.raw.external_id = f"live-{int(now.timestamp())}-{rnd.randint(1000, 9999)}"
    d.raw.url = d.raw.url.rsplit("/", 1)[0] + "/" + d.raw.external_id
    return d
