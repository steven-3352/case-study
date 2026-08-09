import json
import urllib.error

import pytest

from mvstudio.providers.seedance import (
    SeedanceFrame,
    SeedancePort,
    SeedanceProviderError,
    SeedanceTask,
    _digest,
)


PNG = b"\x89PNG\r\n\x1a\nfixture"
MP4 = b"\x00\x00\x00\x18ftypisomfixture-video"


class Response:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit):
        return self.value[:limit]


def _task(**values):
    defaults = {
        "shot_id": "shot-001",
        "model": "doubao-seedance-2-0",
        "prompt": "Intent: completion_rate. The sleeve lifts as the camera pushes forward.",
        "duration_seconds": 5,
        "first_frame": SeedanceFrame(PNG, _digest(PNG)),
    }
    defaults.update(values)
    return SeedanceTask(**defaults)


def test_sync_generation_sends_fixed_contract_and_returns_mp4_evidence():
    captured = []

    def opener(request, timeout):
        captured.append((request, timeout))
        if request.full_url == "https://seedance.example/v1/video/generations":
            return Response(json.dumps({"video": {"url": "https://cdn.example/clip.mp4"}}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    result = port.generate(_task())
    request, timeout = captured[0]
    body = json.loads(request.data)
    assert request.full_url == "https://seedance.example/v1/video/generations"
    assert request.headers["Authorization"] == "Bearer secret"
    assert body["model"] == "doubao-seedance-2-0"
    assert body["metadata"] == {
        "duration": 5,
        "ratio": "9:16",
        "generate_audio": False,
        "watermark": False,
        "resolution": "720p",
    }
    assert "duration" not in body
    assert "aspect_ratio" not in body
    assert "resolution" not in body
    assert body["image"].startswith("data:image/png;base64,")
    assert result.video_bytes == MP4
    assert result.video_sha256 == _digest(MP4)
    assert result.first_frame_sha256 == _digest(PNG)
    assert result.provider == "seedance-openai-compatible"
    assert timeout == 120


def test_async_generation_polls_bounded_endpoints():
    seen = []

    def opener(request, timeout):
        seen.append(request.full_url)
        if request.method == "POST":
            return Response(json.dumps({"task_id": "task/1"}).encode())
        if request.full_url.endswith("task%2F1"):
            return Response(json.dumps({"status": "done", "video_url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example/v1", "secret", "doubao-seedance-2-0",
        opener=opener, sleeper=lambda _seconds: None, max_poll_attempts=2,
    )
    result = port.generate(_task())
    assert result.task_id == "task/1"
    assert any(url.endswith("task%2F1") for url in seen)


def test_reference_frames_are_hash_checked_and_bounded():
    reference = SeedanceFrame(PNG + b"2", _digest(PNG + b"2"))
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return Response(json.dumps({"url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    result = port.generate(_task(reference_frames=(reference,)))
    assert len(captured["reference_images"]) == 1
    assert result.reference_frame_sha256s == (reference.sha256,)


@pytest.mark.parametrize(
    "url",
    [
        "http://seedance.example",
        "https://user:pass@seedance.example",
        "https://seedance.example?token=secret",
        "file:///tmp/provider",
    ],
)
def test_provider_rejects_unsafe_base_url(url):
    with pytest.raises(SeedanceProviderError):
        SeedancePort(url, "secret", "doubao-seedance-2-0")


def test_provider_allows_loopback_http_and_v1_base():
    port = SeedancePort("http://127.0.0.1:8000/v1", "local", "model")
    assert port.endpoint == "http://127.0.0.1:8000/v1/video/generations"


@pytest.mark.parametrize(
    "task, message",
    [
        (_task(duration_seconds=3), "duration"),
        (_task(duration_seconds=16), "duration"),
        (_task(prompt="x" * 12001), "prompt"),
        (_task(aspect_ratio="1:1"), "unsupported"),
        (_task(model="other"), "model differs"),
        (_task(first_frame=SeedanceFrame(PNG, "sha256:" + "0" * 64)), "hash changed"),
        (_task(first_frame=SeedanceFrame(b"not-image", _digest(b"not-image"))), "PNG or JPEG"),
    ],
)
def test_task_contract_fails_closed_before_network(task, message):
    port = SeedancePort("https://seedance.example", "secret", "doubao-seedance-2-0")
    with pytest.raises(SeedanceProviderError, match=message):
        port.generate(task)


def test_provider_rejects_invalid_or_oversized_video():
    responses = iter((json.dumps({"url": "https://cdn.example/v.mp4"}).encode(), b"not-mp4"))
    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0",
        opener=lambda *_args, **_kwargs: Response(next(responses)),
    )
    with pytest.raises(SeedanceProviderError, match="not MP4"):
        port.generate(_task())


def test_provider_redacts_transport_error():
    def fail(*_args, **_kwargs):
        raise urllib.error.URLError("/private/path?token=secret")

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=fail
    )
    with pytest.raises(SeedanceProviderError) as error:
        port.generate(_task())
    assert "private" not in str(error.value)
    assert "secret" not in str(error.value)


def test_provider_does_not_require_or_write_files(monkeypatch):
    monkeypatch.setattr("pathlib.Path.open", lambda *_args, **_kwargs: pytest.fail("file access"))
    responses = iter((json.dumps({"url": "https://cdn.example/v.mp4"}).encode(), MP4))
    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0",
        opener=lambda *_args, **_kwargs: Response(next(responses)),
    )
    assert port.generate(_task()).video_bytes == MP4


def test_reference_video_appends_content_entry():
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return Response(json.dumps({"url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    task = _task(reference_video_url="https://example.com/dance.mp4")
    port.generate(task)
    assert "content" in captured["metadata"]
    entries = captured["metadata"]["content"]
    assert len(entries) == 1
    assert entries[0] == {"type": "video_url", "video_url": {"url": "https://example.com/dance.mp4"}, "role": "reference_video"}
    assert captured["image"].startswith("data:image/png;base64,")
    assert captured["metadata"]["generate_audio"] is False
    assert "duration" in captured["metadata"]


def test_reference_audio_enables_generate_audio():
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return Response(json.dumps({"url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    port.generate(_task(reference_audio_url="https://example.com/bg.mp3"))
    audio_entries = [e for e in captured["metadata"]["content"] if e["role"] == "reference_audio"]
    assert len(audio_entries) == 1
    assert captured["metadata"]["generate_audio"] is True


def test_reference_image_urls_all_appear_in_content():
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return Response(json.dumps({"url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    urls = ("https://example.com/frame1.jpg", "https://example.com/frame2.jpg")
    port.generate(_task(reference_image_urls=urls))
    image_entries = [e for e in captured["metadata"]["content"] if e["role"] == "reference_image"]
    assert len(image_entries) == 2
    assert image_entries[0]["image_url"]["url"] == urls[0]
    assert image_entries[1]["image_url"]["url"] == urls[1]


def test_reference_url_rejects_non_https():
    port = SeedancePort("https://seedance.example", "secret", "doubao-seedance-2-0")
    with pytest.raises(SeedanceProviderError, match="HTTPS"):
        port.generate(_task(reference_video_url="http://example.com/dance.mp4"))


def test_content_order_matches_curl_spec():
    """images first, then video, then audio — matches the tested curl."""
    captured = {}

    def opener(request, timeout):
        if request.method == "POST":
            captured.update(json.loads(request.data))
            return Response(json.dumps({"url": "https://cdn.example/v.mp4"}).encode())
        return Response(MP4)

    port = SeedancePort(
        "https://seedance.example", "secret", "doubao-seedance-2-0", opener=opener
    )
    port.generate(_task(
        reference_image_urls=("https://example.com/img.jpg",),
        reference_video_url="https://example.com/vid.mp4",
        reference_audio_url="https://example.com/aud.mp3",
    ))
    roles = [e["role"] for e in captured["metadata"]["content"]]
    assert roles == ["reference_image", "reference_video", "reference_audio"]
