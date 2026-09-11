"""Shared runtime guards for long-running local V-model processes."""
from __future__ import annotations

import os
import shutil
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
