"""Bounded Seedance 2.0 video-generation provider."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class SeedanceProviderError(RuntimeError):
    pass


def _digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _media_url(value, label, allow_query):
    if not isinstance(value, str) or not value:
        raise SeedanceProviderError(label + " URL is invalid")
    parsed = urllib.parse.urlparse(value)
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    schemes = {"http", "https"} if loopback else {"https"}
    if parsed.scheme not in schemes or not parsed.netloc:
        raise SeedanceProviderError(label + " URL must use HTTPS or loopback HTTP")
    if parsed.username or parsed.password or parsed.fragment or (parsed.query and not allow_query):
        raise SeedanceProviderError(label + " URL is invalid")
    return parsed


def _image_type(value):
    if value.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if value.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    raise SeedanceProviderError("Seedance frame must be PNG or JPEG")


@dataclass(frozen=True)
class SeedanceFrame:
    content: bytes
    sha256: str

    def checked(self, max_bytes):
        if not isinstance(self.content, bytes) or not self.content:
            raise SeedanceProviderError("Seedance frame bytes are required")
        if len(self.content) > max_bytes:
            raise SeedanceProviderError("Seedance frame exceeds byte budget")
        if self.sha256 != _digest(self.content):
            raise SeedanceProviderError("Seedance frame hash changed")
        return _image_type(self.content)


@dataclass(frozen=True)
class SeedanceTask:
    shot_id: str
    model: str
    prompt: str
    duration_seconds: int
    first_frame: SeedanceFrame
    reference_frames: tuple[SeedanceFrame, ...] = ()
    aspect_ratio: str = "9:16"
    resolution: str = "720p"


@dataclass(frozen=True)
class SeedanceResult:
    video_bytes: bytes
    video_sha256: str
    provider: str
    model: str
    task_id: str | None
    request_contract_sha256: str
    first_frame_sha256: str
    reference_frame_sha256s: tuple[str, ...]


class SeedancePort:
    provider = "seedance-openai-compatible"

    def __init__(
        self,
        base_url,
        api_key,
        model,
        timeout_seconds=120,
        poll_interval_seconds=5,
        max_poll_attempts=120,
        max_prompt_bytes=12000,
        max_frame_bytes=20 * 1024 * 1024,
        max_response_bytes=1024 * 1024,
        max_video_bytes=200 * 1024 * 1024,
        opener=None,
        sleeper=None,
    ):
        parsed = _media_url(base_url, "Seedance provider", allow_query=False)
        if not isinstance(api_key, str) or not api_key:
            raise SeedanceProviderError("Seedance provider configuration is incomplete")
        if not isinstance(model, str) or not model.strip():
            raise SeedanceProviderError("Seedance model is required")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise SeedanceProviderError("Seedance timeout is invalid")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise SeedanceProviderError("Seedance timeout is invalid")
        if not isinstance(max_poll_attempts, int) or isinstance(max_poll_attempts, bool):
            raise SeedanceProviderError("Seedance polling budget is invalid")
        if max_poll_attempts <= 0 or max_poll_attempts > 240:
            raise SeedanceProviderError("Seedance polling budget is invalid")
        base = base_url.rstrip("/")
        self.api_base = base if parsed.path.rstrip("/").endswith("/v1") else base + "/v1"
        self.endpoint = self.api_base + "/video/generations"
        self.api_key = api_key
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)
        self.poll_interval_seconds = float(poll_interval_seconds)
        self.max_poll_attempts = max_poll_attempts
        self.max_prompt_bytes = int(max_prompt_bytes)
        self.max_frame_bytes = int(max_frame_bytes)
        self.max_response_bytes = int(max_response_bytes)
        self.max_video_bytes = int(max_video_bytes)
        self._opener = opener or urllib.request.urlopen
        self._sleep = sleeper or time.sleep

    @classmethod
    def from_env(cls, environ=None, **kwargs):
        env = os.environ if environ is None else environ
        return cls(
            env.get("SEEDANCE_BASE_URL", ""),
            env.get("SEEDANCE_API_KEY", ""),
            env.get("SEEDANCE_MODEL", ""),
            **kwargs,
        )

    def _checked_contract(self, task):
        if not isinstance(task, SeedanceTask):
            raise SeedanceProviderError("Seedance provider requires SeedanceTask")
        if not isinstance(task.shot_id, str) or not task.shot_id.strip():
            raise SeedanceProviderError("Seedance shot_id is required")
        if task.model != self.model:
            raise SeedanceProviderError("Seedance task model differs from configured model")
        if not isinstance(task.prompt, str) or not task.prompt.strip():
            raise SeedanceProviderError("Seedance prompt is required")
        if len(task.prompt.encode("utf-8")) > self.max_prompt_bytes:
            raise SeedanceProviderError("Seedance prompt exceeds byte budget")
        if isinstance(task.duration_seconds, bool) or not isinstance(task.duration_seconds, int):
            raise SeedanceProviderError("Seedance duration is invalid")
        if not 4 <= task.duration_seconds <= 15:
            raise SeedanceProviderError("Seedance duration must be between 4 and 15 seconds")
        if task.aspect_ratio != "9:16" or task.resolution != "720p":
            raise SeedanceProviderError("Seedance first slice requires 9:16 at 720p")
        if len(task.reference_frames) > 4:
            raise SeedanceProviderError("Seedance reference-frame count exceeds budget")
        first_type = task.first_frame.checked(self.max_frame_bytes)
        reference_types = [frame.checked(self.max_frame_bytes) for frame in task.reference_frames]
        contract = {
            "shot_id": task.shot_id.strip(),
            "model": task.model,
            "prompt": task.prompt.strip(),
            "duration": task.duration_seconds,
            "aspect_ratio": task.aspect_ratio,
            "resolution": task.resolution,
            "first_frame_sha256": task.first_frame.sha256,
            "reference_frame_sha256s": [frame.sha256 for frame in task.reference_frames],
        }
        return contract, first_type, reference_types

    @staticmethod
    def _data_url(frame, media_type):
        return "data:" + media_type + ";base64," + base64.b64encode(frame.content).decode("ascii")

    def _json_request(self, url, method="GET", body=None):
        headers = {"Authorization": "Bearer " + self.api_key}
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise SeedanceProviderError("Seedance provider request failed") from exc
        if len(raw) > self.max_response_bytes:
            raise SeedanceProviderError("Seedance provider response exceeds byte budget")
        try:
            value = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SeedanceProviderError("Seedance provider returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise SeedanceProviderError("Seedance provider returned an invalid envelope")
        return value

    @staticmethod
    def _video_url(envelope):
        candidates = []
        if isinstance(envelope.get("video"), dict):
            candidates.append(envelope["video"].get("url"))
        candidates.extend(envelope.get(key) for key in ("video_url", "url", "output_url", "result_url"))
        if isinstance(envelope.get("data"), list) and envelope["data"]:
            item = envelope["data"][0]
            if isinstance(item, dict):
                candidates.extend(item.get(key) for key in ("url", "video_url", "output_url"))
        if isinstance(envelope.get("output"), dict):
            candidates.extend(envelope["output"].get(key) for key in ("url", "video_url"))
        if isinstance(envelope.get("metadata"), dict):
            candidates.append(envelope["metadata"].get("url"))
        return next((item for item in candidates if isinstance(item, str) and item), None)

    @staticmethod
    def _task_id(envelope):
        return next(
            (
                envelope.get(key)
                for key in ("task_id", "job_id", "id", "request_id")
                if isinstance(envelope.get(key), str) and envelope.get(key)
            ),
            None,
        )

    def _poll(self, task_id):
        encoded = urllib.parse.quote(task_id, safe="")
        candidates = (
            self.endpoint + "/" + encoded,
            self.api_base + "/videos/" + encoded,
            self.api_base + "/tasks/" + encoded,
        )
        for _attempt in range(self.max_poll_attempts):
            for url in candidates:
                try:
                    envelope = self._json_request(url)
                except SeedanceProviderError:
                    continue
                video_url = self._video_url(envelope)
                if video_url:
                    return video_url
                if str(envelope.get("status", "")).lower() in {"failed", "error", "cancelled"}:
                    raise SeedanceProviderError("Seedance provider task failed")
            self._sleep(self.poll_interval_seconds)
        raise SeedanceProviderError("Seedance provider polling timed out")

    def _download(self, url):
        _media_url(url, "Seedance output", allow_query=True)
        request = urllib.request.Request(url, headers={"Accept": "video/mp4"}, method="GET")
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_video_bytes + 1)
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise SeedanceProviderError("Seedance video download failed") from exc
        if not raw or len(raw) > self.max_video_bytes:
            raise SeedanceProviderError("Seedance video violates byte budget")
        if len(raw) < 12 or raw[4:8] != b"ftyp":
            raise SeedanceProviderError("Seedance output is not MP4")
        return raw

    def generate(self, task):
        contract, first_type, reference_types = self._checked_contract(task)
        body = {
            "model": task.model,
            "prompt": contract["prompt"],
            "image": self._data_url(task.first_frame, first_type),
            "metadata": {
                "duration": task.duration_seconds,
                "ratio": task.aspect_ratio,
                "generate_audio": False,
                "watermark": False,
                "resolution": task.resolution,
            },
        }
        if task.reference_frames:
            body["reference_images"] = [
                {"url": self._data_url(frame, media_type)}
                for frame, media_type in zip(task.reference_frames, reference_types)
            ]
        envelope = self._json_request(self.endpoint, method="POST", body=body)
        task_id = self._task_id(envelope)
        video_url = self._video_url(envelope)
        if not video_url:
            if not task_id:
                raise SeedanceProviderError("Seedance response lacks video URL and task ID")
            video_url = self._poll(task_id)
        video = self._download(video_url)
        contract_bytes = json.dumps(
            contract, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return SeedanceResult(
            video_bytes=video,
            video_sha256=_digest(video),
            provider=self.provider,
            model=task.model,
            task_id=task_id,
            request_contract_sha256=_digest(contract_bytes),
            first_frame_sha256=task.first_frame.sha256,
            reference_frame_sha256s=tuple(frame.sha256 for frame in task.reference_frames),
        )
