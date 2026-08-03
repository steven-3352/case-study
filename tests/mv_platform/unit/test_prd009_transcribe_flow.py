"""PRD-009 audio-first flow: audio-only intake -> remote transcription via LLM_*.

End-to-end within the application layer (no network): an audio-only project is
created, the workflow marks lyrics missing, and transcribe_audio_for_project
resolves the shared LLM_* gateway and writes an LRC transcript.
"""

import pytest

from mv_platform.application import ApplicationBlocked, ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure import Database


def make_service(tmp_path):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(settings, database, workspace_root=tmp_path)
    service.initialize()
    return service


def _audio_only_project(service, tmp_path):
    project = service.create_project("audio-first", {"x": 1})
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"RIFF....WAVEfake-pcm-payload")
    service.import_project_asset(project.project_id, audio, "song.wav")
    return project


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_audio_only_transcribes_via_llm_gateway(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    project = _audio_only_project(service, tmp_path)

    # User config: only the shared LLM gateway is set (no local Whisper, no WHISPER_*).
    monkeypatch.setenv("LLM_BASE_URL", "https://gateway.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-user-llm")
    monkeypatch.delenv("WHISPER_BASE_URL", raising=False)
    monkeypatch.delenv("WHISPER_API_KEY", raising=False)
    monkeypatch.delenv("MVSTUDIO_WHISPER_MODEL", raising=False)

    captured = {}

    def fake_post(self, url, headers=None, data=None, files=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["model"] = data.get("model")
        return _FakeResponse({
            "language": "zh",
            "duration": 6.0,
            "words": [
                {"word": "月", "start": 0.20, "end": 0.45},
                {"word": "光", "start": 0.45, "end": 0.80},
                # >0.5 s pause -> forces a new LRC line
                {"word": "洒", "start": 2.10, "end": 2.35},
                {"word": "下", "start": 2.35, "end": 2.70},
            ],
        })

    monkeypatch.setattr("requests.Session.post", fake_post)

    result = service.transcribe_audio_for_project(project.project_id)

    # Routed to the user's LLM gateway, using the standard audio endpoint + bearer.
    assert captured["url"] == "https://gateway.test/v1/audio/transcriptions"
    assert captured["headers"]["Authorization"] == "Bearer sk-user-llm"
    assert captured["model"] == "whisper-1"

    assert result["lrc_file"] == "inputs/lyrics/transcript.lrc"
    assert result["line_count"] == 2

    lrc = (tmp_path / "projects" / "audio-first" / "inputs" / "lyrics" / "transcript.lrc").read_text(
        encoding="utf-8"
    )
    lines = lrc.splitlines()
    assert lines[0].startswith("[00:00.20]") and lines[0].endswith("月光")
    assert lines[1].startswith("[00:02.10]") and lines[1].endswith("洒下")


def test_workflow_marks_lyrics_missing_then_present_after_transcription(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    project = _audio_only_project(service, tmp_path)

    # Before transcription: music stage flags lyrics as missing.
    workflow = service.get_project_workflow(project.project_id)
    music = next(s for s in workflow["stages"] if s["id"] == "music")
    assert music["data"]["has_lyrics"] is False

    monkeypatch.setenv("LLM_BASE_URL", "https://gateway.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-user-llm")

    def fake_post(self, url, headers=None, data=None, files=None, timeout=None):
        return _FakeResponse({
            "language": "zh", "duration": 3.0,
            "words": [{"word": "你", "start": 0.1, "end": 0.4},
                      {"word": "好", "start": 0.4, "end": 0.8}],
        })

    monkeypatch.setattr("requests.Session.post", fake_post)
    service.transcribe_audio_for_project(project.project_id)

    # After transcription: an LRC now exists under inputs/lyrics/.
    assert (tmp_path / "projects" / "audio-first" / "inputs" / "lyrics" / "transcript.lrc").is_file()


def test_no_gateway_and_no_local_model_blocks_with_guidance(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    project = _audio_only_project(service, tmp_path)

    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("WHISPER_BASE_URL", raising=False)
    monkeypatch.delenv("MVSTUDIO_WHISPER_MODEL", raising=False)

    with pytest.raises(ApplicationBlocked) as excinfo:
        service.transcribe_audio_for_project(project.project_id)
    assert "LLM_BASE_URL" in str(excinfo.value)
