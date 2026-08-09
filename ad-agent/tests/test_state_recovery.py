from __future__ import annotations

import json
from pathlib import Path

import pytest

from conductor import cli
from conductor.cli import _status_payload
from conductor.conductor import Conductor
from conductor.contracts import DONE, FAILED_RETRYABLE, RUNNING, STALE
from conductor.pipeline import STEP_ORDER
from conductor.state import State


DEPENDENCIES = {
    "00_intake": [],
    "01_analysis": ["00_intake"],
    "02_storyboard": ["01_analysis", "00_intake"],
    "03_keyframes": ["02_storyboard", "00_intake"],
    "04_shots": ["03_keyframes"],
    "05_delivery": ["04_shots", "00_intake", "01_analysis"],
}


def _completed_state(root: Path) -> State:
    state = State(root)
    state.init("demo", STEP_ORDER)
    hashes: dict[str, str] = {}
    for index, sid in enumerate(STEP_ORDER):
        output_hash = f"sha256:{index}"
        state.set_status(
            sid,
            DONE,
            hash=output_hash,
            input_hashes={dep: hashes[dep] for dep in DEPENDENCIES[sid]},
        )
        hashes[sid] = output_hash
    return state


def test_reconcile_marks_changed_output_and_only_dependents_stale(tmp_path: Path) -> None:
    state = _completed_state(tmp_path)
    current = {sid: state.step(sid)["hash"] for sid in STEP_ORDER}
    current["01_analysis"] = "sha256:changed"

    touched = state.reconcile(STEP_ORDER, DEPENDENCIES, current)

    assert state.step("00_intake")["status"] == DONE
    assert state.step("01_analysis")["status"] == STALE
    assert set(touched) == set(STEP_ORDER[1:])
    assert all(state.step(sid)["status"] == STALE for sid in STEP_ORDER[1:])


def test_shot_action_invalidation_preserves_upstream_and_other_units(tmp_path: Path) -> None:
    state = _completed_state(tmp_path)

    touched = state.invalidate_change(
        "shot_action", STEP_ORDER, dependencies=DEPENDENCIES, units=["SH003"]
    )

    assert touched == ["03_keyframes", "04_shots", "05_delivery"]
    assert all(state.step(sid)["status"] == DONE for sid in STEP_ORDER[:3])
    assert state.step("03_keyframes")["stale_units"] == ["SH003"]
    assert state.step("04_shots")["stale_units"] == ["SH003"]


def test_core_selling_point_invalidation_preserves_intake_only(tmp_path: Path) -> None:
    state = _completed_state(tmp_path)

    touched = state.invalidate_change("core_selling_point", STEP_ORDER)

    assert state.step("00_intake")["status"] == DONE
    assert touched == STEP_ORDER[1:]


def test_interrupted_running_step_becomes_retryable_and_is_selected(tmp_path: Path) -> None:
    conductor = Conductor(None, "demo", root=tmp_path)
    conductor.init_project()
    conductor.state.set_status("00_intake", RUNNING)

    spec = conductor.next_step()

    assert spec is not None and spec.step_id == "00_intake"
    assert conductor.state.step("00_intake")["status"] == FAILED_RETRYABLE


def test_approve_cannot_skip_pending_gate(tmp_path: Path) -> None:
    conductor = Conductor(None, "demo", root=tmp_path)
    conductor.init_project()

    with pytest.raises(ValueError, match="expected awaiting_approval"):
        conductor.approve("00_intake")


def test_status_payload_has_stable_machine_readable_shape(tmp_path: Path) -> None:
    conductor = Conductor(None, "demo", root=tmp_path)
    conductor.init_project()

    payload = _status_payload(conductor, "demo")

    assert list(payload) == [
        "schema_version", "project", "production_tier", "steps", "cost"
    ]
    assert [step["id"] for step in payload["steps"]] == STEP_ORDER
    assert all(
        list(step) == ["id", "title", "status", "revision", "stale_units", "reason"]
        for step in payload["steps"]
    )

    events = [json.loads(line) for line in (tmp_path / "conversation.jsonl").read_text().splitlines()]
    assert events[0]["event"] == "project_initialized"
    assert any(event["event"] == "step_status_changed" for event in events) is False


def test_status_json_accepts_flag_before_or_after_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "registry.json"
    project = tmp_path / "project"
    monkeypatch.setattr(cli, "_REGISTRY", registry)
    cli.main(["conductor.cli", "init", "demo", str(project)])
    capsys.readouterr()

    cli.main(["conductor.cli", "status", "demo", "--json"])
    first = json.loads(capsys.readouterr().out)
    cli.main(["conductor.cli", "status", "--json", "demo"])
    second = json.loads(capsys.readouterr().out)

    assert first == second
    assert first["project"] == "demo"
