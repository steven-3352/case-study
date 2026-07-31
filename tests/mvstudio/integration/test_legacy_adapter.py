import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from mv_platform.domain import JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.database import Database
from mv_platform.infrastructure.repositories import Repository
from mv_platform.supervisor import JobSupervisor


H = "sha256:" + "a" * 64


def _supervisor(tmp_path):
    database = Database(tmp_path / ".mvstudio" / "app.sqlite3")
    database.migrate()
    repository = Repository(database)
    now = datetime.now(timezone.utc)
    repository.add_project(Project("project", "fixture", "projects/fixture", H, now))
    for job_id in ("left", "right"):
        repository.add_job(JobSpec(job_id, "project", "render", (), H, "v1", "v1",
                                   "local", "local", (), job_id))
        repository.set_status(JobStatus(job_id, RuntimeState.QUEUED,
                                        BusinessStage.INTAKE_PENDING, 1, now))
    return JobSupervisor(database, tmp_path / ".mvstudio" / "jobs", 2)


def _source_hashes():
    root = Path(__file__).resolve().parents[3]
    paths = list((root / "src").rglob("*.py")) + list((root / "mv_platform").rglob("*.py"))
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def test_two_legacy_jobs_are_isolated_and_source_is_unchanged(tmp_path):
    before = _source_hashes()
    supervisor = _supervisor(tmp_path)
    supervisor.submit("left", executor="legacy",
                      executor_input={"marker": "LEFT", "steps": 2, "delay_seconds": 0.01})
    supervisor.submit("right", executor="legacy",
                      executor_input={"marker": "RIGHT", "steps": 2, "delay_seconds": 0.01})

    assert supervisor.wait("left", 10).runtime_state is RuntimeState.SUCCEEDED
    assert supervisor.wait("right", 10).runtime_state is RuntimeState.SUCCEEDED
    left = json.loads((tmp_path / ".mvstudio/jobs/left/legacy-result.json").read_text())
    right = json.loads((tmp_path / ".mvstudio/jobs/right/legacy-result.json").read_text())
    assert left["marker"] == "LEFT" and right["marker"] == "RIGHT"
    assert "RIGHT" not in json.dumps(left) and "LEFT" not in json.dumps(right)
    assert before == _source_hashes()
    supervisor.shutdown()
