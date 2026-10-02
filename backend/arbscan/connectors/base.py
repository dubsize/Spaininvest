"""Connector interface.

Every marketplace is an independent connector implementing:

* ``search(query)``           -> list[RawListing]
* ``get_listing(external_id)`` -> RawListing | None
* ``normalize_listing(payload)`` -> RawListing   (pure parser, unit-tested with fixtures)
* ``health_check()``          -> HealthStatus

Connectors only *collect*; product normalisation, valuation, scoring and alerts are
marketplace-agnostic and live in the pipeline.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, ClassVar


class ConnectorError(Exception):
    pass


class ConnectorNotConfigured(ConnectorError):
    pass


class ConnectorDisabled(ConnectorError):
    pass


class LayoutChanged(ConnectorError):
    """Raised when an HTML/JSON source no longer has the structure the parser expects."""


@dataclass
class ComplianceInfo:
    method: str  # official_api | public_feed | permitted_page | manual_only | disabled
    summary: str
    docs_url: str = ""
    alternative: str = ""
    requires_credentials: bool = False


@dataclass
class SearchQuery:
    keywords: str
    category_hint: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    limit: int = 50
    sort: str = "newly_listed"
    include_sold: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawListing:
    marketplace: str
    external_id: str
    url: str
    title: str
    price: float
    currency: str = "EUR"
    country: str = "ES"
    description: str = ""
    original_price: float | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    seller_id: str | None = None
    seller_name: str | None = None
    seller_rating: float | None = None  # 0..5
    seller_rating_count: int | None = None
    seller_account_created_at: datetime | None = None
    seller_type: str | None = None
    seller_listing_count: int | None = None
    condition_raw: str | None = None
    category_raw: str | None = None
    brand_raw: str | None = None
    model_raw: str | None = None
    published_at: datetime | None = None
    shipping_available: bool | None = None
    shipping_cost: float | None = None
    image_urls: list[str] = field(default_factory=list)
    status: str = "active"  # active | sold | ended | reserved
    price_kind: str = "asking"  # asking | sold
    sold_price: float | None = None
    sold_at: datetime | None = None
    raw: dict[str, Any] | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        """Hash of the fields whose change matters (used to detect updates)."""
        key = {
            "t": self.title,
            "d": (self.description or "")[:2000],
            "p": self.price,
            "c": self.currency,
            "s": self.status,
            "i": self.image_urls[:3],
        }
        return hashlib.sha256(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthStatus:
    status: str  # OK | DEGRADED | ERROR | DISABLED | NOT_CONFIGURED | STUB
    message: str = ""
    latency_ms: int | None = None


class Connector(ABC):
    key: ClassVar[str]
    display_name: ClassVar[str]
    countries: ClassVar[list[str]] = []
    compliance: ClassVar[ComplianceInfo]
    supports_sold_data: ClassVar[bool] = False
    default_poll_seconds: ClassVar[int] = 900
    default_requests_per_minute: ClassVar[int] = 10

    def __init__(self, marketplace_code: str, config: dict[str, Any] | None = None):
        self.marketplace_code = marketplace_code
        self.config = config or {}

    # -- capability --------------------------------------------------------
    def is_configured(self) -> bool:
        return True

    @property
    def is_stub(self) -> bool:
        return False

    # -- interface -----------------------------------------------------------
    @abstractmethod
    def search(self, query: SearchQuery) -> list[RawListing]: ...

    @abstractmethod
    def get_listing(self, external_id: str) -> RawListing | None: ...

    @abstractmethod
    def normalize_listing(self, payload: dict[str, Any]) -> RawListing: ...

    @abstractmethod
    def health_check(self) -> HealthStatus: ...

    def search_sold(self, query: SearchQuery) -> list[RawListing]:
        """Completed-sale data, where the marketplace offers it compliantly."""
        return []

    def close(self) -> None:  # pragma: no cover - optional
        pass


class StubConnector(Connector):
    """Placeholder for a marketplace with no compliant automated access (yet).
    The marketplace still works through manual entry / CSV import."""

    @property
    def is_stub(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return False

    def search(self, query: SearchQuery) -> list[RawListing]:
        raise ConnectorDisabled(f"{self.display_name}: {self.compliance.summary}")

    def get_listing(self, external_id: str) -> RawListing | None:
        raise ConnectorDisabled(f"{self.display_name}: automated access not implemented")

    def normalize_listing(self, payload: dict[str, Any]) -> RawListing:
        """Stubs still accept *manually supplied* payloads (manual entry / CSV)."""
        return RawListing(
            marketplace=self.marketplace_code,
            external_id=str(payload.get("external_id") or payload.get("id")),
            url=str(payload.get("url", "")),
            title=str(payload.get("title", "")),
            price=float(payload.get("price", 0)),
            currency=str(payload.get("currency", "EUR")),
            country=str(payload.get("country", (self.countries or ["ES"])[0])),
            description=str(payload.get("description", "")),
        )

    def health_check(self) -> HealthStatus:
        return HealthStatus("STUB", self.compliance.summary)
