"""Mechanical normalization for common model-authored shape drift."""
from __future__ import annotations

from typing import Any, get_args, get_origin

_TEXT_KEYS = ("statement", "text", "description", "summary", "name", "value")


def text_value(value: Any) -> str | None:
    """Extract one text scalar from a wrapper object without inventing prose."""
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    for key in _TEXT_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def normalize_list_string_fields(value: Any, model_cls) -> Any:
    """Normalize model fields annotated list[str] at an assembly boundary.

    Models frequently emit richer `{statement, source_turns}` objects where a
    contract asks for strings. Preserve only the explicit text-like value;
    leave unrecognized objects untouched so Pydantic still fails loudly.
    """
    if not isinstance(value, dict):
        return value
    out = dict(value)
    for key, field in model_cls.model_fields.items():
        if key not in out:
            continue
        annotation = field.annotation
        if get_origin(annotation) is not list or get_args(annotation) != (str,):
            continue
        current = out[key]
        if isinstance(current, str):
            out[key] = [current]
        elif isinstance(current, dict):
            extracted = text_value(current)
            out[key] = [extracted] if extracted is not None else current
        elif isinstance(current, list):
            normalized = []
            for item in current:
                extracted = text_value(item)
                normalized.append(extracted if extracted is not None else item)
            out[key] = normalized
        elif current is None:
            out[key] = []
    return out
