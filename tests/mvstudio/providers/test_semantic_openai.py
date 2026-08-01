import json
import io
import urllib.error

import pytest

from mvstudio.director.drafting import ModelBudget, ModelTask
from mvstudio.providers.semantic_openai import (
    OpenAICompatibleSemanticPort,
    SemanticProviderError,
    SemanticResponseError,
)


def _task(max_output_bytes=4096):
    return ModelTask(
        event_type="lyrics.semantic_segment.requested",
        model="fixture-model",
        budget=ModelBudget(max_input_bytes=4096, max_output_bytes=max_output_bytes, max_tokens=200),
        reason="fixture",
        input_contract_hash="sha256:" + "a" * 64,
        output_schema_hash="sha256:" + "b" * 64,
        output_schema={"groups": [{"id": "text", "line_ids": ["line_id"]}]},
        payload={"lines": [{"id": "line_001", "text": "hello"}]},
    )


class Response:
    def __init__(self, value):
        self.value = io.BytesIO(value)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def readline(self):
        return self.value.readline()


def _stream(envelope):
    chunks = []
    for choice in envelope.get("choices", []):
        chunks.append({
            "choices": [{
                "delta": choice.get("message", {}),
                "finish_reason": choice.get("finish_reason"),
            }],
            "usage": envelope.get("usage", {}),
        })
    if not chunks:
        chunks.append({"choices": [], "usage": envelope.get("usage", {})})
    return (
        "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
        + "data: [DONE]\n\n"
    ).encode()


def test_provider_builds_fixed_json_request_and_returns_usage(monkeypatch):
    captured = {}
    envelope = {
        "choices": [{"message": {"content": json.dumps({"groups": []})}}],
        "usage": {"prompt_tokens": 31, "completion_tokens": 12},
    }

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response(_stream(envelope))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret", timeout_seconds=12)
    result = port.run(_task())
    request_body = json.loads(captured["request"].data)
    assert captured["request"].full_url == "https://models.example/v1/chat/completions"
    assert captured["request"].headers["Authorization"] == "Bearer secret"
    assert request_body["model"] == "fixture-model"
    assert request_body["response_format"] == {"type": "json_object"}
    assert request_body["max_tokens"] == 200
    assert request_body["stream"] is True
    assert request_body["stream_options"] == {"include_usage": True}
    assert "file paths" in request_body["messages"][0]["content"]
    user_contract = json.loads(request_body["messages"][1]["content"])
    assert user_contract["output_schema"] == {
        "groups": [{"id": "text", "line_ids": ["line_id"]}]
    }
    assert user_contract["output_schema_hash"] == "sha256:" + "b" * 64
    assert result.output == {"groups": []}
    assert (result.input_tokens, result.output_tokens) == (31, 12)
    assert captured["timeout"] == 12


def test_provider_default_timeout_allows_slow_reasoning_models():
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret")
    assert port.timeout_seconds == 180


@pytest.mark.parametrize(
    "url",
    [
        "http://models.example/v1",
        "https://user:pass@models.example/v1",
        "https://models.example/v1?token=secret",
        "file:///tmp/model",
    ],
)
def test_provider_rejects_unsafe_base_urls(url):
    with pytest.raises(SemanticProviderError):
        OpenAICompatibleSemanticPort(url, "secret")


def test_provider_allows_loopback_http():
    port = OpenAICompatibleSemanticPort("http://127.0.0.1:8000/v1", "local")
    assert port.endpoint == "http://127.0.0.1:8000/v1/chat/completions"


def test_provider_redacts_transport_and_response_errors(monkeypatch):
    def fail(*_args, **_kwargs):
        raise urllib.error.URLError("/private/secret")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret")
    with pytest.raises(SemanticProviderError) as error:
        port.run(_task())
    assert "/private/secret" not in str(error.value)


def test_provider_rejects_non_json_model_content(monkeypatch):
    envelope = {"choices": [{"message": {"content": "not-json"}}], "usage": {}}
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret")
    with pytest.raises(SemanticProviderError, match="invalid response"):
        port.run(_task())


def test_provider_accepts_fenced_json_model_content(monkeypatch):
    envelope = {
        "choices": [{"message": {"content": "```json\n{\"groups\": []}\n```"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    result = OpenAICompatibleSemanticPort("https://models.example/v1", "secret").run(_task())
    assert result.output == {"groups": []}


def test_provider_accepts_reasoning_content_when_content_is_empty(monkeypatch):
    envelope = {
        "choices": [{"message": {"content": "", "reasoning_content": "{\"groups\": []}"}}],
        "usage": {},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    result = OpenAICompatibleSemanticPort("https://models.example/v1", "secret").run(_task())
    assert result.output == {"groups": []}


def test_provider_accumulates_stream_chunks_and_final_usage(monkeypatch):
    chunks = [
        {"choices": [{"delta": {"content": '{"groups":'}, "finish_reason": None}]},
        {"choices": [{"delta": {"content": " []}"}, "finish_reason": "stop"}]},
        {
            "choices": [],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 12,
                "prompt_tokens_details": {"cached_tokens": 20},
            },
        },
    ]
    payload = (
        "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
        + "data: [DONE]\n\n"
    ).encode()
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(payload)
    )
    result = OpenAICompatibleSemanticPort(
        "https://models.example/v1", "secret"
    ).run(_task())
    assert result.output == {"groups": []}
    assert (result.input_tokens, result.cache_read_tokens, result.output_tokens) == (
        100, 20, 12,
    )


def test_provider_rejects_non_stream_response(monkeypatch):
    envelope = {
        "choices": [{"message": {"content": '{"groups": []}'}}],
        "usage": {},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: Response(json.dumps(envelope).encode()),
    )
    with pytest.raises(SemanticProviderError, match="non-stream"):
        OpenAICompatibleSemanticPort("https://models.example/v1", "secret").run(_task())


def test_provider_does_not_charge_sse_framing_to_generated_byte_budget(monkeypatch):
    envelope = {
        "choices": [{"message": {"content": '{"groups": []}'}}],
        "usage": {},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    result = OpenAICompatibleSemanticPort(
        "https://models.example/v1", "secret"
    ).run(_task(max_output_bytes=40))
    assert result.output == {"groups": []}


def test_provider_still_enforces_generated_byte_budget(monkeypatch):
    envelope = {
        "choices": [{"message": {"content": '{"groups": ["' + "x" * 80 + '"]}'}}],
        "usage": {},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    with pytest.raises(SemanticProviderError, match="response exceeds"):
        OpenAICompatibleSemanticPort(
            "https://models.example/v1", "secret"
        ).run(_task(max_output_bytes=40))


def test_provider_surfaces_truncation_with_billable_usage(monkeypatch):
    envelope = {
        "choices": [{
            "finish_reason": "length",
            "message": {"content": '{"groups":[{"id":"unfinished'},
        }],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 75,
            "prompt_tokens_details": {"cached_tokens": 20},
        },
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    with pytest.raises(SemanticResponseError, match="truncated") as error:
        OpenAICompatibleSemanticPort("https://models.example/v1", "secret").run(_task())
    assert error.value.finish_reason == "length"
    assert (error.value.input_tokens, error.value.cache_read_tokens, error.value.output_tokens) == (
        100, 20, 75,
    )


def test_provider_surfaces_invalid_json_with_billable_usage(monkeypatch):
    envelope = {
        "choices": [{"finish_reason": "stop", "message": {"content": "{broken"}}],
        "usage": {"prompt_tokens": 31, "completion_tokens": 12},
    }
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(_stream(envelope))
    )
    with pytest.raises(SemanticResponseError, match="invalid response JSON") as error:
        OpenAICompatibleSemanticPort("https://models.example/v1", "secret").run(_task())
    assert (error.value.input_tokens, error.value.output_tokens) == (31, 12)
