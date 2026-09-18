"""Shared runtime guards for long-running local V-model processes."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
import subprocess
import sys
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")


def keep_awake_command(command: list[str]) -> list[str]:
    """Wrap a child command so macOS cannot idle-sleep while it runs."""
    if sys.platform == "darwin" and shutil.which("caffeinate"):
        return ["caffeinate", "-dims", *command]
    return command


@contextmanager
def system_awake() -> Iterator[bool]:
    """Keep this Python process awake on macOS; no-op elsewhere.

    ``caffeinate -w`` follows this process id and exits with it. The explicit
    terminate in ``finally`` also makes direct calls and tests clean.
    """
    proc = None
    active = sys.platform == "darwin" and shutil.which("caffeinate") is not None
    if active:
        proc = subprocess.Popen(
            ["caffeinate", "-dims", "-w", str(os.getpid())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    try:
        yield active
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def run_with_system_awake(fn: Callable[..., T], *args, **kwargs) -> T:
    """Run one long-lived entry point under the shared macOS guard."""
    with system_awake():
        return fn(*args, **kwargs)


def artifacts_root(override: str | None = None, cwd: Path | None = None) -> Path:
    """Where run artifacts live by default: the ``artifacts`` folder SIBLING
    of the repo checkout you run from.

    Layout convention: the services are checked out side by side under one
    workspace root (``~/development/require/<repo>``). Running from inside a
    checkout writes to ``<root>/artifacts/``, keeping generated output out of
    the git trees. ``override`` (env/.env, e.g. VMODEL_ARTIFACTS_DIR) wins:
    absolute paths are used as-is, relative paths resolve against ``cwd``.
    ``cwd`` is injectable for tests.
    """
    base = cwd or Path.cwd()
    if override:
        p = Path(override).expanduser()
        return (p if p.is_absolute() else base / p).resolve()
    return (base.parent / "artifacts").resolve()


def session_artifacts_dir(session_id: str, component: str | None = None,
                          override: str | None = None, cwd: Path | None = None) -> Path:
    """Canonical run layout: <artifacts>/<session>[/<component>]."""
    root=artifacts_root(override,cwd)
    base=root/session_id
    return base/component if component else base


def console_timestamp(ts: float | None = None) -> str:
    """Local wall-clock time for every human-facing runtime progress line."""
    import time

    return time.strftime("%H:%M:%S", time.localtime(time.time() if ts is None else ts))


def timestamp_console_line(message: str, ts: float | None = None) -> str:
    """Prepend the canonical local HH:MM:SS marker to a console line."""
    return f"[{console_timestamp(ts)}] {message}"


_CONSOLE_COLORS = {"error": "31", "warning": "33", "success": "32"}


def color_console_line(message: str, level: str | None = None, stream=None) -> str:
    """Color a human console line only when its destination is an interactive TTY.

    Redirected output, tee/file logs, CI captures, and NO_COLOR remain plain.
    """
    if level not in _CONSOLE_COLORS or os.environ.get("NO_COLOR") is not None:
        return message
    destination = stream or sys.stderr
    try:
        enabled = destination.isatty()
    except (AttributeError, OSError):
        enabled = False
    if not enabled:
        return message
    return f"\x1b[{_CONSOLE_COLORS[level]}m{message}\x1b[0m"


def format_console_line(message: str, ts: float | None = None,
                        level: str | None = None, stream=None) -> str:
    """Canonical timestamp plus optional TTY-safe severity color."""
    return color_console_line(timestamp_console_line(message, ts), level, stream)


class PlainLogMirror:
    """Mirror a text stream to a plain UTF-8 log while preserving TTY behavior."""
    def __init__(self, terminal, sink):
        self.terminal, self.sink = terminal, sink

    def write(self, text):
        import re
        self.terminal.write(text)
        self.sink.write(re.sub(r"\x1b\[[0-9;]*m", "", text))
        self.sink.flush()
        return len(text)

    def flush(self):
        self.terminal.flush(); self.sink.flush()

    def isatty(self):
        return self.terminal.isatty()

    def __getattr__(self, name):
        return getattr(self.terminal, name)


def install_plain_log(path: Path, stream=None):
    """Return a TTY-preserving stream that also writes a clean timestamped log."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sink = path.open("a", encoding="utf-8", buffering=1)
    return PlainLogMirror(stream or sys.stderr, sink)


def empty_llm_response_detail(response, mask: Callable[[str], str] | None = None) -> dict:
    """Return a safe, JSON-serializable diagnostic envelope for empty completions.

    This deliberately excludes request messages. Provider response ids,
    metadata, usage, and additional fields are enough to diagnose an empty
    completion without copying founder prompts into routine telemetry.
    """
    import json

    clean = mask or (lambda value: value)
    payload = {"response_type": type(response).__name__}
    for name in ("id", "content", "response_metadata", "usage_metadata", "additional_kwargs"):
        value = getattr(response, name, None)
        if value not in (None, {}, []):
            payload[name] = value
    try:
        return json.loads(clean(json.dumps(payload, default=str)))
    except (TypeError, ValueError):
        return {"response_type": type(response).__name__,
                "raw": clean(repr(response))[:2000]}


def debug_http_enabled() -> bool:
    """Explicit opt-in for payload-bearing LLM HTTP diagnostics."""
    return os.environ.get("VMODEL_DEBUG_HTTP", "").strip().lower() in {"1", "true", "yes", "on"} or bool(
        os.environ.get("VMODEL_DEBUG_HTTP", "").strip() not in {"", "0", "false", "no", "off"}
    )


def debug_http_path(llm_log: str | None = None) -> Path:
    """Debug sink next to llm-calls.jsonl, or an explicit path from the env."""
    configured = os.environ.get("VMODEL_DEBUG_HTTP", "").strip()
    if configured and configured.lower() not in {"1", "true", "yes", "on"}:
        return Path(configured).expanduser()
    sink = llm_log or os.environ.get("VMODEL_LLM_LOG")
    if sink and sink != "stderr":
        return Path(sink).expanduser().parent / "debug-http.jsonl"
    return Path("debug-http.jsonl")


def _debug_json(value, mask: Callable[[str], str]):
    """Round-trip arbitrary SDK objects through JSON while masking secrets."""
    import json
    try:
        return json.loads(mask(json.dumps(value, default=str)))
    except (TypeError, ValueError):
        return mask(repr(value))


def append_debug_http(record: dict, *, llm_log: str | None = None,
                      mask: Callable[[str], str] | None = None) -> Path | None:
    """Append one payload-bearing HTTP diagnostic record when explicitly enabled."""
    if not debug_http_enabled():
        return None
    import json
    import threading
    from datetime import datetime, timezone

    clean = mask or (lambda value: value)
    path = debug_http_path(llm_log)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = _debug_json({"ts": datetime.now(timezone.utc).isoformat(), **record}, clean)
    # One append call is atomic enough for the small local process records and
    # avoids a module-global lock that would not coordinate separate processes.
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    return path


def debug_http_client(*, llm_log: str | None = None,
                      mask: Callable[[str], str] | None = None):
    """Return an httpx client that records the exact request/response exchange.

    Request headers are intentionally omitted: they contain bearer credentials.
    The full JSON request body is retained because this mode is explicit and is
    used to replay malformed calls. Response headers and the complete raw JSON
    body are retained, including unknown provider fields and error objects.
    """
    if not debug_http_enabled():
        return None
    import json
    import time
    import httpx

    clean = mask or (lambda value: value)

    def on_request(request):
        try:
            raw = request.content.decode("utf-8", errors="replace")
            body = json.loads(raw)
        except Exception:
            body = clean(getattr(request, "content", b"").decode("utf-8", errors="replace"))
        request.extensions["vmodel_debug_started"] = time.time()
        request.extensions["vmodel_debug_body"] = body

    def on_response(response):
        response.read()
        request = response.request
        raw = response.content.decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        append_debug_http({
            "event": "http_exchange",
            "method": request.method,
            "url": str(request.url),
            "elapsed_s": round(time.time() - request.extensions.get("vmodel_debug_started", time.time()), 3),
            "request": request.extensions.get("vmodel_debug_body"),
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body,
                "raw_body_chars": len(raw),
            },
        }, llm_log=llm_log, mask=clean)

    return httpx.Client(event_hooks={"request": [on_request], "response": [on_response]})


class AdaptiveCallWatchdog:
    """Process-local per-stage wall-clock baseline for LLM calls.

    The first call gets the full floor. Later calls use the larger of the
    floor and K times that stage's running median, so one unusually fast early
    call can never create an aggressive deadline.
    """
    def __init__(self, multiplier: float = 8.0, floor_s: float = 240.0):
        self.multiplier, self.floor_s = multiplier, floor_s
        self._completed: dict[str, list[float]] = {}
        import threading
        self._lock = threading.Lock()

    def deadline(self, stage: str) -> tuple[float, float | None]:
        import statistics
        with self._lock:
            values = list(self._completed.get(stage, ()))
        median = statistics.median(values) if values else None
        return max(self.floor_s, self.multiplier * median) if median is not None else self.floor_s, median

    def complete(self, stage: str, duration_s: float) -> None:
        if duration_s < 0:
            return
        with self._lock:
            self._completed.setdefault(stage, []).append(float(duration_s))

    def reset(self) -> None:
        with self._lock:
            self._completed.clear()


class AdaptiveWatchdogTimeout(TimeoutError):
    def __init__(self, stage: str, elapsed_s: float, deadline_s: float, median_s: float | None):
        self.stage, self.elapsed_s, self.deadline_s, self.median_s = stage, elapsed_s, deadline_s, median_s
        super().__init__(f"{stage} exceeded adaptive watchdog deadline {deadline_s:.0f}s")

    @property
    def ratio(self) -> float | None:
        return self.elapsed_s / self.median_s if self.median_s else None


def parse_expert_verdict(text: str, allowed: tuple[str, ...]) -> dict | None:
    """Deterministically read a line-protocol or JSON expert verdict."""
    import json
    allowed_set = {value.lower() for value in allowed}
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    index = next((i for i, line in enumerate(lines)
                  if line.rstrip(" :.").lower() in allowed_set), None)
    if index is not None:
        action = lines[index].rstrip(" :.").lower()
        body_lines = lines[index + 1:]
        sections = {"rationale": [], "feedback": []}
        current = "rationale"
        for line in body_lines:
            upper = line.upper()
            if upper.startswith("RATIONALE:"):
                current = "rationale"
                sections[current].append(line.split(":", 1)[1].strip())
            elif upper.startswith("FEEDBACK:"):
                current = "feedback"
                sections[current].append(line.split(":", 1)[1].strip())
            else:
                sections[current].append(line)
        rationale = "\n".join(part for part in sections["rationale"] if part).strip()
        feedback = "\n".join(part for part in sections["feedback"] if part).strip()
        return {"action": action, "feedback": feedback,
                "rationale": rationale or "No separate rationale supplied.",
                "extracted_from": "line_protocol"}

    # Provider may ignore the plain-text protocol and emit a fenced or inline
    # object. Decode the first balanced object and trust only known actions.
    start = text.find("{")
    if start < 0:
        return None
    depth = 0; in_string = False; escaped = False
    for end in range(start, len(text)):
        char = text[end]
        if in_string:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': in_string = False
        elif char == '"': in_string = True
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try: payload = json.loads(text[start:end + 1])
                except (json.JSONDecodeError, TypeError): return None
                action = str(payload.get("action", "")).strip().lower() if isinstance(payload, dict) else ""
                if action not in allowed_set: return None
                return {"action": action,
                        "feedback": str(payload.get("feedback") or "").strip(),
                        "rationale": str(payload.get("rationale") or "No separate rationale supplied.").strip(),
                        "extracted_from": "json_object"}
    return None


def format_expert_review_rounds(records: list[dict], width: int = 96) -> str:
    """Readable, deduplicated per-round expert objections."""
    import difflib
    import re
    import textwrap

    def normalized(value) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()

    def objection_text(objection: dict) -> str:
        return " ".join(str(objection.get(key) or "") for key in
                        ("artifact", "rule", "location", "resolution"))

    lines = ["Reviewer objections:"]
    prior_signatures = []
    for index, record in enumerate(records, 1):
        objections = record.get("objections") or []
        # Collapse near-identical items inside a round. Preserve first wording.
        unique = []
        for objection in objections:
            candidate = normalized(objection_text(objection))
            if any(difflib.SequenceMatcher(None, candidate, normalized(objection_text(old))).ratio() >= .88
                   for old in unique):
                continue
            unique.append(objection)
        signature = tuple(sorted(normalized(objection_text(item)) for item in unique))
        identical_to = next((n for n, prior in enumerate(prior_signatures, 1)
                             if signature and signature == prior), None)
        prior_signatures.append(signature)
        if identical_to is not None:
            lines.extend(("", f"Round {index}: objections identical to round {identical_to}"))
            continue

        lines.extend(("", f"Round {index}", ""))
        saved_at = str(record.get("artifact_saved_at") or "").strip()
        revision = record.get("artifact_revision")
        fingerprint = str(record.get("artifact_sha256") or "").strip()
        if saved_at:
            revision_text = f"revision {revision}, " if revision is not None else ""
            sha_text = f", SHA {fingerprint}" if fingerprint else ""
            lines.extend(("Artifact reviewed:", f"  {revision_text}saved at {saved_at}{sha_text}", ""))
        rationale = str(record.get("rationale") or "No separate rationale supplied.").strip()
        lines.append("Rationale:")
        lines.extend(textwrap.wrap(rationale, width=width, initial_indent="  ", subsequent_indent="  ") or ["  (none)"])
        upstream = record.get("upstream_advisories") or []
        if upstream:
            lines.append("Upstream advisories:")
            for advisory_index, advisory in enumerate(upstream, 1):
                lines.append(f"  {advisory_index}. This concerns the {advisory.get('artifact', 'upstream artifact')}:")
                for field in ("rule", "location", "resolution"):
                    label = field.title()
                    value = str(advisory.get(field) or "(none)").strip()
                    prefix = f"     {label}: "
                    lines.extend(textwrap.wrap(value, width=width, initial_indent=prefix,
                                               subsequent_indent=" " * len(prefix)) or [prefix + "(none)"])
        if unique:
            lines.append("Feedback:")
            for objection_index, objection in enumerate(unique, 1):
                lines.append(f"  {objection_index}.")
                for field in ("artifact", "rule", "location", "resolution"):
                    label = field.title()
                    value = str(objection.get(field) or "(none)").strip()
                    prefix = f"     {label}: "
                    lines.extend(textwrap.wrap(value, width=width, initial_indent=prefix,
                                               subsequent_indent=" " * len(prefix)) or [prefix + "(none)"])
        else:
            feedback = str(record.get("feedback") or "(none)").strip()
            enumerated = re.split(r"(?:^|\s+)\d+[.)](?=\s|$)", feedback)
            chunks = [re.sub(r"(?:^|\s+)\d+[.)]\s*$", "", chunk).strip() for chunk in enumerated]
            chunks = [chunk for chunk in chunks if chunk and not re.fullmatch(r"\d+[.)]?", chunk)]
            parts = (chunks if len(chunks) > 1 else
                     [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z])", feedback) if p.strip()])
            lines.append("Feedback:")
            for part_index, part in enumerate(parts, 1):
                prefix = f"  {part_index}. " if len(parts) > 1 else "  "
                lines.extend(textwrap.wrap(part, width=width, initial_indent=prefix,
                                           subsequent_indent=" " * len(prefix)) or [prefix + "(none)"])
    return "\n".join(lines)


def validate_expert_objections(feedback: str, reviewed_artifacts: tuple[str, ...], reviewed_text: str = "") -> tuple[list[dict], list[str]]:
    """Parse and deterministically validate concrete expert objections.

    Protocol, one objection per line:
    OBJECTION: artifact=<name> | rule=<criterion> | location=<id/section/quote> | resolution=<change>
    """
    import re
    artifact_set = {str(value).strip().lower() for value in reviewed_artifacts if str(value).strip()}
    lines = [line.strip() for line in str(feedback or "").splitlines() if line.strip()]
    objections, errors = [], []
    candidates = [line for line in lines if line.lower().startswith("objection:")]
    if not candidates:
        return [], ["objection 1 has no structured OBJECTION line"]
    for index, line in enumerate(candidates, 1):
        fields = {}
        for piece in line.split(":", 1)[1].split("|"):
            if "=" in piece:
                key, value = piece.split("=", 1)
                fields[key.strip().lower()] = value.strip()
        missing = [key for key in ("artifact", "rule", "location", "resolution") if not fields.get(key)]
        if missing:
            errors.append(f"objection {index} missing {', '.join(missing)}")
            continue
        artifact = fields["artifact"].lower()
        if artifact_set and artifact not in artifact_set:
            errors.append(f"objection {index} names artifact {fields['artifact']!r}, not reviewed artifact(s) {sorted(artifact_set)}")
            continue
        location = fields["location"]
        # A location must point to an identifier, named section/field, or a
        # quoted source fragment. Generic words such as "artifact" do not pass.
        concrete_location = (bool(re.search(r"\b(?:SN|N|R|AC|ADR|SPEC|TEST)-[A-Za-z0-9._-]+\b", location, re.I))
                             or bool(re.search(r"\b(?:section|field|entry|decision|requirement|criterion)\s+[A-Za-z0-9_.-]+", location, re.I))
                             or bool(re.search(r'["“][^"”]{3,}["”]', location)))
        if not concrete_location:
            errors.append(f"objection {index} location {location!r} has no section, id, field, or quoted fragment")
            continue
        if len(fields["rule"].split()) < 2:
            errors.append(f"objection {index} rule {fields['rule']!r} is not a named criterion")
            continue
        if len(fields["resolution"].split()) < 3:
            errors.append(f"objection {index} resolution {fields['resolution']!r} is not a concrete change")
            continue
        quotes = re.findall(r'["“]([^"”]+)["”]', fields["location"])
        containment_claim = bool(re.search(r"\b(?:contain(?:s|ed|ing)?|include(?:s|d|ing)?|invent(?:s|ed|ing)?|mention(?:s|ed|ing)?)\b",
                                           fields["rule"] + " " + fields["resolution"], re.I))
        if containment_claim and not quotes:
            errors.append(f"objection {index} containment/invention claim requires a quoted artifact example")
            continue
        missing_quotes = [quote for quote in quotes if reviewed_text and quote not in reviewed_text]
        if missing_quotes:
            errors.append(f"objection {index} quotes text absent from reviewed artifact: {missing_quotes!r}")
            continue
        objections.append({key: fields[key] for key in ("artifact", "rule", "location", "resolution")})
    return objections, errors


def classify_expert_objections(feedback: str, reviewed_artifact: str,
                               known_artifacts: tuple[str, ...], reviewed_text: str = "") -> tuple[list[dict], list[dict], list[str]]:
    """Validate feedback, separating fix-here blockers from upstream advisories."""
    import re
    known = tuple(dict.fromkeys((reviewed_artifact, *known_artifacts)))
    reviewed = reviewed_artifact.strip().lower()
    upstream_names = {name.strip().lower() for name in known_artifacts}
    own, upstream, errors = [], [], []
    remaining = []
    for raw_line in str(feedback or "").splitlines():
        line = re.sub(r"^\s*\d+[.)]\s*", "", raw_line.strip())
        if not line:
            continue
        lower = line.lower()
        # Attribute blame to the artifact described as owning the defect. An
        # own-artifact word in a destination phrase ("belongs to architecture")
        # must not override the blamed upstream subject ("The SRS contains").
        named_upstream = next((name for name in upstream_names
                               if re.search(rf"(?:^|objection:\s*)(?:the\s+)?{re.escape(name)}\b", lower)
                               or re.search(rf"artifact\s*=\s*{re.escape(name)}\b", lower)), None)
        structured = line.lower().startswith("objection:") and "artifact=" in lower
        if named_upstream and not structured:
            quotes = re.findall(r'["“]([^"”]+)["”]', line)
            evidence = ", ".join(f'"{value}"' for value in quotes)
            upstream.append({"artifact": named_upstream,
                "rule": "upstream concern reported by expert reviewer",
                "location": f'quoted fragment(s) {evidence}' if evidence else f"reviewer statement: {line}",
                "resolution": f"Inspect and correct the named {named_upstream} concern before rewinding that stage",
                "detail": line})
        else:
            remaining.append(line)
    if remaining:
        items, strict_errors = validate_expert_objections("\n".join(remaining), known, reviewed_text)
        errors.extend(strict_errors)
        for item in items:
            (own if item["artifact"].strip().lower() == reviewed else upstream).append(item)
    return own, upstream, errors
