from __future__ import annotations

import json
import fcntl
from pathlib import Path

import pytest
import yaml

from conductor import cli
from conductor.conductor import Conductor, ProjectBusyError
from conductor.contracts import BLOCKED, FAILED_RETRYABLE, ToolResult
from conductor.pipeline import STEP_BY_ID
from conductor.state import State
from conductor.tools import gen_video


def test_failed_tool_persists_recommendations_and_requires_explicit_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    conductor = Conductor(None, "demo", root=tmp_path)
    conductor.init_project()
    spec = STEP_BY_ID["00_intake"]
    monkeypatch.setattr(
        spec,
        "tool",
        lambda **_kwargs: ToolResult(
            ok=False,
            error={"code": "missing", "message": "material missing", "hint": "add material"},
        ),
    )

    result = conductor.run_step(spec)

    package_path = tmp_path / "00_intake" / "_meta" / "recommendations.yaml"
    package = yaml.safe_load(package_path.read_text(encoding="utf-8"))
    assert result["status"] == BLOCKED
    assert conductor.state.step("00_intake")["status"] == BLOCKED
    assert package["recommended_option"] == "O1"
    assert len(package["options"]) == 2
    assert conductor.next_step() is None

    conductor.retry("00_intake")
    assert conductor.state.step("00_intake")["status"] == FAILED_RETRYABLE
    assert conductor.next_step().step_id == "00_intake"


def test_budget_and_cost_cli_are_machine_readable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = tmp_path / "registry.json"
    project = tmp_path / "project"
    monkeypatch.setattr(cli, "_REGISTRY", registry)
    cli.main(["conductor.cli", "init", "demo", str(project)])
    capsys.readouterr()

    cli.main(["conductor.cli", "budget", "demo", "12.5", "CNY"])
    capsys.readouterr()
    cli.main(["conductor.cli", "cost", "demo", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["currency"] == "CNY"
    assert payload["hard_limit"] == 12.5
    assert payload["spent"] == 0.0
    assert payload["paused"] is False


def test_i2v_unknown_cost_blocks_before_provider_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = tmp_path / "staged"
    keyframes = inputs / "03_keyframes"
    intake = inputs / "00_intake"
    out_dir = tmp_path / "04_shots"
    keyframes.mkdir(parents=True)
    intake.mkdir(parents=True)
    out_dir.mkdir()
    (keyframes / "SH001.png").write_bytes(b"frame")
    (keyframes / "keyframes_index.yaml").write_text(yaml.safe_dump({
        "keyframes": [{
            "id": "SH001", "keyframe": "SH001.png", "type": "generated",
            "motion": "i2v", "duration": 5, "digest": "sha256:fixture",
        }]
    }), encoding="utf-8")
    (intake / "manifest.yaml").write_text(
        yaml.safe_dump({"aspect_ratio": "9:16"}), encoding="utf-8")
    State(tmp_path).init("demo", ["04_shots"])
    monkeypatch.delenv("SEEDANCE_ESTIMATED_COST", raising=False)

    class SeedanceStub:
        def generate(self, _task):
            pytest.fail("provider must not be called before cost confirmation")

    from mvstudio.providers.seedance import SeedancePort
    monkeypatch.setattr(SeedancePort, "from_env", lambda: SeedanceStub())

    result = gen_video([inputs], out_dir, {})

    assert not result.ok
    assert result.error["code"] == "confirmation_required"
    assert result.meta["exit_code"] == 2
    assert result.meta["recommendations"]["status"] == BLOCKED
    assert len(list((tmp_path / ".adfilm" / "jobs").glob("job-*.yaml"))) == 1


def test_second_writer_is_rejected_without_changing_state(tmp_path: Path) -> None:
    conductor = Conductor(None, "demo", root=tmp_path)
    conductor.init_project()
    lock_path = tmp_path / ".adfilm.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ProjectBusyError, match="another session"):
            conductor.run_step(STEP_BY_ID["00_intake"])

    conductor.state.load()
    assert conductor.state.step("00_intake")["status"] == "pending"
