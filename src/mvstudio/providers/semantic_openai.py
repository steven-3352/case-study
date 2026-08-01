"""OpenAI-compatible implementation of the bounded semantic model port."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping

from mvstudio.director.drafting import ModelResult, ModelTask


class SemanticProviderError(RuntimeError):
    pass


class SemanticResponseError(SemanticProviderError):
    """A provider response failed after usage metadata was returned."""

    def __init__(self, message, *, input_tokens=0, output_tokens=0,
                 cache_read_tokens=0, finish_reason=""):
        super().__init__(message)
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_tokens = cache_read_tokens
        self.finish_reason = finish_reason


def _json_object_content(value):
    if not isinstance(value, str):
        raise ValueError("model content must be text")
    content = value.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        if start < 0:
            raise
        output, _end = json.JSONDecoder().raw_decode(content[start:])
        return output


def _usage_values(usage):
    if not isinstance(usage, Mapping):
        return 0, 0, 0
    details = usage.get("prompt_tokens_details", {})
    if not isinstance(details, Mapping):
        details = {}
    cache_read_tokens = int(
        details.get(
            "cached_tokens",
            usage.get("cache_read_input_tokens", usage.get("cached_tokens", 0)),
        )
    )
    input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
    if "cached_tokens" in details:
        input_tokens = max(0, input_tokens - cache_read_tokens)
    output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)))
    return input_tokens, cache_read_tokens, output_tokens


class OpenAICompatibleSemanticPort:
    translate_chinese_prompts = True

    def __init__(self, base_url, api_key, timeout_seconds=180):
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
        instruction = task.instruction or (
            "Return one JSON object only. Follow the requested event contract exactly."
        )
        instruction += (
            " Return one JSON object only; do not add timestamps, file paths, markdown, "
            "or commentary."
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
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content_parts = []
                reasoning_parts = []
                finish_reason = ""
                usage = {}
                received_bytes = 0
                generated_bytes = 0
                saw_data = False
                while True:
                    raw_line = response.readline()
                    if not raw_line:
                        break
                    received_bytes += len(raw_line)
                    if received_bytes > task.budget.max_output_bytes * 8:
                        raise SemanticProviderError(
                            "semantic provider stream exceeds transport byte budget"
                        )
                    try:
                        line = raw_line.decode("utf-8").strip()
                    except UnicodeDecodeError as exc:
                        raise SemanticProviderError(
                            "semantic provider returned an invalid stream"
                        ) from exc
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        raise SemanticProviderError(
                            "semantic provider returned a non-stream response"
                        )
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise SemanticProviderError(
                            "semantic provider returned an invalid stream chunk"
                        ) from exc
                    saw_data = True
                    if isinstance(chunk.get("usage"), Mapping):
                        usage = chunk["usage"]
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    if not isinstance(choice, Mapping):
                        raise SemanticProviderError(
                            "semantic provider returned an invalid stream choice"
                        )
                    delta = choice.get("delta", {})
                    if not isinstance(delta, Mapping):
                        raise SemanticProviderError(
                            "semantic provider returned an invalid stream delta"
                        )
                    content = delta.get("content")
                    reasoning = delta.get("reasoning_content")
                    if isinstance(content, str):
                        content_parts.append(content)
                        generated_bytes += len(content.encode("utf-8"))
                    if isinstance(reasoning, str):
                        reasoning_parts.append(reasoning)
                        generated_bytes += len(reasoning.encode("utf-8"))
                    if generated_bytes > task.budget.max_output_bytes:
                        raise SemanticProviderError(
                            "semantic provider response exceeds byte budget"
                        )
                    if choice.get("finish_reason"):
                        finish_reason = str(choice["finish_reason"])
        except (socket.timeout, TimeoutError) as exc:
            raise SemanticProviderError("semantic provider request timed out") from exc
        except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise SemanticProviderError("semantic provider request failed") from exc
        try:
            if not saw_data:
                raise ValueError("stream contained no data chunks")
            input_tokens, cache_read_tokens, output_tokens = _usage_values(usage)
        except (TypeError, ValueError) as exc:
            raise SemanticProviderError("semantic provider returned an invalid response") from exc
        content = "".join(content_parts) or "".join(reasoning_parts)
        if finish_reason in {"length", "max_tokens"}:
            raise SemanticResponseError(
                "semantic provider response was truncated",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                finish_reason=finish_reason,
            )
        try:
            output = _json_object_content(content)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SemanticResponseError(
                "semantic provider returned invalid response JSON",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                finish_reason=finish_reason,
            ) from exc
        if not isinstance(output, Mapping):
            raise SemanticResponseError(
                "semantic provider output must be a JSON object",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                finish_reason=finish_reason,
            )
        return ModelResult(output, input_tokens, output_tokens, cache_read_tokens)
