"""Single source of truth for the contract bundle version.

Bump SemVer rules (see ARCHITECTURE.md in vmodel-spec-app):
- MAJOR: a consumer written against the previous version can break (field removed/renamed, meaning changed).
- MINOR: purely additive (new optional fields, new models). Required-field additions may ride a MINOR
  ONLY because consumers enforce contract_version equality on minor before reading (see compat.py) -
  a payload from the wrong minor fails loudly, never silently.
- PATCH: docs, defaults, validation tightening that accepts a superset of the old inputs.
"""
__version__ = "0.6.0"
CONTRACT_VERSION = __version__
