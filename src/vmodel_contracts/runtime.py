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
        rest = "\n".join(lines[index + 1:])
        feedback = ""
        for marker in ("\nFEEDBACK:", "\nfeedback:"):
            if marker in "\n" + rest:
                before, feedback = ("\n" + rest).split(marker, 1)
                rest = before.strip()
                break
        rationale = rest.removeprefix("RATIONALE:").removeprefix("rationale:").strip()
        return {"action": action, "feedback": feedback.strip(),
                "rationale": rationale or "No separate rationale supplied."}

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
                        "rationale": str(payload.get("rationale") or "No separate rationale supplied.").strip()}
    return None
