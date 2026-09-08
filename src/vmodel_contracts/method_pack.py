"""Access to the curated method pack (tier-a knowledge augmentation).

The pack is static prompt context - systems-engineering interview and
requirements knowledge restated from the IEEE SWEBOK Guide v4.0a (see the
pack's header for attribution). It is intentionally tiny: prompt context on a
local 14B is the scarce resource, so METHOD_PACK_TOKEN_CAP is enforced by
tests in this repo.

Sections are numbered ("1".."5") so each consumer takes only the slice its
stage needs instead of paying the full context cost every call.
"""
from importlib.resources import files

# ~4 chars/token; the pack must stay well under the 2,000-token design cap.
METHOD_PACK_TOKEN_CAP = 2000


def _parts() -> tuple[str, dict[str, str]]:
    text = (files("vmodel_contracts") / "method_pack.md").read_text(encoding="utf-8")
    preamble, *chunks = text.split("\n## ")
    sections = {}
    for chunk in chunks:
        header, _, body = chunk.partition("\n")
        number = header.split(".", 1)[0].strip()
        sections[number] = "## " + chunk.rstrip()
    return preamble.rstrip(), sections


def load_method_pack(sections: list[str] | None = None) -> str:
    """The method pack markdown, ready to append to a prompt.

    sections=None returns the full pack; otherwise the preamble plus only the
    numbered sections requested (e.g. ["1", "2"]).
    """
    preamble, all_sections = _parts()
    if sections is None:
        return "\n\n".join([preamble, *all_sections.values()]) + "\n"
    missing = [s for s in sections if s not in all_sections]
    if missing:
        raise ValueError(f"unknown method-pack section(s): {missing}; have {sorted(all_sections)}")
    return "\n\n".join([preamble, *[all_sections[s] for s in sections]]) + "\n"
