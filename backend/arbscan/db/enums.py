"""Domain enumerations. Stored as plain strings in the database for migration-friendliness."""

from __future__ import annotations

from enum import StrEnum


class Condition(StrEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    FOR_PARTS = "for_parts"
    UNKNOWN = "unknown"


class ListingStatus(StrEnum):
    ACTIVE = "active"
    SOLD = "sold"  # confirmed sold (completed transaction data)
    ENDED = "ended"  # disappeared / ended, outcome unknown
    RESERVED = "reserved"


class PriceKind(StrEnum):
    ASKING = "asking"
    SOLD = "sold"


class OpportunityType(StrEnum):
    FLIP = "FLIP"  # intra-market flip (buy & resell in same country)
    CROSS_BORDER = "CROSS_BORDER"  # buy abroad, resell in resale market
    NEGOTIATION = "NEGOTIATION"  # currently above max buy but likely negotiable
    NONE = "NONE"  # evaluated, not an opportunity


class DealStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    WATCHING = "WATCHING"
    CONTACTED = "CONTACTED"
    NEGOTIATING = "NEGOTIATING"
    PURCHASED = "PURCHASED"
    RECEIVED = "RECEIVED"
    LISTED_FOR_RESALE = "LISTED_FOR_RESALE"
    SOLD = "SOLD"
    REJECTED = "REJECTED"
    SCAM_RISK = "SCAM_RISK"
    EXPIRED = "EXPIRED"


# Statuses where capital is deployed (inventory held)
INVENTORY_STATUSES = {DealStatus.PURCHASED, DealStatus.RECEIVED, DealStatus.LISTED_FOR_RESALE}


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class ConnectorStatus(StrEnum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    STUB = "STUB"


class ScanPriority(StrEnum):
    HIGH = "high"
    STANDARD = "standard"
    BACKGROUND = "background"


class ListingSource(StrEnum):
    CONNECTOR = "connector"
    MANUAL = "manual"
    CSV = "csv"
    DEMO = "demo"


class FeeSide(StrEnum):
    SELL = "sell"
    BUY = "buy"
