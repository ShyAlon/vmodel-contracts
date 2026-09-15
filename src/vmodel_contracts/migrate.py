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

from .architecture import ArchitectureOverview
from .conops import ConOpsDocument
from .compat import ContractVersionMismatch, check_compatible
from .interview import IntentModel
from .baseline import SystemBaseline
from .version import CONTRACT_VERSION

# ADDED 0.8.0 (ADR-0021): ArchitectureDecision gained required-present fields
# (driver, options_considered). Pre-0.8.0 decision dicts get the honest legacy
# form: driver null (unverifiable retroactively), options_considered empty,
# deprecated `rejected` carried as-is.
def _synthesize_008(node, path: str = "") -> list[str]:
    """Recursively add the 0.8.0 required-present fields to decision dicts.
    Returns the list of changed paths."""
    changed = []
    if isinstance(node, dict):
        if "decision_id" in node and "rationale" in node:
            here = path or node.get("decision_id", "?")
            if "driver" not in node:
                node["driver"] = None
                changed.append(f"{here}.driver: synthesized null (legacy artifact - no retroactive driver)")
            if "options_considered" not in node:
                node["options_considered"] = []
                changed.append(f"{here}.options_considered: synthesized [] (legacy artifact)")
        for k, v in node.items():
            here = f"{path}.{k}" if path else k
            changed += _synthesize_008(v, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            changed += _synthesize_008(v, f"{path}[{i}]")
    return changed


class UnhealableLegacyArchitecture(ValueError):
    """A pre-0.13.0 architecture payload whose parallel maps cannot be healed
    into typed stack entries without guessing."""


def _synthesize_013(payload: dict) -> list[str]:
    """0.13.0: heal a pre-0.13.0 architecture payload's parallel maps
    (`stack` + `stack_baseline_refs`) into typed `stack_entries`.

    Honest rules (the 2026-09-11 phi4 failure shaped them):
    - Both maps present, both dicts, EQUAL key sets: unambiguous legacy -
      co-locate each value with its refs; migration_adr_id stays null (the
      legacy departure linkage was by ADR title/decision text and is NOT
      retro-mapped to pipeline ids; the stage checks accept the legacy form).
    - Key sets disagree, or either value is not a string->string / string->
      list map: the payload is ambiguous or malformed. Refuse loudly - it
      needs an architecture re-run, not a guessed heal.
    Returns the list of changed paths."""
    if "stack_entries" in payload or "stack" not in payload:
        return []
    stack = payload.get("stack")
    refs_present = "stack_baseline_refs" in payload
    refs = payload.get("stack_baseline_refs", {})
    # A MISSING refs map is not ambiguous: pre-grounding artifacts (pre-0.12.0)
    # simply did not record refs - heal with empty refs ("not recorded"), which
    # the CONTRACT accepts even though the stage demands grounding for new work.
    # A PRESENT refs map whose keys disagree with the stack map IS ambiguous:
    # no honest co-location exists (the 2026-09-11 phi4 failure shape).
    if not isinstance(stack, dict) or not isinstance(refs, dict) or (refs_present and set(stack) != set(refs)):
        raise UnhealableLegacyArchitecture(
            "this pre-0.13.0 architecture payload cannot be healed: 'stack' and "
            "'stack_baseline_refs' must both be maps with EXACTLY the same keys "
            f"(stack keys: {sorted(stack) if isinstance(stack, dict) else type(stack).__name__}; "
            f"refs keys: {sorted(refs) if isinstance(refs, dict) else type(refs).__name__}). "
            "The two maps disagree, so no honest co-location exists - this payload "
            "needs an architecture re-run against contracts 0.13.0, not a migration."
        )
    entries = []
    for key, value in stack.items():
        entry_refs = refs.get(key, [])
        if not isinstance(value, str) or not isinstance(entry_refs, list) or not all(isinstance(r, str) for r in entry_refs):
            raise UnhealableLegacyArchitecture(
                f"stack entry {key!r} is malformed (value {type(value).__name__}, "
                f"refs {type(entry_refs).__name__}) - refusing to guess; re-run the architecture stage."
            )
        entries.append({"contract_version": CONTRACT_VERSION, "key": key, "value": value,
                        "baseline_refs": entry_refs, "migration_adr_id": None})
    payload["stack_entries"] = entries
    del payload["stack"]
    payload.pop("stack_baseline_refs", None)
    note = ("stack/stack_baseline_refs" if refs_present else "stack (no refs recorded pre-0.12.0)")
    return [f"{note}: healed into stack_entries ({len(entries)} entries, "
            "migration_adr_id null - legacy title-linked departures)"]


def _detect_schema(payload: dict):
    """Which contract model validates this payload. Shape sniff, ordered."""
    if "stakeholder_context" in payload and "concept_options" in payload and "decision" in payload:
        return ConOpsDocument
    if "stakeholder_needs" in payload:
        return IntentModel
    if "baseline_id" in payload and "mode" in payload and "repositories" in payload:
        return SystemBaseline
    if ("components" in payload or "decisions" in payload
            or "stack" in payload or "stack_entries" in payload):
        return ArchitectureOverview
    return IntentModel  # default: IntentModel errors are the most actionable


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
    # synthesize additive required fields from MINOR bumps BEFORE validating:
    # that synthesis is what makes a re-stamp (not a re-run) the honest path.
    try:
        synthesized = _synthesize_008(payload) + _synthesize_013(payload)
    except UnhealableLegacyArchitecture as e:
        print(f"Error: {path}: {e}", file=sys.stderr)
        return 1
    # validate against the CURRENT schema first: the stamp only moves when the
    # payload is otherwise a legal current-version artifact.
    schema = _detect_schema(payload)
    try:
        validated = schema.model_validate(payload)
        if schema is ConOpsDocument:
            payload = validated.model_dump(mode="json")
            synthesized.append("concept ids: resolved from canonical alias registry")
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
    print(f"Migrated {path}: {have} -> {CONTRACT_VERSION} ({schema.__name__}; {len(changed)} stamp(s) re-stamped; schema validated first).")
    for c in synthesized + changed:
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

