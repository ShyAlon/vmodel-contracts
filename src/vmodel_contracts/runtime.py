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
