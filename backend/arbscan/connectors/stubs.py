"""Marketplaces without a compliant automated integration (yet).

These are registered so the rest of the system (manual entry, CSV import, fee rules,
valuation, alerts) works for them today. Each documents *why* it is a stub and the best
compliant alternative. See docs/connectors.md for details.
"""

from __future__ import annotations

from arbscan.connectors.base import ComplianceInfo, StubConnector


class WallapopConnector(StubConnector):
    key = "wallapop"
    display_name = "Wallapop"
    countries = ["ES"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary=(
            "No public/partner API for searching listings. Wallapop's terms prohibit automated "
            "extraction, and the web app relies on private, undocumented endpoints - not used."
        ),
        docs_url="https://about.wallapop.com/condiciones-de-uso/",
        alternative=(
            "Use Wallapop's own saved searches + push/e-mail notifications, then paste the listing URL "
            "into Manual entry (one user-initiated fetch of public page metadata, robots.txt respected), "
            "or import a CSV. Ask Wallapop for a partner/data agreement for automated access."
        ),
    )


class LeboncoinConnector(StubConnector):
    key = "leboncoin"
    display_name = "Leboncoin"
    countries = ["FR"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary=(
            "No public search API (the Leboncoin API is for professional ad *publishing*). Terms "
            "forbid scraping and the site uses anti-bot protection - circumventing it is not done."
        ),
        docs_url="https://www.leboncoin.fr/dc/cgu",
        alternative=(
            "Create Leboncoin saved searches with e-mail alerts and paste interesting URLs into Manual "
            "entry, or CSV-import. A future connector could parse your own alert e-mails (IMAP)."
        ),
    )


class VintedConnector(StubConnector):
    key = "vinted"
    display_name = "Vinted"
    countries = ["ES", "FR", "DE", "IT"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public listing-search API; terms prohibit scraping.",
        docs_url="https://www.vinted.es/terms_and_conditions",
        alternative="Saved searches + notifications in the Vinted app, manual entry / CSV import.",
    )


class KleinanzeigenConnector(StubConnector):
    key = "kleinanzeigen"
    display_name = "Kleinanzeigen (DE)"
    countries = ["DE"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public search API; terms prohibit automated access.",
        docs_url="https://themen.kleinanzeigen.de/nutzungsbedingungen/",
        alternative="Use 'Suchauftrag' e-mail alerts, then manual entry / CSV import.",
    )


class MilanunciosConnector(StubConnector):
    key = "milanuncios"
    display_name = "Milanuncios"
    countries = ["ES"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public search API; anti-bot protection in place; terms prohibit scraping.",
        docs_url="https://www.milanuncios.com/terminos-y-condiciones-de-uso.htm",
        alternative="Saved-search alerts + manual entry / CSV import.",
    )


class VestiaireConnector(StubConnector):
    key = "vestiaire"
    display_name = "Vestiaire Collective"
    countries = ["FR", "ES", "IT", "DE"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public API for listings; terms prohibit scraping.",
        docs_url="https://www.vestiairecollective.com/terms/",
        alternative="Use as a *resale* channel (fee rule seeded) and for manual price checks.",
    )


class Chrono24Connector(StubConnector):
    key = "chrono24"
    display_name = "Chrono24"
    countries = ["DE", "ES", "FR", "IT"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public search API for third parties; terms prohibit scraping.",
        docs_url="https://www.chrono24.com/info/terms.htm",
        alternative="Manual entry of reference prices; Chrono24 dealer tools if you become a dealer.",
    )


class CatawikiConnector(StubConnector):
    key = "catawiki"
    display_name = "Catawiki"
    countries = ["NL", "ES", "FR", "DE", "IT"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="No public API for auctions/results; terms prohibit scraping.",
        docs_url="https://www.catawiki.com/en/help/terms-of-use",
        alternative="Manually record hammer prices as SOLD comparables (CSV import supports price_kind=sold).",
    )


class FacebookMarketplaceConnector(StubConnector):
    key = "facebook"
    display_name = "Facebook Marketplace"
    countries = ["ES", "FR", "DE", "IT"]
    compliance = ComplianceInfo(
        method="disabled",
        summary="Meta provides no Marketplace search API for third parties and prohibits automated collection.",
        docs_url="https://www.facebook.com/policies/marketplace",
        alternative="Manual entry only.",
    )


class AmazonConnector(StubConnector):
    key = "amazon"
    display_name = "Amazon (ES/FR/DE/IT)"
    countries = ["ES", "FR", "DE", "IT"]
    compliance = ComplianceInfo(
        method="official_api",
        summary=(
            "Official Product Advertising API exists but requires an approved Amazon Associates account "
            "(with qualifying sales) and its own licence terms. Not implemented yet."
        ),
        docs_url="https://webservices.amazon.com/paapi5/documentation/",
        alternative="Useful as a *new-price ceiling* reference. Implement once Associates credentials are available; check the current API status/successor first.",
        requires_credentials=True,
    )


class ManualConnector(StubConnector):
    key = "manual"
    display_name = "Manual / other marketplace"
    countries = ["ES", "FR", "DE", "IT", "PT", "GB"]
    compliance = ComplianceInfo(
        method="manual_only",
        summary="Listings entered by hand or imported from CSV.",
    )
