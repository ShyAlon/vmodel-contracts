"""Canonical, tuneable product-scope definition shared by intake consumers.

Scope wording and deterministic signal vocabulary live here, not in an LLM
prompt or module-local classifier. A future scope change is one contract-layer
edit plus tests; consumers import it verbatim.
"""
from __future__ import annotations

PRODUCT_SCOPE_DEFINITION = (
    "interactive applications - including games - delivered on web or mobile platforms"
)

# (regex, audit label). These are data consumed by the deterministic gate.
# Software qualifiers belong in-scope even when the domain is physical.
SCOPE_IN_SIGNALS: tuple[tuple[str, str], ...] = (
    (r"\b(web ?app|website|web platform|web application|saas|portal|dashboard|pwa)\b", "web application"),
    (r"\b(mobile app|native app|ios app|android app|app store|play store|swiftui|kotlin)\b", "mobile application"),
    (r"\b(game|gaming|pokemon|unity|unreal)\b", "interactive game"),
    (r"\b(marketplace|booking|storefront|checkout)\b", "interactive commerce pattern"),
    (r"\b(login|sign up|account|subscription)\b", "interactive account pattern"),
)

SCOPE_OUT_SIGNALS: tuple[tuple[str, str], ...] = (
    (r"\b(hardware|firmware|embedded|pcb|sensor|drone|vehicle|device)\b", "hardware or firmware product"),
    (r"\b(desktop-only|windows-only desktop|mac-only desktop)\b", "desktop-only application"),
    (r"\b(cli tool|command.line|dev.?tool sdk)\b", "CLI or developer tooling with no interactive web/mobile surface"),
    (r"\b(open|start|run|buy|own)\b[^.]{0,40}\b(bakery|restaurant|cafe|shop|logistics company|trucking company)\b", "non-software business"),
    (r"\b(bakery|restaurant|cafe|logistics company|trucking company)\b[^.]{0,40}\b(business|company|store)\b", "non-software business"),
)

SCOPE_DECLINE_PREFIX = (
    f"This service builds systems-engineering specs for {PRODUCT_SCOPE_DEFINITION}."
)
