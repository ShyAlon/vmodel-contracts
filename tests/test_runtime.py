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
        "rationale":"No separate rationale supplied.", "extracted_from":"json_object"}
    assert parse_expert_verdict("not a verdict", ("approve", "regenerate")) is None


def test_format_expert_rounds_is_sectioned_wrapped_and_numbered():
    from vmodel_contracts.runtime import format_expert_review_rounds
    text=format_expert_review_rounds([{"rationale":"Because the artifact is incomplete.",
      "feedback":"Fix trace links. Remove solution language. Add measurable criteria."}],width=48)
    assert "Reviewer objections:\n\nRound 1\n\nRationale:\n  Because" in text
    assert "Feedback:\n  1. Fix trace links.\n  2. Remove solution" in text
    assert "\n  3. Add measurable criteria." in text


def test_format_expert_rounds_shows_full_artifact_date_time():
    from vmodel_contracts.runtime import format_expert_review_rounds
    text = format_expert_review_rounds([{
        "artifact_revision": 2,
        "artifact_saved_at": "2026-09-18T06:45:58.600595+00:00",
        "artifact_sha256": "7039e3d991a6",
        "rationale": "Current artifact is coherent.",
        "feedback": "Fix trace links.",
    }])
    assert "Artifact reviewed:" in text
    assert "revision 2, saved at 2026-09-18T06:45:58.600595+00:00" in text
    assert "SHA 7039e3d991a6" in text


def test_specific_expert_objection_validation_and_rendering():
    from vmodel_contracts.runtime import validate_expert_objections, format_expert_review_rounds
    vague, errors = validate_expert_objections(
        "The artifact hierarchy and authoring rules are not strictly adhered to.", ("architecture",))
    assert vague == [] and "no structured OBJECTION" in errors[0]
    text = ('OBJECTION: artifact=architecture | rule=ADR traceability criterion | '
            'location=ADR-2 field requirement_ids | resolution=Add the governing R-4 id to requirement_ids')
    objections, errors = validate_expert_objections(text, ("architecture",))
    assert not errors and objections[0]["location"] == "ADR-2 field requirement_ids"
    rendered = format_expert_review_rounds([{"rationale":"Trace is absent.", "feedback":text,
                                             "objections":objections}])
    for expected in ("Artifact: architecture", "Rule: ADR traceability criterion",
                     "Location: ADR-2 field requirement_ids",
                     "Resolution: Add the governing R-4 id to requirement_ids"):
        assert expected in rendered


def test_embedded_rationale_after_feedback_is_extracted():
    from vmodel_contracts.runtime import parse_expert_verdict
    verdict = parse_expert_verdict(
        "REGENERATE\nFEEDBACK: OBJECTION: artifact=srs | rule=trace rule | location=R-1 field need_ids | resolution=Add SN-1 to need_ids\nRATIONALE: R-1 has no need trace.",
        ("approve", "regenerate"))
    assert verdict["rationale"] == "R-1 has no need trace."
    assert "RATIONALE:" not in verdict["feedback"]


def test_expert_round_renderer_deduplicates_items_and_rounds():
    from vmodel_contracts.runtime import format_expert_review_rounds
    objection={"artifact":"srs","rule":"need trace rule","location":"R-1 field need_ids","resolution":"Add SN-1 to need_ids"}
    near={**objection,"resolution":"Add SN-1 into need_ids"}
    text=format_expert_review_rounds([
      {"rationale":"Missing trace.","objections":[objection,near]},
      {"rationale":"Still missing.","objections":[objection]}])
    assert text.count("Artifact: srs") == 1
    assert "Round 2: objections identical to round 1" in text
