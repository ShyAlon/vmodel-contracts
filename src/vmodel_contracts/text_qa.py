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


# Recognized ecosystem names per area (ADR-0019 'verified' check). A founder
# preference naming something outside the list is KEPT but warned at the
# approval gate - niche-but-real exists; invented-and-confident is the enemy.
KNOWN_ECOSYSTEMS: dict[str, set[str]] = {
    "language": {"python", "node", "nodejs", "javascript", "typescript", "go", "golang", "rust",
                 "java", "kotlin", "ruby", "php", "c#", "csharp", ".net", "dotnet", "swift",
                 "scala", "elixir", "agnostic", "any", "no preference"},
    "cloud": {"aws", "amazon", "gcp", "google cloud", "azure", "firebase", "supabase", "vercel",
              "fly.io", "railway", "render", "heroku", "cloudflare", "on-prem", "onprem",
              "self-hosted", "none", "no cloud", "agnostic", "any"},
    "database": {"postgres", "postgresql", "mysql", "mariadb", "sqlite", "mongodb", "mongo",
                 "redis", "dynamodb", "firestore", "cassandra", "elastic", "elasticsearch",
                 "agnostic", "any"},
    "framework": {"django", "flask", "fastapi", "rails", "laravel", "express", "nestjs", "next",
                  "nextjs", "react", "vue", "svelte", "spring", "asp.net", "phoenix", "agnostic", "any"},
    "infrastructure": {"docker", "kubernetes", "k8s", "terraform", "serverless", "lambda",
                       "bare metal", "vms", "agnostic", "any"},
}


def ecosystem_recognized(area: str, preference: str) -> bool:
    """True when the preference names a known ecosystem entry for its area
    (substring-tolerant: 'we are locked into AWS' matches 'aws'). Unknown areas
    and empty preferences pass - the check only flags confident nonsense."""
    names = KNOWN_ECOSYSTEMS.get(area)
    if not names or not preference.strip():
        return True
    low = preference.lower()
    return any(name in low for name in names)


# Single shared rule table for pre-review SRS linting. Each match preserves the
# exact offending span so repair feedback and console evidence are actionable.
SRS_SOLUTION_RULES = (
    ("named_technology", _TECH_RE),
    ("http_verb", re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\b", re.I)),
    ("http_status", re.compile(r"\b[1-5]\d\d(?:\s+(?:Unauthorized|OK|Found|Error|Created))?\b", re.I)),
    ("url_path", re.compile(r"/(?:api/)?[a-z0-9_{}-]+(?:/[a-z0-9_{}-]+)+", re.I)),
    ("json_shape", re.compile(r"\bJSON\b|\{\s*[\"'][^}]+\}", re.I)),
    ("database", re.compile(r"\b(?:database|table|column|row|SQL)\b", re.I)),
    ("ui_widget", re.compile(r"\b(?:button|text field|checkbox|dropdown|modal|widget)\b", re.I)),
)


def srs_draft_findings(draft: dict, interview_text: str) -> list[dict]:
    """Find solution language and ungrounded numbers/entities before review."""
    findings = []
    source_lower = interview_text.lower()
    for section in ("functional", "non_functional"):
        for requirement in draft.get(section) or []:
            rid = str(requirement.get("requirement_id") or "?")
            values = [("title", str(requirement.get("title") or "")),
                      ("statement", str(requirement.get("statement") or ""))]
            values += [(f"acceptance.{item.get('criterion_id','?')}", str(item.get("statement") or ""))
                       for item in requirement.get("acceptance") or []]
            for field, text in values:
                seen = set()
                for rule, pattern in SRS_SOLUTION_RULES:
                    for match in pattern.finditer(text):
                        span = match.group(0)
                        key = (rule, span.lower())
                        if key not in seen:
                            seen.add(key); findings.append({"kind":"solution_language","rule":rule,
                                "location":f"{rid} field {field}","span":span})
                for token in re.findall(r"\b\d+(?:\.\d+)?%?\b|\b[A-Z][A-Za-z0-9-]{2,}\b", text):
                    if token.lower() not in source_lower and token.lower() not in {"the","system"}:
                        findings.append({"kind":"potential_invention","rule":"absent_from_interview",
                            "location":f"{rid} field {field}","span":token})
    return findings
