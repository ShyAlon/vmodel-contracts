"""Export every contract's JSON Schema into schemas/ for non-Python consumers
and for contract-diffing in CI (a schema diff IS the compatibility check)."""
from __future__ import annotations

import json
from pathlib import Path

from . import __all__ as _public
from . import intake, interview, requirements, spec, verification, delivery, telemetry
from .base import ContractModel

_MODULES = [intake, interview, requirements, spec, verification, delivery, telemetry]


def all_models() -> dict[str, type[ContractModel]]:
    found: dict[str, type[ContractModel]] = {}
    for mod in _MODULES:
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, ContractModel) and obj is not ContractModel:
                found[name] = obj
    return found


def main() -> None:
    out = Path("schemas")
    out.mkdir(exist_ok=True)
    for name, model in sorted(all_models().items()):
        (out / f"{name}.schema.json").write_text(json.dumps(model.model_json_schema(), indent=2))
    print(f"exported {len(all_models())} schemas to {out}/")


if __name__ == "__main__":
    main()
