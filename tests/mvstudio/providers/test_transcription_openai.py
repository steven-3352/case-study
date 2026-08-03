import pytest

from mvstudio.providers.transcription_openai import (
    OpenAICompatibleTranscriptionPort,
    TranscriptionProviderError,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def post(self, url, headers=None, data=None, files=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "data": data, "timeout": timeout})
        return FakeResponse(self._payload)


def _audio(tmp_path):
    path = tmp_path / "song.mp3"
    path.write_bytes(b"\x00\x01\x02\x03")
    return path


def test_endpoint_normalization_and_bearer(tmp_path):
    session = FakeSession({"words": [{"word": "你好", "start": 0.0, "end": 0.5}], "duration": 1.0})
    port = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=session)
    port.transcribe(_audio(tmp_path))
    call = session.calls[0]
    assert call["url"] == "https://gw.test/v1/audio/transcriptions"
    assert call["headers"]["Authorization"] == "Bearer sk-x"
    assert call["data"]["model"] == "whisper-1"
    assert call["data"]["response_format"] == "verbose_json"


def test_word_level_segments_are_returned(tmp_path):
    payload = {
        "language": "zh",
        "duration": 3.0,
        "words": [
            {"word": "月", "start": 0.1, "end": 0.4},
            {"word": "光", "start": 0.4, "end": 0.8},
        ],
    }
    port = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=FakeSession(payload))
    result = port.transcribe(_audio(tmp_path))
    assert result.detected_language == "zh"
    assert result.hallucination_risk is False
    assert [s["text"] for s in result.segments] == ["月", "光"]
    assert result.segments[0]["start"] == pytest.approx(0.1)


def test_falls_back_to_segment_then_text(tmp_path):
    seg_payload = {"duration": 2.0, "segments": [{"text": " hello ", "start": 0.0, "end": 2.0}]}
    port = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=FakeSession(seg_payload))
    result = port.transcribe(_audio(tmp_path))
    assert result.segments[0]["text"] == "hello"

    txt_payload = {"text": "only text"}
    port2 = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=FakeSession(txt_payload))
    result2 = port2.transcribe(_audio(tmp_path))
    assert result2.segments[0]["text"] == "only text"


def test_hallucination_gate_flags_dense_words(tmp_path):
    payload = {
        "duration": 1.0,
        "words": [{"word": f"w{i}", "start": i * 0.01, "end": i * 0.01 + 0.005} for i in range(20)],
    }
    port = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=FakeSession(payload))
    result = port.transcribe(_audio(tmp_path))
    assert result.hallucination_risk is True


def test_empty_response_raises(tmp_path):
    port = OpenAICompatibleTranscriptionPort("https://gw.test/v1", "sk-x", session=FakeSession({"text": ""}))
    with pytest.raises(TranscriptionProviderError):
        port.transcribe(_audio(tmp_path))


def test_from_env_prefers_llm_gateway():
    # LLM_* is the primary transcription gateway.
    only_llm = OpenAICompatibleTranscriptionPort.from_env(
        {"LLM_BASE_URL": "https://llm.test/v1", "LLM_API_KEY": "sk-llm"}
    )
    assert only_llm.endpoint == "https://llm.test/v1/audio/transcriptions"

    # When both are set, LLM_* still wins; WHISPER_MODEL overrides the model name.
    both = OpenAICompatibleTranscriptionPort.from_env({
        "LLM_BASE_URL": "https://llm.test/v1", "LLM_API_KEY": "sk-llm",
        "WHISPER_BASE_URL": "https://w.test", "WHISPER_API_KEY": "sk-w",
        "WHISPER_MODEL": "whisper-large-v3",
    })
    assert both.endpoint == "https://llm.test/v1/audio/transcriptions"
    assert both.model == "whisper-large-v3"

    # WHISPER_* is used only as a fallback when no LLM gateway is configured.
    fallback = OpenAICompatibleTranscriptionPort.from_env(
        {"WHISPER_BASE_URL": "https://w.test", "WHISPER_API_KEY": "sk-w"}
    )
    assert fallback.endpoint == "https://w.test/v1/audio/transcriptions"


def test_incomplete_config_rejected():
    with pytest.raises(TranscriptionProviderError):
        OpenAICompatibleTranscriptionPort("https://gw.test/v1", "")
