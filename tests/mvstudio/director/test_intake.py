import json
import wave

import pytest
from PIL import Image

from mvstudio.director.intake import IntakeContractError, inspect_intake, parse_lrc, validate_intake


def _write_wave(path, frames=800):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * frames)


def _inputs(tmp_path, lyrics="[00:00.00]first\n[00:00.05]second\n"):
    _write_wave(tmp_path / "inputs/audio/song.wav")
    lyric_path = tmp_path / "inputs/lyrics/song.lrc"
    lyric_path.parent.mkdir(parents=True)
    lyric_path.write_text(lyrics, encoding="utf-8")
    character = tmp_path / "inputs/characters/lead.png"
    character.parent.mkdir(parents=True)
    Image.new("RGBA", (12, 18), (20, 40, 60, 128)).save(character)
    return {
        "project_id": "project-a",
        "audio": "inputs/audio/song.wav",
        "lyrics": "inputs/lyrics/song.lrc",
        "characters": ["inputs/characters/lead.png"],
    }


def test_lrc_is_sorted_and_plain_lyrics_require_alignment(tmp_path):
    entries = parse_lrc("[00:02.5]later\n[00:01.25][00:01.50]earlier")
    assert [item["start_seconds"] for item in entries] == [1.25, 1.5, 2.5]
    assert entries[0]["end_seconds"] == 1.5
    assert entries[-1]["end_seconds"] is None

    value = _inputs(tmp_path, "line one\nline two\n")
    manifest = inspect_intake(value, tmp_path)
    assert manifest["lyrics"]["alignment_state"] == "alignment_required"
    assert not (tmp_path / "intake/lyrics_timed.json").exists()


def test_timed_intake_probes_without_altering_portrait(tmp_path):
    value = _inputs(tmp_path)
    portrait = tmp_path / value["characters"][0]
    original = portrait.read_bytes()
    manifest = inspect_intake(value, tmp_path)
    timed = json.loads((tmp_path / "intake/lyrics_timed.json").read_text())
    assert manifest["status"] == "intake_validated"
    assert manifest["audio"]["codec"] == "pcm_s16le"
    assert manifest["characters"][0]["format"] == "PNG"
    assert manifest["characters"][0]["has_alpha"] is True
    assert timed["entries"][1]["start_seconds"] == 0.05
    assert portrait.read_bytes() == original


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("audio", "/tmp/song.wav"),
        ("audio", "inputs/audio/../song.wav"),
        ("lyrics", "inputs/audio/song.lrc"),
        ("characters", ["inputs/characters\\lead.png"]),
    ],
)
def test_intake_rejects_unsafe_or_misclassified_paths(field, value):
    package = {
        "project_id": "project-a",
        "audio": "inputs/audio/song.wav",
        "lyrics": "inputs/lyrics/song.lrc",
        "characters": ["inputs/characters/lead.png"],
    }
    package[field] = value
    with pytest.raises(IntakeContractError):
        validate_intake(package)


def test_intake_rejects_symlink_even_when_target_is_inside_staging(tmp_path):
    value = _inputs(tmp_path)
    real = tmp_path / value["characters"][0]
    link = real.with_name("linked.png")
    link.symlink_to(real)
    value["characters"] = ["inputs/characters/linked.png"]
    with pytest.raises(IntakeContractError, match="symlink"):
        inspect_intake(value, tmp_path)


def test_intake_rejects_timed_lyrics_past_audio_duration(tmp_path):
    value = _inputs(tmp_path, "[00:02.00]too late\n")
    with pytest.raises(IntakeContractError, match="exceed audio duration"):
        inspect_intake(value, tmp_path)
