"""Canonical identity resolution at artifact parse boundaries."""
from __future__ import annotations
import re
import unicodedata

CONCEPT_ALIASES: dict[str, tuple[str, ...]] = {
    "concept:pwa": ("pwa", "progressive web app", "progressive web application", "progressive web application pwa", "installable web app"),
    "concept:native-app": ("native app", "native application", "native mobile app", "native mobile application"),
    "concept:web-app": ("web app", "web application", "browser app", "browser application"),
    "concept:web-native-bridge": ("web plus native bridge", "web native bridge", "hybrid app", "hybrid application"),
}

def normalize_identity(value: str) -> str:
    """Case-fold and collapse every punctuation/space run once, at ingress."""
    folded = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")

_CONCEPT_BY_ALIAS = {normalize_identity(a): cid for cid, aliases in CONCEPT_ALIASES.items() for a in aliases}

def canonical_concept_id(value: str) -> str:
    normalized = normalize_identity(value)
    return _CONCEPT_BY_ALIAS.get(normalized, f"concept:{normalized}")

def canonical_technology_id(name: str) -> str:
    return f"tech:{normalize_identity(name)}"
