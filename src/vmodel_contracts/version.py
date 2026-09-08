"""Single source of truth for the contract bundle version.

Bump SemVer rules (see ARCHITECTURE.md in vmodel-spec-app):
- MAJOR: a consumer written against the previous version can break (field removed/renamed, meaning changed).
- MINOR: purely additive (new optional fields, new models).
- PATCH: docs, defaults, validation tightening that accepts a superset of the old inputs.
"""
__version__ = "0.1.0"
CONTRACT_VERSION = __version__
