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
    # Algorithms and algorithm families express required properties and are
    # allowed. Binding technology choices remain lintable unless exemplary.
    ("named_technology", re.compile(r"\b(?:oauth|jwt|saml|openid|postgres(?:ql)?|mysql|mongodb|redis|kafka|rabbitmq|kubernetes|docker|graphql|grpc|websocket|elasticsearch|spark|hadoop|snowflake)\b", re.I)),
    ("http_verb", re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)(?=\s+/(?:api/)?|\s+(?:request|endpoint))")),
    # A bare 3-digit number is not an HTTP status ("within 200 ms"). It needs an HTTP cue
    # (see _http_status_context): a status word after it, or "HTTP/status/returns/responds with" before it.
    ("http_status", re.compile(r"\b[1-5]\d\d(?:\s+(?:Unauthorized|OK|Found|Error|Created))?\b", re.I)),
    ("url_path", re.compile(r"/(?:api/)?[a-z0-9_{}-]+(?:/[a-z0-9_{}-]+)+", re.I)),
    ("json_shape", re.compile(r"\bJSON\b|\{\s*[\"'][^}]+\}", re.I)),
    ("database", re.compile(r"\b(?:database|table|column|row|SQL)\b", re.I)),
    ("ui_widget", re.compile(r"\b(?:button|text field|checkbox|dropdown|modal|widget)\b", re.I)),
)


_STATUS_WORD = re.compile(r"^\d{3}\s+(?:Unauthorized|OK|Found|Error|Created)$", re.I)
_STATUS_CUE = re.compile(r"(?:\bhttp(?:/\d(?:\.\d)?)?|\bstatus(?:\s+code)?|\bresponse\s+code|\breturns?|\bresponds?\s+with|\bresult(?:s|ing)?\s+in)\s*:?\s*$", re.I)
_TIME_UNIT = re.compile(r"^\s*(?:ms|milliseconds?|seconds?|secs?|s|minutes?|mins?|hours?|hz|fps|kb|mb|gb|px|%)\b", re.I)


def _http_status_context(text: str, match) -> bool:
    if _STATUS_WORD.match(match.group(0).strip()):
        return True
    if _TIME_UNIT.match(text[match.end():match.end() + 14]):
        return False
    return bool(_STATUS_CUE.search(text[max(0, match.start() - 24):match.start()]))


def _in_corpus(token: str, corpus_lower: str) -> bool:
    """Numbers match as whole numbers ('200' is not found inside '2000'); words match as substrings."""
    t = token.lower()
    if re.fullmatch(r"\d+(?:\.\d+)?%?", t):
        return re.search(r"(?<![\d.])" + re.escape(t.rstrip("%")) + r"(?![\d])", corpus_lower) is not None
    return t in corpus_lower


def _invention_candidate(token: str, field: str, text: str, start: int) -> bool:
    """Would an unsupported `token` be a signal of an invented detail? Ordinary Title Case words in
    a title ('Required', 'Capability') are not: titles capitalize every word. Numbers, acronyms,
    CamelCase / digit-bearing names, and capitalized words in running text still are."""
    if re.fullmatch(r"\d+(?:\.\d+)?%?", token):
        return True
    if field != "title":
        return True
    return token.isupper() or bool(re.search(r"\d", token)) or bool(re.search(r"[a-z][A-Z]", token))


def srs_draft_findings(draft: dict, interview_text: str) -> list[dict]:
    """Find binding solution language, inventions, and non-EARS requirements.
    `interview_text` is every source the founder's meaning lives in (intent model, needs, concept of operations)."""
    findings = []
    source_lower = interview_text.lower()
    common_sentence_words = {"each", "upon", "management", "resolution", "when", "while", "if", "then",
                             "where", "after", "before", "the", "system", "user", "users"}
    exemplar = re.compile(r"\b(?:like|such as|e\.g\.|for example)\b", re.I)
    ears = re.compile(r"^(?:(?:The )?.+ shall .+|When .+, (?:the )?.+ shall .+|While .+, (?:the )?.+ shall .+|If .+, then (?:the )?.+ shall .+)$", re.I)
    for section in ("functional", "non_functional"):
        for requirement in draft.get(section) or []:
            rid = str(requirement.get("requirement_id") or "?")
            statement = str(requirement.get("statement") or "").strip()
            if statement and not ears.match(statement):
                findings.append({"kind":"structure","rule":"ears_pattern",
                    "location":f"{rid} field statement","span":statement,
                    "expected":"The <system> shall <response>; When <trigger>, the <system> shall <response>; While <state>, ...; or If <condition>, then the <system> shall ..."})
            values = [("title", str(requirement.get("title") or "")), ("statement", statement)]
            values += [(f"acceptance.{item.get('criterion_id','?')}", str(item.get("statement") or ""))
                       for item in requirement.get("acceptance") or []]
            for field, text in values:
                seen = set()
                for rule, pattern in SRS_SOLUTION_RULES:
                    for match in pattern.finditer(text):
                        prefix = text[max(0, match.start()-24):match.start()]
                        if exemplar.search(prefix):
                            continue
                        if rule == "http_status" and not _http_status_context(text, match):
                            continue
                        span = match.group(0); key = (rule, span.lower())
                        if key not in seen:
                            seen.add(key); findings.append({"kind":"solution_language","rule":rule,
                                "location":f"{rid} field {field}","span":span})
                for match in re.finditer(r"\b\d+(?:\.\d+)?%?\b|\b[A-Z][A-Za-z0-9-]{2,}\b", text):
                    token=match.group(0); lower=token.lower()
                    sentence_initial = match.start()==0 or text[max(0,match.start()-2):match.start()].endswith(". ")
                    if lower in common_sentence_words or (sentence_initial and lower.isalpha() and lower not in source_lower):
                        continue
                    if not _in_corpus(token, source_lower) and _invention_candidate(token, field, text, match.start()):
                        findings.append({"kind":"potential_invention","rule":"absent_from_interview",
                            "location":f"{rid} field {field}","span":token})
    return findings

