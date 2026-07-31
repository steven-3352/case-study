import json
import urllib.error

import pytest

from mvstudio.director.drafting import ModelBudget, ModelTask
from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort, SemanticProviderError


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
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, limit):
        return self.value[:limit]


def test_provider_builds_fixed_json_request_and_returns_usage(monkeypatch):
    captured = {}
    envelope = {
        "choices": [{"message": {"content": json.dumps({"groups": []})}}],
        "usage": {"prompt_tokens": 31, "completion_tokens": 12},
    }

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response(json.dumps(envelope).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret", timeout_seconds=12)
    result = port.run(_task())
    request_body = json.loads(captured["request"].data)
    assert captured["request"].full_url == "https://models.example/v1/chat/completions"
    assert captured["request"].headers["Authorization"] == "Bearer secret"
    assert request_body["model"] == "fixture-model"
    assert request_body["response_format"] == {"type": "json_object"}
    assert request_body["max_tokens"] == 200
    assert "file paths" in request_body["messages"][0]["content"]
    user_contract = json.loads(request_body["messages"][1]["content"])
    assert user_contract["output_schema"] == {
        "groups": [{"id": "text", "line_ids": ["line_id"]}]
    }
    assert user_contract["output_schema_hash"] == "sha256:" + "b" * 64
    assert result.output == {"groups": []}
    assert (result.input_tokens, result.output_tokens) == (31, 12)
    assert captured["timeout"] == 12


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
        "urllib.request.urlopen", lambda *_args, **_kwargs: Response(json.dumps(envelope).encode())
    )
    port = OpenAICompatibleSemanticPort("https://models.example/v1", "secret")
    with pytest.raises(SemanticProviderError, match="invalid response"):
        port.run(_task())
