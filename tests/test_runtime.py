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
