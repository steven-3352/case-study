import json

import pytest

from mvstudio.director.alignment import (
    AlignmentResult,
    LyricAlignmentError,
    align_plain_lyrics,
    normalize_token,
    proportional_entries,
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


def test_normalize_token_keeps_cjk_and_drops_punctuation():
    assert normalize_token(" 月亮，升起! ") == "月亮升起"
    assert normalize_token("Hello, World.") == "helloworld"


def test_proportional_entries_maps_lines_without_exact_transcript():
    # transcript ("la la la la") deliberately does NOT match the lyrics
    words = [
        {"text": "la", "start": 0.1, "end": 0.4, "probability": 0.9},
        {"text": "la", "start": 0.5, "end": 0.9, "probability": 0.8},
        {"text": "la", "start": 1.0, "end": 1.4, "probability": 0.7},
        {"text": "la", "start": 1.5, "end": 1.9, "probability": 0.6},
    ]
    lines = [
        {"text": "第一句歌词", "source_line": 1},
        {"text": "第二句歌词呀", "source_line": 2},
    ]
    entries = proportional_entries(words, lines, duration=2.0)
    assert [entry["text"] for entry in entries] == ["第一句歌词", "第二句歌词呀"]
    assert [entry["source_line"] for entry in entries] == [1, 2]
    starts = [entry["start_seconds"] for entry in entries]
    assert starts[0] < starts[1] < 2.0
    assert all(0.0 <= entry["confidence"] <= 1.0 for entry in entries)


def test_proportional_entries_even_spread_when_no_words():
    lines = [
        {"text": "第一句", "source_line": 1},
        {"text": "第二句", "source_line": 2},
        {"text": "第三句", "source_line": 3},
    ]
    entries = proportional_entries([], lines, duration=6.0)
    starts = [entry["start_seconds"] for entry in entries]
    assert starts == sorted(starts)
    assert starts[0] < starts[1] < starts[2] < 6.0
    assert [entry["text"] for entry in entries] == ["第一句", "第二句", "第三句"]


def test_proportional_entries_forces_strictly_increasing_within_duration():
    # all words at the very end -> mapper must still spread strictly increasing
    words = [{"text": "la", "start": 1.95, "end": 1.99, "probability": 0.5}]
    lines = [
        {"text": "a", "source_line": 1},
        {"text": "b", "source_line": 2},
        {"text": "c", "source_line": 3},
    ]
    entries = proportional_entries(words, lines, duration=2.0)
    starts = [entry["start_seconds"] for entry in entries]
    assert starts[0] < starts[1] < starts[2] < 2.0


def test_proportional_entries_rejects_nonpositive_duration():
    with pytest.raises(LyricAlignmentError, match="duration must be positive"):
        proportional_entries([], [{"text": "x", "source_line": 1}], duration=0.0)
