"""OpenAI-compatible implementation of the bounded semantic model port."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping

from mvstudio.director.drafting import ModelResult, ModelTask


class SemanticProviderError(RuntimeError):
    pass


class OpenAICompatibleSemanticPort:
    def __init__(self, base_url, api_key, timeout_seconds=60):
        if not isinstance(base_url, str) or not isinstance(api_key, str) or not api_key:
            raise SemanticProviderError("semantic provider configuration is incomplete")
        parsed = urllib.parse.urlparse(base_url)
        loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if parsed.scheme not in ({"http", "https"} if loopback else {"https"}):
            raise SemanticProviderError("semantic provider URL must use HTTPS or loopback HTTP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.netloc:
            raise SemanticProviderError("semantic provider URL is invalid")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise SemanticProviderError("semantic provider timeout is invalid")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise SemanticProviderError("semantic provider timeout is invalid")
        base = base_url.rstrip("/")
        self.endpoint = base + ("/chat/completions" if parsed.path.rstrip("/").endswith("/v1") else "/v1/chat/completions")
        self.api_key = api_key
        self.timeout_seconds = float(timeout_seconds)

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        return cls(env.get("LLM_BASE_URL", ""), env.get("LLM_API_KEY", ""))

    def run(self, task: ModelTask) -> ModelResult:
        if not isinstance(task, ModelTask):
            raise SemanticProviderError("semantic provider requires a bounded ModelTask")
        instruction = (
            "Return one JSON object only. Follow the requested event contract exactly; "
            "do not add fields, timestamps, file paths, markdown, or commentary."
        )
        body = {
            "model": task.model,
            "messages": [
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "event_type": task.event_type,
                            "reason": task.reason,
                            "output_schema_hash": task.output_schema_hash,
                            "output_schema": task.output_schema,
                            "payload": task.payload,
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": task.budget.max_tokens,
            "temperature": 0,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(task.budget.max_output_bytes + 1)
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise SemanticProviderError("semantic provider request failed") from exc
        if len(raw) > task.budget.max_output_bytes:
            raise SemanticProviderError("semantic provider response exceeds byte budget")
        try:
            envelope = json.loads(raw)
            content = envelope["choices"][0]["message"]["content"]
            output = json.loads(content)
            usage = envelope.get("usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SemanticProviderError("semantic provider returned an invalid response") from exc
        if not isinstance(output, Mapping):
            raise SemanticProviderError("semantic provider output must be a JSON object")
        return ModelResult(output, input_tokens, output_tokens)
