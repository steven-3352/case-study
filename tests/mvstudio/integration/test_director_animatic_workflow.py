import hashlib
import json
import subprocess

import pytest
import yaml
from PIL import Image

from apps.runtime import build_service
from mv_platform.domain.states import BusinessStage, RuntimeState
from mvstudio.director.alignment import AlignmentResult
from tests.mvstudio.director.test_drafting import FixturePort, _wave


HASH = "sha256:" + "a" * 64


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FixtureAlignmentPort:
    def align(self, task):
        return AlignmentResult(
            entries=tuple(
                {
                    "text": line["text"],
                    "source_line": line["source_line"],
                    "start_seconds": start,
                    "confidence": 0.95,
                }
                for line, start in zip(task.lines, (0.1, 0.6, 1.1, 1.55))
            ),
            provider="fixture-aligner",
            model="fixture-word-timestamps",
            evidence={"kind": "fixture_word_timestamps"},
        )


@pytest.mark.parametrize("semantic_mode", ["configured_model", "offline_unclassified"])
@pytest.mark.parametrize("lyrics_mode", ["timed_lrc", "provider_word_timestamps"])
def test_job_id_action_drafts_and_publishes_540p_structural_animatic(
    tmp_path, semantic_mode, lyrics_mode
):
    service = build_service(tmp_path)
    if lyrics_mode == "provider_word_timestamps":
        service.alignment_port = FixtureAlignmentPort()
    if semantic_mode == "configured_model":
        service.semantic_port = FixturePort()
        service.semantic_model = "fixture-model"
    project = service.create_project(
        "animatic-test",
        {
            "canvas": "9:16",
            "premise": "Two characters choose to stand together.",
            "characters": [
                {"id": "A", "name": "Lead", "traits": ["quiet"]},
                {"id": "B", "name": "Counterpart", "traits": ["bold"]},
            ],
        },
    )
    root = tmp_path / "projects" / project.slug
    audio = root / "inputs/audio/song.wav"
    lyrics = root / "inputs/lyrics/song.lrc"
    first = root / "inputs/characters/a.png"
    second = root / "inputs/characters/b.png"
    _wave(audio)
    lyrics.write_text(
        (
            "[00:00.10]first\n[00:00.60]second\n[00:01.10]third\n[00:01.55]fourth\n"
            if lyrics_mode == "timed_lrc"
            else "first\nsecond\nthird\nfourth\n"
        ),
        encoding="utf-8",
    )
    Image.new("RGBA", (24, 32), (20, 30, 40, 255)).save(first)
    Image.new("RGBA", (24, 32), (50, 60, 70, 255)).save(second)
    source_hashes = (_digest(first), _digest(second))
    job = service.submit_job(
        project.project_id,
        "animatic",
        HASH,
        [
            "inputs/audio/song.wav",
            "inputs/lyrics/song.lrc",
            "inputs/characters/a.png",
            "inputs/characters/b.png",
        ],
    )

    result = (
        service.start_director_animatic_test(job.job_id)
        if semantic_mode == "configured_model"
        else service.start_director_animatic_offline_test(job.job_id)
    )
    inspection = service.inspect_job(job.job_id)
    output = root / result["output"]
    staging = tmp_path / ".mvstudio" / "jobs" / job.job_id

    assert result["status"] == "draft_self_generated"
    assert result["approval_required"] is True
    assert result["semantic_mode"] == semantic_mode
    assert result["lyrics_alignment_mode"] == lyrics_mode
    assert inspection.status.runtime_state is RuntimeState.SUCCEEDED
    assert inspection.status.business_stage is BusinessStage.VISUAL_SCORE_PENDING_USER
    assert output.is_file()
    assert source_hashes == (_digest(first), _digest(second))
    assert yaml.safe_load((staging / "creative/music_map.yaml").read_text())["status"] == "draft_self_generated"
    score = yaml.safe_load((staging / "creative/visual_score.yaml").read_text())
    assert score["status"] == "draft_self_generated"
    assert score["approval_required"] is True
    manifest = json.loads((staging / "artifact-manifest.json").read_text())
    assert all(item["status"] == "draft_self_generated" for item in manifest["artifacts"])
    audit = json.loads((staging / "creative/model_audit.json").read_text())
    assert len(audit["calls"]) == 2
    if lyrics_mode == "provider_word_timestamps":
        alignment_audit = json.loads(
            (staging / "intake/lyrics_alignment_audit.json").read_text()
        )
        assert alignment_audit["provider"] == "fixture-aligner"
    if semantic_mode == "offline_unclassified":
        assert {item["model"] for item in audit["calls"]} == {"offline-structural-v1"}
        assert all(item["usage"] == {"input_tokens": 0, "output_tokens": 0} for item in audit["calls"])
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", str(output),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert (stream["width"], stream["height"]) == (540, 960)
    service.shutdown()
