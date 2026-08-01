import hashlib
import json
import subprocess
from types import SimpleNamespace

import pytest
from PIL import Image

from apps.runtime import build_service
from mv_platform.application import ApplicationBlocked
from mv_platform.domain.hashing import canonical_hash
from mv_platform.domain.states import BusinessStage, RuntimeState
from mvstudio.providers.seedance import SeedanceProviderError


def _hash_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _video_bytes(path):
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "color=c=black:s=720x1280:r=6:d=4",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return path.read_bytes()


class FixtureSeedancePort:
    def __init__(self, video):
        self.video = video
        self.calls = []

    def generate(self, task):
        self.calls.append(task)
        return SimpleNamespace(
            video_bytes=self.video,
            video_sha256=_hash_bytes(self.video),
            provider="fixture-seedance",
            model=task.model,
            task_id="fixture-task",
            request_contract_sha256="sha256:" + "b" * 64,
            first_frame_sha256=task.first_frame.sha256,
        )


class FailingSeedancePort:
    def __init__(self):
        self.calls = 0

    def generate(self, _task):
        self.calls += 1
        raise SeedanceProviderError("upstream uncertain")


def _project_job(tmp_path, port):
    service = build_service(tmp_path)
    service.seedance_port = port
    project = service.create_project("qingyi", {"title": "Qingyi", "canvas": "9:16"})
    root = tmp_path / "projects" / "qingyi"
    frame = root / "assets/source/keyframes/shot-001.png"
    frame.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (720, 1280), (30, 40, 35)).save(frame)
    frame_hash = _hash_bytes(frame.read_bytes())
    contract = {
        "version": 1,
        "status": "approved",
        "project_id": project.project_id,
        "shot_id": "shot-001",
        "model": "doubao-seedance-2-0",
        "prompt": "A restrained push-in; fabric and hair move naturally in a light breeze.",
        "duration_seconds": 4,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "first_frame": {
            "path": "assets/source/keyframes/shot-001.png",
            "sha256": frame_hash,
        },
        "approved_by": "user",
        "approved_at": "2026-07-31T12:00:00+08:00",
    }
    contract_path = root / "creative/approved_shots/shot-001.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(
        json.dumps(contract, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    )
    job = service.submit_job(
        project.project_id,
        "generate",
        canonical_hash(contract),
        input_refs=(
            "creative/approved_shots/shot-001.json",
            "assets/source/keyframes/shot-001.png",
        ),
        model_policy_ref="doubao-seedance-2-0",
    )
    return service, project, job, frame, contract_path


def test_approved_shot_generates_qc_and_pending_diagnosis_preview(tmp_path):
    video = _video_bytes(tmp_path / "fixture.mp4")
    port = FixtureSeedancePort(video)
    service, _project, job, frame, contract = _project_job(tmp_path, port)
    source_hashes = (_hash_bytes(frame.read_bytes()), _hash_bytes(contract.read_bytes()))

    result = service.start_seedance_shot(job.job_id)
    inspection = service.inspect_job(job.job_id)
    preview = tmp_path / "projects/qingyi" / result["preview"]
    staging = tmp_path / ".mvstudio/jobs" / job.job_id

    assert len(port.calls) == 1
    assert result["status"] == "pending_diagnosis"
    assert result["diagnosis_required"] is True
    assert result["user_approval_required"] is True
    assert "_pending-diagnosis.mp4" in result["preview"]
    assert preview.read_bytes() == video
    assert inspection.status.runtime_state is RuntimeState.SUCCEEDED
    assert inspection.status.business_stage is BusinessStage.GENERATION_PARTIAL
    assert source_hashes == (_hash_bytes(frame.read_bytes()), _hash_bytes(contract.read_bytes()))
    qc = json.loads((staging / "generated/shot_qc.json").read_bytes())
    assert qc["status"] == "pass_gate_checked"
    assert json.loads((staging / "generated/provider_audit.json").read_bytes())[
        "status"
    ] == "generated_pending_qc"
    service.shutdown()


def test_uncertain_provider_failure_is_not_automatically_retried(tmp_path):
    port = FailingSeedancePort()
    service, _project, job, _frame, _contract = _project_job(tmp_path, port)

    with pytest.raises(ApplicationBlocked, match="automatic paid retry"):
        service.start_seedance_shot(job.job_id)
    with pytest.raises(ApplicationBlocked, match="already attempted"):
        service.start_seedance_shot(job.job_id)

    assert port.calls == 1
    assert service.inspect_job(job.job_id).status.runtime_state is RuntimeState.QUEUED
    service.shutdown()


def test_configuration_error_does_not_consume_paid_attempt_claim(tmp_path, monkeypatch):
    video = _video_bytes(tmp_path / "fixture.mp4")
    fixture = FixtureSeedancePort(video)
    service, _project, job, _frame, _contract = _project_job(tmp_path, fixture)
    service.seedance_port = None
    for name in ("SEEDANCE_BASE_URL", "SEEDANCE_API_KEY", "SEEDANCE_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ApplicationBlocked, match="configuration"):
        service.start_seedance_shot(job.job_id)

    claim = tmp_path / ".mvstudio/jobs" / job.job_id / ".seedance-request-claimed"
    assert not claim.exists()
    service.seedance_port = fixture
    result = service.start_seedance_shot(job.job_id)

    assert result["status"] == "pending_diagnosis"
    assert len(fixture.calls) == 1
    service.shutdown()
