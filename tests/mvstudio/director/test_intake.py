import json
import wave
import zipfile

import pytest
from PIL import Image

from mvstudio.director.intake import (
    IntakeContractError, inspect_intake, parse_lrc, parse_xlsx_director_sheet,
    validate_intake,
)


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


def _write_director_xlsx(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    strings = ["角色", "歌词", "起始时间", "结束时间", "锦礼", "第一句", "锦礼+安玥", "第二句"]
    shared = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + "".join(f"<si><t>{value}</t></si>" for value in strings) + "</sst>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheets><sheet name="导演表" sheetId="1"/></sheets></workbook>'
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
        '<c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c></row>'
        '<row r="2"><c r="A2" t="s"><v>4</v></c><c r="B2" t="s"><v>5</v></c>'
        '<c r="C2"><v>0</v></c><c r="D2"><v>0.04</v></c></row>'
        '<row r="3"><c r="A3" t="s"><v>6</v></c><c r="B3" t="s"><v>7</v></c>'
        '<c r="C3"><v>0.04</v></c><c r="D3"><v>0.08</v></c></row>'
        '</sheetData></worksheet>'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_lrc_is_sorted_and_plain_lyrics_require_alignment(tmp_path):
    entries = parse_lrc("[00:02.5]later\n[00:01.25][00:01.50]earlier")
    assert [item["start_seconds"] for item in entries] == [1.25, 1.5, 2.5]
    assert entries[0]["end_seconds"] == 1.5
    assert entries[-1]["end_seconds"] is None

    value = _inputs(tmp_path, "line one\nline two\n")
    manifest = inspect_intake(value, tmp_path)
    assert manifest["lyrics"]["alignment_state"] == "alignment_required"
    assert not (tmp_path / "intake/lyrics_timed.json").exists()
    plain = json.loads((tmp_path / "intake/lyrics_plain.json").read_text())
    assert plain["lines"] == [
        {"text": "line one", "source_line": 1},
        {"text": "line two", "source_line": 2},
    ]


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


def test_audio_only_intake_produces_partial_manifest(tmp_path):
    # Audio-first path (PRD-009 step-level self-healing): lyrics and characters
    # are supplied later. validate_intake must accept lyrics=None + empty
    # characters, and inspect_intake must emit a partial manifest without crashing.
    _write_wave(tmp_path / "inputs/audio/song.wav")
    value = {
        "project_id": "project-a",
        "audio": "inputs/audio/song.wav",
        "lyrics": None,
        "characters": [],
    }
    validated = validate_intake(value)
    assert validated["lyrics"] is None
    assert validated["characters"] == ()

    manifest = inspect_intake(value, tmp_path)
    assert manifest["status"] == "intake_validated"
    assert manifest["audio"]["codec"] == "pcm_s16le"
    assert manifest["lyrics"] is None
    assert manifest["characters"] == []
    # No lyrics sidecars should be written when lyrics are absent.
    assert not (tmp_path / "intake/lyrics_timed.json").exists()
    assert not (tmp_path / "intake/lyrics_plain.json").exists()


def test_intake_still_rejects_wrong_directory_lyrics_when_present(tmp_path):
    # Relaxing lyrics to optional must not weaken path validation when a lyrics
    # value IS provided.
    _write_wave(tmp_path / "inputs/audio/song.wav")
    value = {
        "project_id": "project-a",
        "audio": "inputs/audio/song.wav",
        "lyrics": "inputs/audio/song.lrc",
        "characters": [],
    }
    with pytest.raises(IntakeContractError):
        validate_intake(value)


def test_xlsx_preserves_binding_cast_end_times_and_source_rows(tmp_path):
    value = _inputs(tmp_path)
    xlsx = tmp_path / "inputs/lyrics/director.xlsx"
    _write_director_xlsx(xlsx)
    value["lyrics"] = "inputs/lyrics/director.xlsx"
    parsed = parse_xlsx_director_sheet(xlsx)
    assert parsed["director_contract"] == {
        "sheet_name": "导演表",
        "columns": ["角色", "歌词", "起始时间", "结束时间"],
        "entry_count": 2,
        "characters_are_binding": True,
    }
    assert parsed["timed_entries"][1]["character_names"] == ["锦礼", "安玥"]
    assert parsed["timed_entries"][1]["end_seconds"] == 0.08
    assert parsed["timed_entries"][1]["source_row"] == 3

    manifest = inspect_intake(value, tmp_path)
    timed = json.loads((tmp_path / "intake/lyrics_timed.json").read_text())
    assert manifest["lyrics"]["kind"] == "timed_spreadsheet"
    assert manifest["lyrics"]["alignment_state"] == "aligned_director_contract"
    assert timed["entries"] == parsed["timed_entries"]


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


@pytest.mark.parametrize("lyrics", ["", "[00:00.00]timed\nplain\n"])
def test_intake_rejects_empty_or_mixed_lyrics(tmp_path, lyrics):
    value = _inputs(tmp_path, lyrics)
    with pytest.raises(IntakeContractError, match="empty|mix"):
        inspect_intake(value, tmp_path)


def test_intake_rejects_symlink_staging_root(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    value = _inputs(real)
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(IntakeContractError, match="staging directory cannot be a symlink"):
        inspect_intake(value, linked)
