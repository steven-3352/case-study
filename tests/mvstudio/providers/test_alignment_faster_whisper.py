from types import SimpleNamespace

import pytest

from mvstudio.director.alignment import AlignmentTask, LyricAlignmentError
from mvstudio.providers.alignment_faster_whisper import FasterWhisperAlignmentPort


class FixtureWhisper:
    def __init__(self, words):
        self.words = words
        self.kwargs = None

    def transcribe(self, _path, **kwargs):
        self.kwargs = kwargs
        words = [
            SimpleNamespace(word=text, start=start, end=end, probability=probability)
            for text, start, end, probability in self.words
        ]
        return iter([SimpleNamespace(words=words)]), SimpleNamespace()


def _task(tmp_path):
    return AlignmentTask(
        audio_path=tmp_path / "song.wav",
        audio_digest="sha256:" + "a" * 64,
        duration_seconds=2.0,
        lines=(
            {"text": "First line", "source_line": 1},
            {"text": "Second line", "source_line": 2},
        ),
    )


def test_local_whisper_requires_exact_text_and_uses_word_timestamps(tmp_path):
    engine = FixtureWhisper([
        (" First", 0.1, 0.3, 0.95),
        (" line", 0.3, 0.6, 0.93),
        (" second", 0.9, 1.2, 0.91),
        (" line.", 1.2, 1.5, 0.89),
    ])
    port = FasterWhisperAlignmentPort("fixture", model_instance=engine)
    result = port.align(_task(tmp_path))

    assert [entry["start_seconds"] for entry in result.entries] == [0.1, 0.9]
    assert result.entries[1]["confidence"] == 0.89
    assert result.evidence["words"][0]["start"] == 0.1
    assert engine.kwargs["word_timestamps"] is True
    assert engine.kwargs["condition_on_previous_text"] is False


def test_local_whisper_rejects_transcript_drift(tmp_path):
    engine = FixtureWhisper([(" different", 0.1, 0.5, 0.9)])
    port = FasterWhisperAlignmentPort("fixture", model_instance=engine)
    with pytest.raises(LyricAlignmentError, match="exactly cover"):
        port.align(_task(tmp_path))


def test_local_whisper_rejects_line_boundary_without_word_evidence(tmp_path):
    task = AlignmentTask(
        audio_path=tmp_path / "song.wav",
        audio_digest="sha256:" + "a" * 64,
        duration_seconds=2.0,
        lines=({"text": "First", "source_line": 1}, {"text": "line", "source_line": 2}),
    )
    engine = FixtureWhisper([(" Firstline", 0.1, 0.8, 0.9)])
    port = FasterWhisperAlignmentPort("fixture", model_instance=engine)
    with pytest.raises(LyricAlignmentError, match="boundary lacks"):
        port.align(task)


def test_local_whisper_requires_explicit_model_configuration(tmp_path):
    with pytest.raises(LyricAlignmentError, match="MVSTUDIO_WHISPER_MODEL"):
        FasterWhisperAlignmentPort.from_env({})
    with pytest.raises(LyricAlignmentError, match="directory is missing"):
        FasterWhisperAlignmentPort.from_env(
            {"MVSTUDIO_WHISPER_MODEL": str(tmp_path / "missing")}
        )


def test_tolerant_port_maps_lyrics_despite_transcript_drift(tmp_path):
    # strict rejects, tolerant maps supplied lyrics onto Whisper word timing
    engine = FixtureWhisper([
        (" totally", 0.1, 0.4, 0.9),
        (" different", 0.5, 0.9, 0.8),
        (" words", 1.0, 1.4, 0.7),
    ])
    strict = FasterWhisperAlignmentPort("fixture", model_instance=engine)
    with pytest.raises(LyricAlignmentError, match="exactly cover"):
        strict.align(_task(tmp_path))

    tolerant = FasterWhisperAlignmentPort("fixture", model_instance=engine, tolerant=True)
    result = tolerant.align(_task(tmp_path))
    assert [entry["text"] for entry in result.entries] == ["First line", "Second line"]
    assert [entry["source_line"] for entry in result.entries] == [1, 2]
    starts = [entry["start_seconds"] for entry in result.entries]
    assert starts[0] < starts[1] < 2.0
    assert result.evidence["mode"] == "proportional_char_mapping"
    assert result.evidence["words"][0]["start"] == 0.1


def test_tolerant_flag_flows_through_from_env(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    port = FasterWhisperAlignmentPort.from_env(
        {"MVSTUDIO_WHISPER_MODEL": str(model_dir)}, tolerant=True
    )
    assert port.tolerant is True
    strict_default = FasterWhisperAlignmentPort.from_env(
        {"MVSTUDIO_WHISPER_MODEL": str(model_dir)}
    )
    assert strict_default.tolerant is False
