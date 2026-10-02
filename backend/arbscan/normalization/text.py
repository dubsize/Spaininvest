"""Text helpers: accent folding, tokenisation, light-weight language detection, sanitising."""

from __future__ import annotations

import html
import re
import unicodedata

_WS = re.compile(r"\s+")
_TAGS = re.compile(r"<[^>]+>")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def fold(text: str | None) -> str:
    """Lower-case, strip accents, collapse whitespace. ``"Pulsera Cartier LOVE – oro"`` -> ``"pulsera cartier love - oro"``."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ß", "ss").replace("–", "-").replace("—", "-").replace("’", "'")
    return _WS.sub(" ", text.lower()).strip()


def compact(text: str) -> str:
    """Remove everything that is not alphanumeric (used for reference numbers)."""
    return re.sub(r"[^a-z0-9]", "", fold(text))


def sanitize_text(text: str | None, max_len: int = 20000) -> str:
    """Strip markup/control chars from scraped content. Content is always rendered as text
    in the UI (never as HTML), this is defence in depth."""
    if not text:
        return ""
    text = html.unescape(str(text))
    text = _TAGS.sub(" ", text)
    text = _CTRL.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:max_len]


_STOPWORDS: dict[str, set[str]] = {
    "es": {"de", "el", "la", "con", "para", "en", "muy", "estado", "vendo", "nuevo", "y", "los", "las", "sin", "por"},
    "fr": {"le", "la", "les", "avec", "pour", "et", "en", "très", "tres", "etat", "état", "vends", "neuf", "sans", "du"},
    "de": {"der", "die", "das", "mit", "und", "für", "fur", "neu", "zustand", "verkaufe", "ohne", "sehr", "gut", "ist"},
    "it": {"il", "lo", "con", "per", "e", "di", "nuovo", "usato", "vendo", "senza", "ottime", "condizioni", "della"},
    "pt": {"o", "com", "para", "em", "novo", "usado", "estado", "vendo", "sem", "muito", "bom", "do", "da"},
    "en": {"the", "with", "for", "and", "new", "used", "condition", "selling", "without", "very", "good", "of"},
}


def detect_language(text: str) -> str | None:
    tokens = re.findall(r"[a-zà-ÿ]+", (text or "").lower())
    if not tokens:
        return None
    scores = {lang: sum(1 for t in tokens if t in words) for lang, words in _STOPWORDS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else None
