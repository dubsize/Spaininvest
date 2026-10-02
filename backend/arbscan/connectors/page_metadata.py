"""Single-page public metadata extraction for *manual entry*.

When you paste a listing URL, the system may (if you tick "fetch details") perform ONE
user-initiated GET of that page, only if robots.txt allows it, and read the public
OpenGraph / schema.org JSON-LD metadata that sites publish for link previews. No
crawling, no pagination, no login, no anti-bot circumvention. If the fetch is refused or
fails, the form simply stays empty for manual completion.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from arbscan.connectors.base import LayoutChanged
from arbscan.core.http import PoliteClient, RobotsDisallowed
from arbscan.normalization.text import sanitize_text

DOMAIN_MARKETPLACES: list[tuple[str, str, str]] = [
    # (domain suffix, marketplace code, country)
    ("wallapop.com", "wallapop", "ES"),
    ("leboncoin.fr", "leboncoin", "FR"),
    ("ebay.es", "ebay_es", "ES"),
    ("ebay.fr", "ebay_fr", "FR"),
    ("ebay.de", "ebay_de", "DE"),
    ("ebay.it", "ebay_it", "IT"),
    ("vinted.es", "vinted_es", "ES"),
    ("vinted.fr", "vinted_fr", "FR"),
    ("vinted.de", "vinted_de", "DE"),
    ("vinted.it", "vinted_it", "IT"),
    ("kleinanzeigen.de", "kleinanzeigen", "DE"),
    ("milanuncios.com", "milanuncios", "ES"),
    ("vestiairecollective.com", "vestiaire", "FR"),
    ("chrono24.", "chrono24", "DE"),
    ("catawiki.", "catawiki", "NL"),
    ("facebook.com", "facebook", "ES"),
    ("amazon.es", "amazon_es", "ES"),
    ("amazon.fr", "amazon_fr", "FR"),
    ("amazon.de", "amazon_de", "DE"),
    ("amazon.it", "amazon_it", "IT"),
]


def detect_marketplace(url: str) -> tuple[str, str | None]:
    host = (urlparse(url).hostname or "").lower()
    for suffix, code, country in DOMAIN_MARKETPLACES:
        if host.endswith(suffix) or (suffix.endswith(".") and suffix in host):
            return code, country
    return "manual", None


def external_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    m = re.search(r"(\d{6,})", path)
    if m:
        return m.group(1)
    return (path.rsplit("/", 1)[-1] or urlparse(url).netloc)[:120]


@dataclass
class PageMetadata:
    url: str
    title: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    image_urls: list[str] = field(default_factory=list)
    brand: str | None = None
    condition: str | None = None
    fetched: bool = False
    error: str | None = None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    s = str(value).replace("\xa0", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(re.sub(r"[^0-9.]", "", s))
    except ValueError:
        return None


def parse_metadata(html: str, url: str) -> PageMetadata:
    soup = BeautifulSoup(html, "lxml")
    md = PageMetadata(url=url, fetched=True)

    def meta(*names: str) -> str | None:
        for n in names:
            tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
            if tag and tag.get("content"):
                return str(tag["content"])
        return None

    md.title = sanitize_text(meta("og:title", "twitter:title") or (soup.title.string if soup.title else None), 500) or None
    md.description = sanitize_text(meta("og:description", "description", "twitter:description")) or None
    md.price = _to_float(meta("product:price:amount", "og:price:amount"))
    md.currency = meta("product:price:currency", "og:price:currency")
    img = meta("og:image", "twitter:image")
    if img:
        md.image_urls.append(img)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for node in data if isinstance(data, list) else [data]:
            if not isinstance(node, dict):
                continue
            graph = node.get("@graph")
            for item in graph if isinstance(graph, list) else [node]:
                if not isinstance(item, dict) or "Product" not in str(item.get("@type")):
                    continue
                md.title = md.title or sanitize_text(item.get("name"), 500)
                md.description = md.description or sanitize_text(item.get("description"))
                brand = item.get("brand")
                md.brand = (brand.get("name") if isinstance(brand, dict) else brand) or md.brand
                offers = item.get("offers")
                offer = offers[0] if isinstance(offers, list) and offers else offers
                if isinstance(offer, dict):
                    md.price = md.price or _to_float(offer.get("price") or offer.get("lowPrice"))
                    md.currency = md.currency or offer.get("priceCurrency")
                    cond = str(offer.get("itemCondition") or "")
                    md.condition = cond.rsplit("/", 1)[-1] or None
                images = item.get("image")
                for im in images if isinstance(images, list) else [images]:
                    if isinstance(im, str) and im not in md.image_urls:
                        md.image_urls.append(im)
    if len(html) > 5000 and not md.title:
        raise LayoutChanged("page has content but no title metadata")
    md.image_urls = [u for u in md.image_urls if u.startswith("http")][:8]
    return md


def is_public_host(host: str) -> bool:
    """SSRF guard: only fetch hosts that resolve exclusively to public IP addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return bool(infos)


def fetch_metadata(url: str, client: PoliteClient | None = None) -> PageMetadata:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return PageMetadata(url=url, error="only http(s) URLs are supported")
    if client is None and not is_public_host(parsed.hostname):
        return PageMetadata(url=url, error="refusing to fetch a non-public address")
    client = client or PoliteClient("page-metadata", requests_per_minute=6)
    try:
        resp = client.get(url)
        if "html" not in resp.headers.get("content-type", "html"):
            return PageMetadata(url=url, error="not an HTML page")
        return parse_metadata(resp.text[:2_000_000], str(resp.url))
    except RobotsDisallowed:
        return PageMetadata(url=url, error="robots.txt disallows automated fetching of this page - please fill the fields manually")
    except Exception as exc:  # noqa: BLE001
        return PageMetadata(url=url, error=f"could not fetch page metadata: {exc}"[:300])
    finally:
        client.close()
