import json
from datetime import datetime, timezone

from mv_platform.domain import JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.database import Database
from mv_platform.infrastructure.repositories import Repository
from mv_platform.supervisor import JobSupervisor


H = "sha256:" + "a" * 64


def test_two_director_jobs_are_isolated(tmp_path):
    from tests.mvstudio.director.conftest import director_package as package_fixture

    director_package = package_fixture.__wrapped__()
    database = Database(tmp_path / ".mvstudio" / "app.sqlite3")
    database.migrate()
    repository = Repository(database)
    now = datetime.now(timezone.utc)
    repository.add_project(Project("project", "fixture", "projects/fixture", H, now))
    supervisor = JobSupervisor(database, tmp_path / ".mvstudio" / "jobs", 2)

    for job_id, premise in (("left", "LEFT"), ("right", "RIGHT")):
        repository.add_job(JobSpec(job_id, "project", "compile", (), H, "v1", "v1", "local", "local", (), job_id))
        repository.set_status(JobStatus(job_id, RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, now))
        payload = json.loads(json.dumps(director_package))
        payload["project_id"] = "project"
        payload["brief"]["premise"] = premise
        payload["visual_score"]["project"]["premise"] = premise
        supervisor.submit(job_id, executor="director", executor_input=payload)

    assert supervisor.wait("left", 15).runtime_state is RuntimeState.SUCCEEDED
    assert supervisor.wait("right", 15).runtime_state is RuntimeState.SUCCEEDED
    left = (tmp_path / ".mvstudio/jobs/left/creative/story_framework.yaml").read_text()
    right = (tmp_path / ".mvstudio/jobs/right/creative/story_framework.yaml").read_text()
    assert "LEFT" in left and "RIGHT" not in left
    assert "RIGHT" in right and "LEFT" not in right
    assert supervisor.model_call_count == 0
    assert supervisor.token_count == 0
    supervisor.shutdown()
