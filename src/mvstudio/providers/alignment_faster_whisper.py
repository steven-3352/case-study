"""Local Faster Whisper adapter for evidence-backed plain-lyric alignment."""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path

from mvstudio.director.alignment import (
    AlignmentResult,
    AlignmentTask,
    LyricAlignmentError,
)


def _normalized(value):
    return "".join(
        character.casefold()
        for character in unicodedata.normalize("NFKC", value)
        if character.isalnum()
    )


class FasterWhisperAlignmentPort:
    provider = "faster-whisper-local"

    def __init__(self, model, device="cpu", compute_type="int8", language=None, model_instance=None):
        if not isinstance(model, str) or not model.strip():
            raise LyricAlignmentError("local Whisper model path is required")
        self.model = model.strip()
        self.device = device
        self.compute_type = compute_type
        self.language = language or None
        self._model_instance = model_instance

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        model = env.get("MVSTUDIO_WHISPER_MODEL", "")
        if not model:
            raise LyricAlignmentError(
                "MVSTUDIO_WHISPER_MODEL must name an installed local model or model directory"
            )
        path = Path(model).expanduser()
        if path.is_absolute() and not path.is_dir():
            raise LyricAlignmentError("configured local Whisper model directory is missing")
        return cls(
            str(path) if path.is_absolute() else model,
            device=env.get("MVSTUDIO_WHISPER_DEVICE", "cpu"),
            compute_type=env.get("MVSTUDIO_WHISPER_COMPUTE_TYPE", "int8"),
            language=env.get("MVSTUDIO_WHISPER_LANGUAGE") or None,
        )

    def _engine(self):
        if self._model_instance is not None:
            return self._model_instance
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise LyricAlignmentError(
                "faster-whisper is required for local plain-lyric alignment"
            ) from exc
        self._model_instance = WhisperModel(
            self.model,
            device=self.device,
            compute_type=self.compute_type,
            local_files_only=True,
        )
        return self._model_instance

    def align(self, task):
        if not isinstance(task, AlignmentTask):
            raise LyricAlignmentError("local Whisper alignment requires AlignmentTask")
        try:
            segments, _info = self._engine().transcribe(
                str(task.audio_path),
                language=self.language,
                word_timestamps=True,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            words = [
                {
                    "text": word.word,
                    "start": float(word.start),
                    "end": float(word.end),
                    "probability": float(word.probability),
                }
                for segment in segments
                for word in (segment.words or [])
                if word.start is not None and word.end is not None and _normalized(word.word)
            ]
        except LyricAlignmentError:
            raise
        except Exception as exc:
            raise LyricAlignmentError("local Whisper transcription failed") from exc
        if not words:
            raise LyricAlignmentError("local Whisper returned no word timestamp evidence")
        transcript = "".join(_normalized(item["text"]) for item in words)
        expected = "".join(_normalized(item["text"]) for item in task.lines)
        if not expected or transcript != expected:
            raise LyricAlignmentError("transcript does not exactly cover the supplied lyrics")
        character_words = []
        for index, word in enumerate(words):
            character_words.extend([index] * len(_normalized(word["text"])))
        entries = []
        offset = 0
        previous_word = None
        for line in task.lines:
            normalized = _normalized(line["text"])
            if not normalized:
                raise LyricAlignmentError("plain lyric line has no alignable characters")
            word_index = character_words[offset]
            if previous_word == word_index:
                raise LyricAlignmentError("lyric line boundary lacks word timestamp evidence")
            covered = character_words[offset:offset + len(normalized)]
            confidence = min(words[index]["probability"] for index in set(covered))
            entries.append({
                "text": line["text"],
                "source_line": line["source_line"],
                "start_seconds": words[word_index]["start"],
                "confidence": max(0.0, min(1.0, confidence)),
            })
            previous_word = covered[-1]
            offset += len(normalized)
        evidence = {
            "audio_digest": task.audio_digest,
            "model": self.model,
            "words": words,
        }
        return AlignmentResult(
            entries=tuple(entries),
            provider=self.provider,
            model=self.model,
            evidence=evidence,
        )
