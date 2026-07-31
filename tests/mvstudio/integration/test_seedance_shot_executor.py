import hashlib
import json
import subprocess
from datetime import datetime, timezone

import pytest

from mv_platform.domain import JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.database import Database
from mv_platform.infrastructure.repositories import Repository
from mv_platform.supervisor import InvalidExecutorInput, JobSupervisor


H = "sha256:" + "a" * 64


def _fixture_video(path, duration=4):
    path.parent.mkdir(parents=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "color=c=black:s=720x1280:r=12:d=" + str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _supervisor(tmp_path, job_id="shot-job"):
    database = Database(tmp_path / ".mvstudio" / "app.sqlite3")
    database.migrate()
    repository = Repository(database)
    now = datetime.now(timezone.utc)
    repository.add_project(Project("project-qingyi", "qingyi", "projects/qingyi", H, now))
    repository.add_job(
        JobSpec(job_id, "project-qingyi", "generate", (), H, "v1", "v1", "seedance", "local", (), job_id)
    )
    repository.set_status(
        JobStatus(job_id, RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, now)
    )
    return JobSupervisor(database, tmp_path / ".mvstudio" / "jobs", 1), repository


def test_seedance_shot_qc_runs_in_isolated_worker(tmp_path):
    supervisor, _repository = _supervisor(tmp_path)
    video = tmp_path / ".mvstudio" / "jobs" / "shot-job" / "generated" / "shot-001.mp4"
    digest = _fixture_video(video)
    payload = {
        "project_id": "project-qingyi",
        "shot_id": "shot-001",
        "video_path": "generated/shot-001.mp4",
        "video_sha256": digest,
        "duration_seconds": 4,
        "width": 720,
        "height": 1280,
    }

    supervisor.submit("shot-job", "seedance_shot_qc", payload)
    completed = supervisor.wait("shot-job", 15)

    assert completed.runtime_state is RuntimeState.SUCCEEDED
    report = json.loads((video.parent / "shot_qc.json").read_bytes())
    assert report["status"] == "pass_gate_checked"
    assert report["diagnosis_required"] is True
    assert report["user_approval_required"] is True
    assert report["video_sha256"] == digest
    supervisor.shutdown()


def test_seedance_shot_qc_rejects_paths_outside_generated(tmp_path):
    supervisor, _repository = _supervisor(tmp_path)
    payload = {
        "project_id": "project-qingyi",
        "shot_id": "shot-001",
        "video_path": "../source.mp4",
        "video_sha256": H,
        "duration_seconds": 4,
        "width": 720,
        "height": 1280,
    }
    with pytest.raises(InvalidExecutorInput, match="under generated"):
        supervisor.submit("shot-job", "seedance_shot_qc", payload)
    supervisor.shutdown()


def test_seedance_shot_qc_fails_on_hash_change(tmp_path):
    supervisor, _repository = _supervisor(tmp_path)
    video = tmp_path / ".mvstudio" / "jobs" / "shot-job" / "generated" / "shot-001.mp4"
    _fixture_video(video)
    payload = {
        "project_id": "project-qingyi",
        "shot_id": "shot-001",
        "video_path": "generated/shot-001.mp4",
        "video_sha256": H,
        "duration_seconds": 4,
        "width": 720,
        "height": 1280,
    }

    supervisor.submit("shot-job", "seedance_shot_qc", payload)
    completed = supervisor.wait("shot-job", 15)

    assert completed.runtime_state is RuntimeState.FAILED
    assert completed.status.error_code == "worker_error"
    assert not (video.parent / "shot_qc.json").exists()
    supervisor.shutdown()
