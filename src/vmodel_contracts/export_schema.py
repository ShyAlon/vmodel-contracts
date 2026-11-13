"""Export every contract's JSON Schema into schemas/ for non-Python consumers
and for contract-diffing in CI (a schema diff IS the compatibility check)."""
from __future__ import annotations

import json
from pathlib import Path

from . import intake, interview, conops, requirements, spec, verification, delivery, telemetry, baseline, facets, semantic_review, founder_register, handoff, interactive, citations
from .base import ContractModel
from .semantic_review import ReviewModel
from .interactive import InteractiveModel

_MODULES = [intake, interview, conops, requirements, spec, verification, delivery, telemetry, baseline, facets, semantic_review, founder_register, handoff, interactive, citations]


def all_models() -> dict[str, type[ContractModel]]:
    found: dict[str, type[ContractModel]] = {}
    for mod in _MODULES:
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, (ContractModel,ReviewModel,InteractiveModel)) and obj not in (ContractModel,ReviewModel,InteractiveModel):
                found[name] = obj
    return found


def main() -> None:
    out = Path("schemas")
    try:
        out.mkdir(exist_ok=True)
        for name, model in sorted(all_models().items()):
            (out / f"{name}.schema.json").write_text(json.dumps(model.model_json_schema(), indent=2))
    except OSError as e:
        import sys

        print(
            f"Error: could not write schemas into {out}/ ({e.strerror or e}).\n"
            "Likely cause: the directory is not writable from here.\n"
            "Next: run from a writable checkout directory, or pass a writable CWD.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"exported {len(all_models())} schemas to {out}/")


if __name__ == "__main__":
    main()
