"""Deterministic text QA guards, shared by every engine (ADR-0015 doctrine:
prompt discipline failed repeatedly; these checks are MECHANICAL).

Promoted from interview-engine in v0.6.0 so the interview engine and the spec
generator enforce the SAME rules from one implementation:
- is_solution_language / names_technology: a requirement or criterion must be
  an observable check on stakeholder language, not a design decision.
- grounded_in: text that shares no vocabulary with what the founder actually
  said is an invention ("portfolio of case studies") - the tell is zero overlap.
"""
from __future__ import annotations

import re

_STOP = {
    "the", "and", "for", "with", "must", "shall", "should", "will", "would", "have", "has",
    "this", "that", "these", "those", "from", "into", "your", "their", "them", "they",
    "when", "what", "which", "keep", "make", "made", "need", "needs", "able", "about",
    "over", "such", "than", "then", "also", "only", "very", "more", "most",
    "some", "any", "all", "each", "other", "there", "here", "where", "while", "being",
    "been", "are", "was", "were", "not", "can", "could", "may", "might", "per", "via", "out", "off", "way", "easily", "easy",
}


def content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9\-]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def shared_words(a: set[str], b: set[str]) -> set[str]:
    """Overlap with light stemming: 'predict' catches 'predictive'."""
    out = set()
    for w in a:
        if w in b or any(len(w) >= 5 and (x.startswith(w) or w.startswith(x)) for x in b if len(x) >= 5):
            out.add(w)
    return out


_SOLUTION_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+/|\bHTTP\b|\b[1-5]\d\d\s+(Unauthorized|OK|Found|Error|Created)"
    r"|/api/|endpoint|json response|status code|\bSQL\b|database table|button|text field|click",
    re.IGNORECASE,
)

_TECH_RE = re.compile(
    r"\b[A-Z]{2,}[-]?\d{2,}\b"  # AES-256, SHA256, RSA-2048, TLS1.3-style cipher/version names
    r"|\b(oauth|jwt|bcrypt|scrypt|argon2|saml|openid|postgres(?:ql)?|mysql|mongodb|redis|kafka|"
    r"rabbitmq|kubernetes|docker|graphql|grpc|websocket|elasticsearch|spark|hadoop|snowflake)\b",
    re.IGNORECASE,
)


def names_technology(text: str) -> bool:
    """True when text names a specific technology/algorithm instead of an
    observable property ('encrypted' is a check; 'AES-256' is a design)."""
    return bool(_TECH_RE.search(text))


def is_solution_language(text: str) -> bool:
    """True when a criterion/requirement names an implementation (endpoint,
    status code, UI widget, named technology) instead of observable behavior."""
    return bool(_SOLUTION_RE.search(text)) or names_technology(text)


def grounded_in(text: str, source_texts: list[str]) -> bool:
    """True when the text shares at least one content word with the founder's
    own language. Invented details share none."""
    sw = content_words(text)
    if not sw:
        return True  # too generic to flag
    src = content_words(" ".join(source_texts))
    return bool(shared_words(sw, src))
