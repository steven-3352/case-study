"""OpenAI-compatible remote transcription provider (Whisper endpoint).

Reuses the already-configured OpenAI-compatible gateway so audio-first projects
do not require a separate local Whisper model download.  Resolution honours the
user-configured gateway first: a dedicated ``WHISPER_*`` gateway when present,
otherwise the shared ``LLM_*`` gateway credentials.  The returned object is
shape-compatible with :class:`mvstudio.providers.alignment_faster_whisper.TranscribeResult`
so :meth:`ApplicationService.transcribe_audio_for_project` can consume either
provider interchangeably.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from mvstudio.providers.alignment_faster_whisper import TranscribeResult


class TranscriptionProviderError(RuntimeError):
    pass


class OpenAICompatibleTranscriptionPort:
    provider = "openai-compatible-remote"

    def __init__(self, base_url, api_key, model="whisper-1", timeout_seconds=300,
                 session=None):
        if not isinstance(base_url, str) or not isinstance(api_key, str) or not api_key:
            raise TranscriptionProviderError("transcription provider configuration is incomplete")
        parsed = urlparse(base_url)
        loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if parsed.scheme not in ({"http", "https"} if loopback else {"https"}):
            raise TranscriptionProviderError("transcription provider URL must use HTTPS or loopback HTTP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.netloc:
            raise TranscriptionProviderError("transcription provider URL is invalid")
        if not isinstance(model, str) or not model.strip():
            raise TranscriptionProviderError("transcription provider model is missing")
        base = base_url.rstrip("/")
        self.endpoint = base + (
            "/audio/transcriptions" if parsed.path.rstrip("/").endswith("/v1")
            else "/v1/audio/transcriptions"
        )
        self.api_key = api_key
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls, environ):
        # User-config priority: reuse the shared LLM gateway credentials by
        # default; a dedicated WHISPER_* gateway is only used when explicitly set.
        base_url = environ.get("LLM_BASE_URL") or environ.get("WHISPER_BASE_URL", "")
        api_key = environ.get("LLM_API_KEY") or environ.get("WHISPER_API_KEY", "")
        model = environ.get("WHISPER_MODEL", "") or "whisper-1"
        return cls(base_url, api_key, model)

    def transcribe(self, audio_path, language="zh"):
        """Transcribe audio via the remote /v1/audio/transcriptions endpoint.

        Requests ``verbose_json`` with word-level timestamps and normalizes the
        response into a :class:`TranscribeResult`.  Falls back to segment-level
        timestamps, then to a single whole-file segment, when the gateway does
        not return word granularity.  Applies the same >8.0 words/second
        hallucination gate as the local provider (§4.2.1).
        """
        audio_path = Path(audio_path)
        data = {
            "model": self.model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }
        if language:
            data["language"] = language
        try:
            with audio_path.open("rb") as handle:
                response = self.session.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                    files={"file": (audio_path.name, handle, "application/octet-stream")},
                    timeout=self.timeout_seconds,
                )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise TranscriptionProviderError(f"remote transcription failed: {exc}") from exc

        segments = self._normalize_segments(payload)
        if not segments:
            raise TranscriptionProviderError("remote transcription returned no speech segments")
        detected_language = payload.get("language") or (language or "")
        duration_s = float(payload.get("duration") or segments[-1]["end"] or 0.0)
        hallucination_risk = bool(duration_s > 0.0 and len(segments) / duration_s > 8.0)
        return TranscribeResult(
            segments=segments,
            detected_language=detected_language,
            hallucination_risk=hallucination_risk,
        )

    @staticmethod
    def _normalize_segments(payload):
        words = payload.get("words")
        if isinstance(words, list) and words:
            return [
                {
                    "text": str(word.get("word", word.get("text", ""))),
                    "start": float(word.get("start", 0.0)),
                    "end": float(word.get("end", word.get("start", 0.0))),
                    "probability": float(word.get("probability", 1.0)),
                }
                for word in words
                if word.get("start") is not None
            ]
        chunks = payload.get("segments")
        if isinstance(chunks, list) and chunks:
            return [
                {
                    "text": str(chunk.get("text", "")).strip(),
                    "start": float(chunk.get("start", 0.0)),
                    "end": float(chunk.get("end", chunk.get("start", 0.0))),
                    "probability": 1.0,
                }
                for chunk in chunks
                if chunk.get("start") is not None
            ]
        text = str(payload.get("text", "")).strip()
        if text:
            return [{"text": text, "start": 0.0, "end": 0.0, "probability": 1.0}]
        return []
