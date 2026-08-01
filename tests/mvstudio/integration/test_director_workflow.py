import hashlib
import json
import wave

import pytest
from PIL import Image

from mv_platform.application import ApplicationBlocked, ApplicationConflict, ApplicationService
from mv_platform.config import Settings
from mv_platform.domain.hashing import canonical_hash
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.database import Database
from mv_platform.supervisor import JobSupervisor


def _write_inputs(project_root):
    audio = project_root / "inputs/audio/song.wav"
    with wave.open(str(audio), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * 1600)
    (project_root / "inputs/lyrics/song.lrc").write_text(
        "[00:00.00]first\n[00:00.10]second\n", encoding="utf-8"
    )
    portrait = project_root / "inputs/characters/lead.png"
    Image.new("RGBA", (24, 32), (90, 30, 10, 200)).save(portrait)
    return portrait.read_bytes()


def _service(tmp_path):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(settings, database, workspace_root=tmp_path)
    service.initialize()
    supervisor = JobSupervisor(database, tmp_path / settings.data_root / "jobs", 1)
    service.supervisor = supervisor
    return service, supervisor


def test_three_input_intake_compile_approval_and_publication(tmp_path):
    from tests.mvstudio.director.conftest import director_package as package_fixture

    service, supervisor = _service(tmp_path)
    project = service.create_project("film", {"canvas": "9:16"})
    project_root = tmp_path / "projects/film"
    portrait_bytes = _write_inputs(project_root)
    refs = (
        "inputs/audio/song.wav",
        "inputs/lyrics/song.lrc",
        "inputs/characters/lead.png",
    )
    intake = service.submit_job(project.project_id, "analyze", canonical_hash({"refs": refs}), input_refs=refs)
    service.start_director_intake(intake.job_id)
    assert supervisor.wait(intake.job_id, 15).runtime_state is RuntimeState.SUCCEEDED
    intake_manifest = json.loads(
        (tmp_path / ".mvstudio/jobs" / intake.job_id / "intake/intake_manifest.json").read_text()
    )
    assert intake_manifest["lyrics"]["alignment_state"] == "aligned"
    assert (project_root / "inputs/characters/lead.png").read_bytes() == portrait_bytes

    package = package_fixture.__wrapped__()
    package["project_id"] = project.project_id
    package["animatic"]["enabled"] = True
    compile_job = service.submit_job(
        project.project_id, "compile", canonical_hash(package), requested_outputs=("creative/shots.yaml",)
    )
    service.start_job(compile_job.job_id, "director", package)
    assert supervisor.wait(compile_job.job_id, 20).runtime_state is RuntimeState.SUCCEEDED

    approval = service.approve_director_artifacts(compile_job.job_id)
    assert approval["status"] == "approved"
    assert service.inspect_job(compile_job.job_id).status.business_stage is BusinessStage.QC_PASSED
    receipt = service.publish_director_artifacts(compile_job.job_id)
    assert receipt["status"] == "published"
    assert (project_root / "creative/shots.yaml").is_file()
    assert (project_root / "outputs/animatic.mp4").is_file()
    assert service.inspect_job(compile_job.job_id).status.business_stage is BusinessStage.EXPORTED

    manifest = json.loads(
        (tmp_path / ".mvstudio/jobs" / compile_job.job_id / "artifact-manifest.json").read_text()
    )
    assert {item["job_id"] for item in manifest["artifacts"]} == {compile_job.job_id}
    assert {item["status"] for item in manifest["artifacts"]} == {"approved"}
    assert service.publish_director_artifacts(compile_job.job_id)["status"] == "published"
    supervisor.shutdown()


def test_publication_rejects_hash_tampering_and_existing_conflict(tmp_path):
    from tests.mvstudio.director.conftest import director_package as package_fixture

    service, supervisor = _service(tmp_path)
    project = service.create_project("film", {"canvas": "9:16"})
    package = package_fixture.__wrapped__()
    package["project_id"] = project.project_id
    package["animatic"]["enabled"] = True
    job = service.submit_job(project.project_id, "compile", canonical_hash(package))
    service.start_job(job.job_id, "director", package)
    assert supervisor.wait(job.job_id, 20).runtime_state is RuntimeState.SUCCEEDED
    with pytest.raises(ApplicationBlocked, match="not approved"):
        service.publish_director_artifacts(job.job_id)
    service.approve_director_artifacts(job.job_id)

    destination = tmp_path / "projects/film/creative/shots.yaml"
    destination.write_text("existing approved content", encoding="utf-8")
    before = hashlib.sha256(destination.read_bytes()).hexdigest()
    with pytest.raises(ApplicationConflict, match="overwrite"):
        service.publish_director_artifacts(job.job_id)
    with pytest.raises(ApplicationConflict, match="unverified"):
        service.publish_director_artifacts(job.job_id, supersede=True)
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == before
    assert not (tmp_path / "projects/film/outputs/animatic.mp4").exists()
    supervisor.shutdown()


def test_publication_can_supersede_only_a_verified_prior_publication(tmp_path):
    from tests.mvstudio.director.conftest import director_package as package_fixture

    service, supervisor = _service(tmp_path)
    project = service.create_project("film", {"canvas": "9:16"})

    first_package = package_fixture.__wrapped__()
    first_package["project_id"] = project.project_id
    first_job = service.submit_job(
        project.project_id, "compile", canonical_hash(first_package)
    )
    service.start_job(first_job.job_id, "director", first_package)
    assert supervisor.wait(first_job.job_id, 20).runtime_state is RuntimeState.SUCCEEDED
    service.approve_director_artifacts(first_job.job_id)
    service.publish_director_artifacts(first_job.job_id)

    second_package = package_fixture.__wrapped__()
    second_package["project_id"] = project.project_id
    second_package["visual_score"]["shots"][0]["primary_action"] = (
        "A steps into the shared light before B becomes visible"
    )
    second_job = service.submit_job(
        project.project_id, "compile", canonical_hash(second_package)
    )
    service.start_job(second_job.job_id, "director", second_package)
    assert supervisor.wait(second_job.job_id, 20).runtime_state is RuntimeState.SUCCEEDED
    service.approve_director_artifacts(second_job.job_id)

    with pytest.raises(ApplicationConflict, match="overwrite"):
        service.publish_director_artifacts(second_job.job_id)
    receipt = service.publish_director_artifacts(second_job.job_id, supersede=True)
    assert receipt["status"] == "published"
    assert receipt["supersedes_job_ids"] == (first_job.job_id,)
    second_manifest = json.loads(
        (tmp_path / ".mvstudio/jobs" / second_job.job_id / "artifact-manifest.json").read_text()
    )
    expected = {
        item["path"]: item["content_hash"] for item in second_manifest["artifacts"]
    }
    for relative, digest in expected.items():
        published = tmp_path / "projects/film" / relative
        assert "sha256:" + hashlib.sha256(published.read_bytes()).hexdigest() == digest
    supervisor.shutdown()
