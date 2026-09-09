"""First-class payload migration: python -m vmodel_contracts.migrate <payload.json>

The version gate rejects wrong-minor payloads LOUDLY by design - but an
additive MINOR bump (new models, new optional fields) leaves old payloads
semantically valid under the new schema, and hand-editing the stamp is not a
workflow. This command makes the honest path first-class:

1. Validate the payload against the CURRENT IntentModel schema.
2. Valid: re-stamp every contract_version field (top-level AND nested) to the
   current version, in place, and report exactly what changed.
3. Invalid: print the field-by-field errors and refuse (exit 1) - a payload
   that fails the current schema needs a re-run, not a re-stamp.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .compat import ContractVersionMismatch, check_compatible
from .interview import IntentModel
from .version import CONTRACT_VERSION


def _restamp(node, have: str, path: str = "") -> list[str]:
    """Recursively set every contract_version to the current one. Returns the
    list of changed paths (old value -> new)."""
    changed = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{path}.{k}" if path else k
            if k == "contract_version" and isinstance(v, str) and v != CONTRACT_VERSION:
                node[k] = CONTRACT_VERSION
                changed.append(f"{here}: {v} -> {CONTRACT_VERSION}")
            else:
                changed += _restamp(v, have, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            changed += _restamp(v, have, f"{path}[{i}]")
    return changed


def migrate_file(path: Path) -> int:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: cannot read {path} ({e}).", file=sys.stderr)
        return 1
    have = payload.get("contract_version", "unknown")
    try:
        check_compatible(payload)
        print(f"{path}: already at {have} - nothing to do.")
        return 0
    except ContractVersionMismatch:
        pass
    # validate against the CURRENT schema first: the stamp only moves when the
    # payload is otherwise a legal current-version intent model.
    try:
        IntentModel.model_validate(payload)
    except ValidationError as e:
        print(f"Error: {path} is NOT compatible with vmodel-contracts {CONTRACT_VERSION} - refusing to re-stamp.",
              file=sys.stderr)
        for err in e.errors():
            loc = ".".join(str(p) for p in err["loc"])
            print(f"  {loc}: {err['msg']} (got {str(err.get('input'))[:60]})", file=sys.stderr)
        print("Next: this payload needs a re-run against the current contracts, not a migration.",
              file=sys.stderr)
        return 1
    changed = _restamp(payload, have)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Migrated {path}: {have} -> {CONTRACT_VERSION} ({len(changed)} stamp(s) re-stamped; schema validated first).")
    for c in changed:
        print(f"  {c}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m vmodel_contracts.migrate",
                                 description="Re-stamp a compatible payload to the current contracts version (validates first, refuses on schema drift).")
    ap.add_argument("payload", type=Path)
    args = ap.parse_args()
    sys.exit(migrate_file(args.payload))


if __name__ == "__main__":
    main()
