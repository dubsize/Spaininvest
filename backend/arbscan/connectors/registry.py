"""Connector registry: connector_key -> class. Marketplaces (DB rows) reference a key
plus per-marketplace config, so e.g. eBay ES/FR/DE share one implementation."""

from __future__ import annotations

from typing import Any

from arbscan.connectors.base import Connector
from arbscan.connectors.demo_feed import DemoFeedConnector
from arbscan.connectors.ebay import EbayBrowseConnector
from arbscan.connectors.stubs import (
    AmazonConnector,
    CatawikiConnector,
    Chrono24Connector,
    FacebookMarketplaceConnector,
    KleinanzeigenConnector,
    LeboncoinConnector,
    ManualConnector,
    MilanunciosConnector,
    VestiaireConnector,
    VintedConnector,
    WallapopConnector,
)

CONNECTORS: dict[str, type[Connector]] = {
    c.key: c
    for c in (
        EbayBrowseConnector,
        WallapopConnector,
        LeboncoinConnector,
        VintedConnector,
        KleinanzeigenConnector,
        MilanunciosConnector,
        VestiaireConnector,
        Chrono24Connector,
        CatawikiConnector,
        FacebookMarketplaceConnector,
        AmazonConnector,
        ManualConnector,
        DemoFeedConnector,
    )
}


def build_connector(connector_key: str, marketplace_code: str, config: dict[str, Any] | None = None) -> Connector:
    cls = CONNECTORS.get(connector_key)
    if cls is None:
        raise KeyError(f"unknown connector '{connector_key}'")
    return cls(marketplace_code, config or {})


# Seed definition of marketplaces (code, name, country, connector key, base url, config, enabled)
MARKETPLACE_SEED: list[dict[str, Any]] = [
    {"code": "wallapop", "name": "Wallapop", "country": "ES", "connector_key": "wallapop", "base_url": "https://es.wallapop.com"},
    {"code": "leboncoin", "name": "Leboncoin", "country": "FR", "connector_key": "leboncoin", "base_url": "https://www.leboncoin.fr"},
    {"code": "ebay_es", "name": "eBay España", "country": "ES", "connector_key": "ebay", "base_url": "https://www.ebay.es", "config": {"ebay_marketplace_id": "EBAY_ES", "country": "ES"}, "enabled": True, "poll_interval_seconds": 600, "max_requests_per_minute": 30},
    {"code": "ebay_fr", "name": "eBay France", "country": "FR", "connector_key": "ebay", "base_url": "https://www.ebay.fr", "config": {"ebay_marketplace_id": "EBAY_FR", "country": "FR"}, "enabled": True, "poll_interval_seconds": 600, "max_requests_per_minute": 30},
    {"code": "ebay_de", "name": "eBay Deutschland", "country": "DE", "connector_key": "ebay", "base_url": "https://www.ebay.de", "config": {"ebay_marketplace_id": "EBAY_DE", "country": "DE"}, "enabled": True, "poll_interval_seconds": 600, "max_requests_per_minute": 30},
    {"code": "ebay_it", "name": "eBay Italia", "country": "IT", "connector_key": "ebay", "base_url": "https://www.ebay.it", "config": {"ebay_marketplace_id": "EBAY_IT", "country": "IT"}, "enabled": False, "poll_interval_seconds": 900},
    {"code": "vinted_es", "name": "Vinted España", "country": "ES", "connector_key": "vinted", "base_url": "https://www.vinted.es"},
    {"code": "vinted_fr", "name": "Vinted France", "country": "FR", "connector_key": "vinted", "base_url": "https://www.vinted.fr"},
    {"code": "vinted_de", "name": "Vinted Deutschland", "country": "DE", "connector_key": "vinted", "base_url": "https://www.vinted.de"},
    {"code": "vinted_it", "name": "Vinted Italia", "country": "IT", "connector_key": "vinted", "base_url": "https://www.vinted.it"},
    {"code": "kleinanzeigen", "name": "Kleinanzeigen", "country": "DE", "connector_key": "kleinanzeigen", "base_url": "https://www.kleinanzeigen.de"},
    {"code": "milanuncios", "name": "Milanuncios", "country": "ES", "connector_key": "milanuncios", "base_url": "https://www.milanuncios.com"},
    {"code": "vestiaire", "name": "Vestiaire Collective", "country": "FR", "connector_key": "vestiaire", "base_url": "https://www.vestiairecollective.com"},
    {"code": "chrono24", "name": "Chrono24", "country": "DE", "connector_key": "chrono24", "base_url": "https://www.chrono24.com"},
    {"code": "catawiki", "name": "Catawiki", "country": "NL", "connector_key": "catawiki", "base_url": "https://www.catawiki.com"},
    {"code": "facebook", "name": "Facebook Marketplace", "country": "ES", "connector_key": "facebook", "base_url": "https://www.facebook.com/marketplace"},
    {"code": "amazon_es", "name": "Amazon.es", "country": "ES", "connector_key": "amazon", "base_url": "https://www.amazon.es"},
    {"code": "amazon_fr", "name": "Amazon.fr", "country": "FR", "connector_key": "amazon", "base_url": "https://www.amazon.fr"},
    {"code": "amazon_de", "name": "Amazon.de", "country": "DE", "connector_key": "amazon", "base_url": "https://www.amazon.de"},
    {"code": "amazon_it", "name": "Amazon.it", "country": "IT", "connector_key": "amazon", "base_url": "https://www.amazon.it"},
    {"code": "manual", "name": "Manual / other", "country": "ES", "connector_key": "manual", "base_url": ""},
    {"code": "demo_feed", "name": "Demo feed", "country": "ES", "connector_key": "demo", "base_url": "", "enabled": True, "poll_interval_seconds": 300},
]
