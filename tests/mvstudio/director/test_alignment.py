import json

import pytest

from mvstudio.director.alignment import (
    AlignmentResult,
    LyricAlignmentError,
    align_plain_lyrics,
)
from mvstudio.director.intake import inspect_intake
from tests.mvstudio.director.test_intake import _inputs


class FixtureAlignmentPort:
    def __init__(self, entries=None):
        self.entries = entries
        self.tasks = []

    def align(self, task):
        self.tasks.append(task)
        entries = self.entries or (
            {"text": "line one", "source_line": 1, "start_seconds": 0.01, "confidence": 0.97},
            {"text": "line two", "source_line": 2, "start_seconds": 0.06, "confidence": 0.91},
        )
        return AlignmentResult(
            entries=tuple(entries),
            provider="fixture-aligner",
            model="fixture-word-timestamps",
            evidence={"words": [{"text": "line one"}, {"text": "line two"}]},
        )


def _plain_intake(tmp_path):
    value = _inputs(tmp_path, "line one\nline two\n")
    return inspect_intake(value, tmp_path)


def test_plain_lyrics_alignment_writes_hash_bound_timed_contract(tmp_path):
    intake = _plain_intake(tmp_path)
    port = FixtureAlignmentPort()
    updated, timed = align_plain_lyrics(intake, tmp_path, port)

    assert updated["lyrics"]["alignment_state"] == "aligned_provider"
    assert [item["start_seconds"] for item in timed["entries"]] == [0.01, 0.06]
    assert timed["entries"][0]["end_seconds"] == 0.06
    assert timed["alignment"]["audio_digest"] == intake["audio"]["digest"]
    assert timed["alignment"]["lyrics_digest"] == intake["lyrics"]["digest"]
    assert port.tasks[0].audio_path == tmp_path / "inputs/audio/song.wav"
    manifest = json.loads((tmp_path / "intake/intake_manifest.json").read_text())
    audit = json.loads((tmp_path / "intake/lyrics_alignment_audit.json").read_text())
    assert manifest["lyrics"]["alignment_state"] == "aligned_provider"
    evidence = json.loads((tmp_path / "intake/lyrics_alignment_evidence.json").read_text())
    assert audit["evidence_hash"] == evidence["evidence_hash"]
    assert evidence["evidence"]["words"][0]["text"] == "line one"


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        (
            ({"text": "changed", "source_line": 1, "start_seconds": 0.01, "confidence": 0.9},
             {"text": "line two", "source_line": 2, "start_seconds": 0.06, "confidence": 0.9}),
            "changed plain lyric",
        ),
        (
            ({"text": "line one", "source_line": 1, "start_seconds": 0.06, "confidence": 0.9},
             {"text": "line two", "source_line": 2, "start_seconds": 0.01, "confidence": 0.9}),
            "strictly advance",
        ),
        (
            ({"text": "line one", "source_line": 1, "start_seconds": float("nan"), "confidence": 0.9},
             {"text": "line two", "source_line": 2, "start_seconds": 0.06, "confidence": 0.9}),
            "strictly advance",
        ),
    ],
)
def test_alignment_rejects_changed_text_and_non_monotonic_evidence(tmp_path, entries, message):
    intake = _plain_intake(tmp_path)
    with pytest.raises(LyricAlignmentError, match=message):
        align_plain_lyrics(intake, tmp_path, FixtureAlignmentPort(entries))
    assert not (tmp_path / "intake/lyrics_timed.json").exists()
    manifest = json.loads((tmp_path / "intake/intake_manifest.json").read_text())
    assert manifest["lyrics"]["alignment_state"] == "alignment_required"


def test_alignment_rechecks_audio_hash_before_provider_call(tmp_path):
    intake = _plain_intake(tmp_path)
    (tmp_path / "inputs/audio/song.wav").write_bytes(b"changed")
    port = FixtureAlignmentPort()
    with pytest.raises(LyricAlignmentError, match="audio hash differs"):
        align_plain_lyrics(intake, tmp_path, port)
    assert port.tasks == []


def test_alignment_rejects_replaced_intake_directory_before_provider_call(tmp_path):
    intake = _plain_intake(tmp_path)
    real = tmp_path / "intake-real"
    (tmp_path / "intake").rename(real)
    (tmp_path / "intake").symlink_to(real, target_is_directory=True)
    port = FixtureAlignmentPort()
    with pytest.raises(LyricAlignmentError, match="intake directory"):
        align_plain_lyrics(intake, tmp_path, port)
    assert port.tasks == []
