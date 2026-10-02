"""Currency conversion. EUR is the base currency.

Rates are stored in ``exchange_rates`` (append-only). Static fallback rates are seeded;
optionally the ECB euro foreign exchange reference rates feed
(https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml, a public, documented
feed) refreshes them daily when ``FX_AUTO_UPDATE=true``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.core.http import PoliteClient
from arbscan.core.logging import get_logger
from arbscan.db.models import ExchangeRate

log = get_logger(__name__)

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

# Fallback rates: EUR per 1 unit of currency. Approximate; replaced by ECB data when enabled.
STATIC_EUR_PER_UNIT = {"EUR": 1.0, "GBP": 1.17, "CHF": 1.06, "USD": 0.92, "SEK": 0.087, "DKK": 0.134, "PLN": 0.232, "CZK": 0.040, "HUF": 0.0025, "JPY": 0.0061}


class FxService:
    def __init__(self, session: Session):
        self.session = session
        self._cache: dict[str, tuple[float, datetime]] = {}

    def rate(self, currency: str) -> tuple[float, datetime]:
        currency = (currency or "EUR").upper()
        if currency == "EUR":
            return 1.0, datetime.now(UTC)
        if currency in self._cache:
            return self._cache[currency]
        row = self.session.scalars(
            select(ExchangeRate).where(ExchangeRate.currency == currency).order_by(ExchangeRate.as_of.desc()).limit(1)
        ).first()
        if row:
            value = (row.eur_per_unit, row.as_of)
        elif currency in STATIC_EUR_PER_UNIT:
            value = (STATIC_EUR_PER_UNIT[currency], datetime(2025, 1, 1, tzinfo=UTC))
        else:
            raise ValueError(f"no exchange rate for {currency}")
        self._cache[currency] = value
        return value

    def to_eur(self, amount: float | None, currency: str) -> tuple[float | None, float, datetime]:
        rate, ts = self.rate(currency)
        if amount is None:
            return None, rate, ts
        return round(amount * rate, 2), rate, ts


def seed_static_rates(session: Session) -> None:
    if session.scalars(select(ExchangeRate).limit(1)).first():
        return
    for cur, rate in STATIC_EUR_PER_UNIT.items():
        if cur != "EUR":
            session.add(ExchangeRate(currency=cur, eur_per_unit=rate, as_of=datetime(2025, 1, 1, tzinfo=UTC), source="static"))


def parse_ecb_xml(xml_text: str) -> tuple[datetime, dict[str, float]]:
    root = ET.fromstring(xml_text)
    ns = {"e": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    day = root.find(".//e:Cube[@time]", ns)
    if day is None:
        raise ValueError("unexpected ECB format")
    as_of = datetime.fromisoformat(day.attrib["time"]).replace(tzinfo=UTC)
    rates = {}
    for cube in day.findall("e:Cube", ns):
        units_per_eur = float(cube.attrib["rate"])
        rates[cube.attrib["currency"]] = round(1 / units_per_eur, 8)
    return as_of, rates


def update_from_ecb(session: Session) -> int:
    client = PoliteClient("ecb", requests_per_minute=2, enforce_robots=False)
    try:
        as_of, rates = parse_ecb_xml(client.get(ECB_URL).text)
    finally:
        client.close()
    for cur, rate in rates.items():
        session.add(ExchangeRate(currency=cur, eur_per_unit=rate, as_of=as_of, source="ecb"))
    log.info("fx rates updated", extra={"n": len(rates), "as_of": as_of.isoformat()})
    return len(rates)
