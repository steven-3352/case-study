from __future__ import annotations

from pathlib import Path

import pytest

from conductor.jobs import JobStore, idempotency_key
from conductor.state import State


def _store(tmp_path: Path, *, hard_limit: float | None = 10.0) -> JobStore:
    state = State(tmp_path)
    state.init("demo", ["04_shots"])
    state.configure_budget(hard_limit=hard_limit, currency="USD")
    return JobStore(tmp_path)


def test_idempotency_key_is_deterministic_and_request_order_independent() -> None:
    one = idempotency_key(
        project="demo", node="N11", shot_id="SH004", provider_id="seedance-2.0",
        request={"prompt": "move", "duration": 5},
    )
    two = idempotency_key(
        project="demo", node="N11", shot_id="SH004", provider_id="seedance-2.0",
        request={"duration": 5, "prompt": "move"},
    )

    assert one == two
    assert one.startswith("idem-")


def test_duplicate_key_reuses_job_and_does_not_reserve_cost_twice(tmp_path: Path) -> None:
    store = _store(tmp_path)
    kwargs = {
        "node": "N11", "shot_id": "SH004", "provider_id": "seedance-2.0",
        "request": {"prompt": "move"}, "estimated_cost": 2.5,
    }

    first = store.prepare(**kwargs)
    second = store.prepare(**kwargs)

    assert first["job_id"] == second["job_id"]
    assert second["reused"] is True
    assert store.cost_summary()["estimated"] == 2.5
    assert len(State(tmp_path).load().cost()["ledger"]) == 1


def test_unknown_estimate_requires_confirmation_and_shows_history(tmp_path: Path) -> None:
    store = _store(tmp_path)
    old = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        request={"version": 1}, estimated_cost=1.0,
    )
    store.mark_running(old["job_id"])
    store.complete(old["job_id"], actual_cost=1.75)
    unknown = store.prepare(
        node="N11", shot_id="SH002", provider_id="seedance-2.0",
        request={"version": 1}, estimated_cost=None,
    )

    blocked = store.authorize_submission(unknown["job_id"])
    allowed = store.authorize_submission(unknown["job_id"], confirm=True)
    resumed = JobStore(tmp_path).authorize_submission(unknown["job_id"])

    assert blocked["error"]["code"] == "confirmation_required"
    assert blocked["exit_code"] == 2
    assert blocked["historical_cost_range"] == {
        "count": 1, "min": 1.75, "max": 1.75, "currency": "USD"
    }
    assert allowed["ok"] is True and allowed["submit"] is True
    assert resumed["ok"] is True and resumed["submit"] is True
    assert resumed["job"]["confirmed_at"] is not None
    assert State(tmp_path).load().cost()["confirmed"] is True


def test_batch_unknown_cost_confirmation_survives_restart(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        estimated_cost=None,
    )
    store.authorize_submission(first["job_id"], confirm=True, confirmation_scope="batch")
    second = JobStore(tmp_path).prepare(
        node="N11", shot_id="SH002", provider_id="seedance-2.0",
        estimated_cost=None,
    )

    decision = JobStore(tmp_path).authorize_submission(second["job_id"])

    assert decision["ok"] is True and decision["submit"] is True
    assert decision["job"]["confirmed_at"] is not None


def test_hard_limit_blocks_before_submission_with_three_options(tmp_path: Path) -> None:
    store = _store(tmp_path, hard_limit=3.0)
    first = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        estimated_cost=2.0,
    )
    assert store.authorize_submission(first["job_id"])["ok"] is True
    second = store.prepare(
        node="N11", shot_id="SH002", provider_id="seedance-2.0",
        estimated_cost=2.0,
    )

    decision = store.authorize_submission(second["job_id"])

    assert second["status"] == "blocked_budget"
    assert decision["submit"] is False
    assert decision["status"] == "blocked_with_recommendations"
    assert len(decision["recommendations"]) == 3
    assert store.cost_summary()["estimated"] == 2.0


def test_actual_cost_crossing_limit_pauses_following_jobs_without_double_charge(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path, hard_limit=3.0)
    job = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        estimated_cost=2.0,
    )
    store.mark_running(job["job_id"])

    first = store.complete(job["job_id"], actual_cost=3.5)
    duplicate = store.complete(job["job_id"], actual_cost=3.5)
    following = store.prepare(
        node="N11", shot_id="SH002", provider_id="seedance-2.0",
        estimated_cost=0.1,
    )
    decision = store.authorize_submission(following["job_id"])

    assert first["paused"] is True
    assert duplicate["paused"] is True
    assert store.cost_summary()["spent"] == 3.5
    assert decision["error"]["code"] == "budget_hard_limit"
    assert len(decision["recommendations"]) == 3
    assert (tmp_path / ".adfilm" / "jobs" / f"{job['job_id']}.yaml").is_file()
    assert not list((tmp_path / ".adfilm" / "jobs").glob("*.tmp"))


def test_submission_rechecks_budget_after_previous_actual_exceeds_estimate(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path, hard_limit=5.0)
    first = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        estimated_cost=2.0,
    )
    second = store.prepare(
        node="N11", shot_id="SH002", provider_id="seedance-2.0",
        estimated_cost=2.0,
    )
    store.mark_running(first["job_id"])
    store.complete(first["job_id"], actual_cost=4.0)

    decision = store.authorize_submission(second["job_id"])

    assert decision["submit"] is False
    assert decision["error"]["code"] == "budget_hard_limit"
    assert store.get(second["job_id"])["status"] == "blocked_budget"
    assert store.cost_summary()["paused"] is True


def test_duplicate_done_job_repairs_missing_state_ledger_without_double_charge(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    job = store.prepare(
        node="N11", shot_id="SH001", provider_id="seedance-2.0",
        estimated_cost=1.0,
    )
    store.mark_running(job["job_id"])
    store.complete(job["job_id"], actual_cost=1.25)

    state = State(tmp_path).load()
    state.cost()["ledger"] = []
    state.cost()["spent"] = 0.0
    state.save()

    repaired = store.complete(job["job_id"], actual_cost=1.25)
    repeated = store.complete(job["job_id"], actual_cost=1.25)

    assert repaired["job"]["status"] == "done"
    assert repeated["job"]["status"] == "done"
    assert store.cost_summary()["spent"] == 1.25
    assert len(State(tmp_path).load().cost()["ledger"]) == 1


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_invalid_cost_values_are_rejected(tmp_path: Path, value: float) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="estimated_cost"):
        store.prepare(
            node="N11", shot_id="SH001", provider_id="seedance-2.0",
            estimated_cost=value,
        )
