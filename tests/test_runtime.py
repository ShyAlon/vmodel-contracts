from unittest.mock import Mock, patch

from pathlib import Path

from vmodel_contracts.runtime import artifacts_root, keep_awake_command, run_with_system_awake, system_awake


def test_keep_awake_command_wraps_only_on_macos():
    command = ["python", "-m", "worker"]
    with patch("vmodel_contracts.runtime.sys.platform", "darwin"), patch(
        "vmodel_contracts.runtime.shutil.which", return_value="/usr/bin/caffeinate"
    ):
        assert keep_awake_command(command) == ["caffeinate", "-dims", *command]
    with patch("vmodel_contracts.runtime.sys.platform", "linux"):
        assert keep_awake_command(command) is command


def test_system_awake_follows_current_process_and_cleans_up():
    proc = Mock(); proc.poll.return_value = None
    with patch("vmodel_contracts.runtime.sys.platform", "darwin"), patch(
        "vmodel_contracts.runtime.shutil.which", return_value="/usr/bin/caffeinate"
    ), patch("vmodel_contracts.runtime.os.getpid", return_value=4242), patch(
        "vmodel_contracts.runtime.subprocess.Popen", return_value=proc
    ) as popen:
        with system_awake() as active:
            assert active
        popen.assert_called_once()
        assert popen.call_args.args[0] == ["caffeinate", "-dims", "-w", "4242"]
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=2)


def test_run_with_system_awake_is_transparent_off_macos():
    with patch("vmodel_contracts.runtime.sys.platform", "linux"):
        assert run_with_system_awake(lambda x: x + 1, 4) == 5


def test_artifacts_root_defaults_to_sibling_folder(tmp_path):
    repo = tmp_path / "require" / "spec-generator"
    repo.mkdir(parents=True)
    assert artifacts_root(cwd=repo) == (tmp_path / "require" / "artifacts").resolve()


def test_artifacts_root_override_wins_absolute_and_relative(tmp_path):
    repo = tmp_path / "require" / "spec-generator"
    repo.mkdir(parents=True)
    assert artifacts_root("/data/runs", cwd=repo) == Path("/data/runs")
    assert artifacts_root("out", cwd=repo) == (repo / "out").resolve()
    assert artifacts_root("", cwd=repo) == (tmp_path / "require" / "artifacts").resolve()
    assert artifacts_root(None, cwd=repo) == (tmp_path / "require" / "artifacts").resolve()

def test_session_artifacts_layout(tmp_path):
    from vmodel_contracts.runtime import session_artifacts_dir
    repo=tmp_path/'require'/'interview-engine';repo.mkdir(parents=True)
    assert session_artifacts_dir('s','interview',cwd=repo)==tmp_path/'require'/'artifacts'/'s'/'interview'


def test_console_timestamp_format_is_shared_and_local():
    from vmodel_contracts.runtime import console_timestamp, timestamp_console_line

    assert console_timestamp(0).count(":") == 2
    assert timestamp_console_line("  -> Working...", 0).endswith("  -> Working...")
    assert timestamp_console_line("ok", 0).startswith("[")


def test_console_colors_are_tty_aware_and_honor_no_color(monkeypatch):
    from vmodel_contracts.runtime import format_console_line

    tty = Mock(); tty.isatty.return_value = True
    plain = Mock(); plain.isatty.return_value = False
    assert "\x1b[32m" in format_console_line("ok", 0, "success", tty)
    assert "\x1b[31m" in format_console_line("error", 0, "error", tty)
    assert "\x1b[33m" in format_console_line("warning", 0, "warning", tty)
    assert "\x1b[" not in format_console_line("ok", 0, "success", plain)
    monkeypatch.setenv("NO_COLOR", "1")
    assert "\x1b[" not in format_console_line("ok", 0, "success", tty)


def test_plain_log_mirror_preserves_tty_and_strips_ansi(tmp_path):
    import io
    from vmodel_contracts.runtime import install_plain_log

    class TTY(io.StringIO):
        def isatty(self): return True
    terminal = TTY(); path = tmp_path / "run.log"
    mirror = install_plain_log(path, terminal)
    mirror.write("\x1b[32m[12:00:00] ok\x1b[0m\n")
    assert mirror.isatty() is True
    assert "\x1b[32m" in terminal.getvalue()
    assert path.read_text() == "[12:00:00] ok\n"


def test_adaptive_watchdog_cold_start_and_quick_baseline_floor():
    from vmodel_contracts.runtime import AdaptiveCallWatchdog
    watch = AdaptiveCallWatchdog(multiplier=8, floor_s=240)
    assert watch.deadline("architecture") == (240, None)
    watch.complete("architecture", 2)
    assert watch.deadline("architecture") == (240, 2)
    watch.complete("architecture", 30)
    # Median 16, 8x=128: the absolute floor still prevents a false positive.
    assert watch.deadline("architecture") == (240, 16)
    watch.complete("architecture", 30)
    assert watch.deadline("architecture") == (240, 30)
    watch.complete("architecture", 40)
    # Median 30 now raises the deadline above the floor.
    assert watch.deadline("architecture") == (240, 30)


def test_parse_expert_verdict_accepts_fenced_json_and_rejects_garbage():
    from vmodel_contracts.runtime import parse_expert_verdict
    blob='''```json
{"action":"REGENERATE","stakeholderNeeds":[{"id":"SN-1"}],"feedback":"Fix trace links"}
```'''
    assert parse_expert_verdict(blob, ("approve", "regenerate")) == {
        "action":"regenerate", "feedback":"Fix trace links",
        "rationale":"No separate rationale supplied."}
    assert parse_expert_verdict("not a verdict", ("approve", "regenerate")) is None
