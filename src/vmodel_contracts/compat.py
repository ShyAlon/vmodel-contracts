"""Payload/version compatibility. The rule: wrong-minor payloads fail LOUDLY,
never silently (ADR-0002/ADR-0012). Patch drift is compatible by definition."""
from __future__ import annotations

from .version import CONTRACT_VERSION


class ContractVersionMismatch(ValueError):
    def __init__(self, have: str | None, want: str):
        self.have, self.want = have, want
        super().__init__(
            f"payload was produced against vmodel-contracts {have or 'unknown'}, "
            f"this code reads {'.'.join(want.split('.')[:2])}.x"
        )


def _major_minor(v: str) -> tuple[int, int]:
    parts = v.split(".")
    return int(parts[0]), int(parts[1])


def check_compatible(payload: dict, expecting: str = CONTRACT_VERSION) -> None:
    """Raise ContractVersionMismatch when the payload's contract_version is a
    different MAJOR.MINOR than this build. Payloads missing the field are
    pre-versioning artifacts: also rejected, named as such."""
    have = payload.get("contract_version")
    if not isinstance(have, str):
        raise ContractVersionMismatch(None, expecting)
    # 0.29 adds optional source snapshots. Read old 0.28 bytes without
    # inventing quotes or approvals. Older readers must reject the new shape.
    if _major_minor(expecting) == (0, 29) and _major_minor(have) == (0, 28):
        return
    if _major_minor(have) != _major_minor(expecting):
        raise ContractVersionMismatch(have, expecting)
