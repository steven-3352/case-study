import os
from datetime import datetime, timezone

import pytest

from mv_platform.config import InfrastructureError, Settings
from mv_platform.domain import (
    Artifact,
    BusinessStage,
    Event,
    JobSpec,
    JobStatus,
    Project,
    RuntimeState,
)
from mv_platform.infrastructure import (
    ArtifactStore,
    Database,
    Repository,
    RepositoryConflict,
    RepositoryNotFound,
    UnsafePathError,
)


NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)
H1 = "sha256:" + "1" * 64
H2 = "sha256:" + "2" * 64


def project(project_id="p1", slug="film-one"):
    return Project(project_id, slug, "projects/" + slug, H1, NOW)


def job(job_id="j1", project_id="p1", key="idem-1"):
    return JobSpec(
        job_id,
        project_id,
        "render",
        ("assets/a.png",),
        H1,
        "pipeline-v1",
        "contract-v1",
        "policy-v1",
        "consent-v1",
        ("build/final.mp4",),
        key,
    )


def repository(tmp_path):
    database = Database(tmp_path / "db" / "app.sqlite3")
    database.migrate()
    return database, Repository(database)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": "0.0.0.0"},
        {"port": True},
        {"port": 0},
        {"max_active_jobs": 0},
        {"data_root": "/tmp/data"},
        {"db_path": "data/../outside.sqlite3"},
        {"project_root": "data\\..\\outside"},
        {"project_root": None},
    ],
)
def test_settings_fail_closed(kwargs):
    with pytest.raises(InfrastructureError):
        Settings(**kwargs)


def test_migration_is_idempotent_and_has_required_constraints(tmp_path):
    database = Database(tmp_path / "db" / "app.sqlite3")
    database.migrate()
    database.migrate()
    with database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] > 0
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"projects", "jobs", "job_status", "events", "artifacts"} <= tables


def test_full_roundtrip_sequence_idempotency_and_rollback(tmp_path):
    _, repo = repository(tmp_path)
    p = project()
    j = job()
    assert repo.add_project(p) == p
    assert repo.get_project("p1") == p
    assert repo.add_job(j) == j
    assert repo.add_job(j) == j
    assert repo.get_job("j1") == j

    status = JobStatus("j1", RuntimeState.QUEUED, BusinessStage.INTAKE_VALIDATED, 1, NOW)
    repo.set_status(status)
    assert repo.get_status("j1") == status

    first = Event("j1", 1, "job.created", NOW, {"nested": {"ok": True}})
    second = Event("j1", 2, "job.running", NOW, {})
    repo.append_event(first)
    with pytest.raises(RepositoryConflict):
        repo.append_event(Event("j1", 3, "gap", NOW, {}))
    repo.append_event(second)
    assert [event.seq for event in repo.list_events("j1")] == [1, 2]
    assert [event.seq for event in repo.list_events("j1", after_seq=1)] == [2]

    artifact = Artifact("a1", "p1", "j1", "1", "build/final.mp4", (H1,), H2, NOW, "worker", "published")
    repo.add_artifact(artifact)
    assert repo.list_artifacts("j1") == [artifact]

    conflicting = job(job_id="j2", key="idem-1")
    with pytest.raises(RepositoryConflict):
        repo.add_job(conflicting)
    with pytest.raises(RepositoryNotFound):
        repo.get_job("j2")


def test_artifact_cannot_cross_project_and_job_boundary(tmp_path):
    _, repo = repository(tmp_path)
    repo.add_project(project())
    repo.add_project(project("p2", "film-two"))
    repo.add_job(job())
    crossed = Artifact("cross", "p2", "j1", "1", "build/x", (H1,), H2, NOW, "worker", "staged")
    with pytest.raises(RepositoryConflict):
        repo.add_artifact(crossed)


def test_artifact_store_rejects_path_and_identifier_escape(tmp_path):
    projects = tmp_path / "projects"
    jobs = tmp_path / "jobs"
    store = ArtifactStore(projects, jobs)
    for slug in ("../outside", "/absolute"):
        with pytest.raises(UnsafePathError):
            store.validate_project_path(slug, "build/a.mp4")
    for job_id in ("../outside", "/absolute"):
        with pytest.raises(UnsafePathError):
            store.validate_job_path(job_id, "stage/a.mp4")
    with pytest.raises(UnsafePathError):
        store.validate_project_path("film", "../outside")


def test_artifact_store_rejects_symlink_and_publishes_atomically(tmp_path):
    projects = tmp_path / "projects"
    jobs = tmp_path / "jobs"
    staged = jobs / "j1" / "stage" / "clip.bin"
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"mv-data")
    store = ArtifactStore(projects, jobs)

    digest, size = store.publish(staged, "film-one", "build/final.bin")
    destination = projects / "film-one" / "build" / "final.bin"
    assert destination.read_bytes() == b"mv-data"
    assert digest == "sha256:" + __import__("hashlib").sha256(b"mv-data").hexdigest()
    assert size == 7
    assert not list(destination.parent.glob(".publish-*"))

    outside = tmp_path / "outside"
    outside.mkdir()
    link = projects / "film-link"
    os.symlink(outside, link)
    with pytest.raises(UnsafePathError):
        store.publish(staged, "film-link", "escaped.bin")
