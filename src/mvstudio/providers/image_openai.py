"""OpenAI-compatible GPT image provider for project-owned generation."""

from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI


class ImageProviderError(RuntimeError):
    pass


class OpenAICompatibleImageProvider:
    def __init__(self, base_url, api_key, model="gpt-image-2", timeout_seconds=300,
                 client=None, downloader=None):
        if not isinstance(base_url, str) or not isinstance(api_key, str) or not api_key:
            raise ImageProviderError("image provider configuration is incomplete")
        if not base_url:
            raise ImageProviderError("画面生成服务地址未配置：请在「系统配置 → 画面生成服务」填写以 https:// 开头的服务地址")
        parsed = urlparse(base_url)
        loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if parsed.scheme not in ({"http", "https"} if loopback else {"https"}):
            raise ImageProviderError("image provider URL must use HTTPS or loopback HTTP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.netloc:
            raise ImageProviderError("image provider URL is invalid")
        if not isinstance(model, str) or not model.strip():
            raise ImageProviderError("image provider model is missing")
        self.model = model.strip()
        self.timeout_seconds = float(timeout_seconds)
        normalized_path = parsed.path.rstrip("/")
        if not normalized_path.endswith("/v1"):
            normalized_path = (normalized_path + "/v1") if normalized_path else "/v1"
        normalized_url = parsed._replace(path=normalized_path, params="", query="", fragment="").geturl()
        self.client = client or OpenAI(
            api_key=api_key, base_url=normalized_url, timeout=self.timeout_seconds,
            max_retries=0,
        )
        self.downloader = downloader or requests.Session()

    @classmethod
    def from_env(cls, environ):
        return cls(
            environ.get("GPT_IMAGE_BASE_URL", ""),
            environ.get("GPT_IMAGE_API_KEY", ""),
            environ.get("GPT_IMAGE_MODEL", "gpt-image-2"),
        )

    def generate(self, prompt, references=(), size="1024x1536",
                 quality=None, output_format=None):
        extra = {}
        if quality:
            extra["quality"] = quality
        if output_format:
            extra["output_format"] = output_format
        handles = []
        try:
            if references:
                handles = [Path(path).open("rb") for path in references]
                result = self.client.images.edit(
                    model=self.model, image=handles, prompt=prompt, size=size, n=1,
                    **extra,
                )
            else:
                result = self.client.images.generate(
                    model=self.model, prompt=prompt, size=size, n=1,
                    **extra,
                )
        except Exception as exc:
            raise ImageProviderError("image provider request failed") from exc
        finally:
            for handle in handles:
                handle.close()
        try:
            item = result.data[0]
        except (AttributeError, IndexError, TypeError) as exc:
            raise ImageProviderError("image provider returned no image") from exc
        encoded = getattr(item, "b64_json", None)
        if isinstance(encoded, str) and encoded:
            try:
                return base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise ImageProviderError("image provider returned invalid image data") from exc
        url = getattr(item, "url", None)
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != "https" or not parsed.netloc:
            raise ImageProviderError("image provider returned an unsafe image URL")
        try:
            response = self.downloader.get(url, timeout=self.timeout_seconds, stream=True)
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(1024 * 1024):
                content.extend(chunk)
                if len(content) > 40 * 1024 * 1024:
                    raise ImageProviderError("generated image is too large")
            return bytes(content)
        except ImageProviderError:
            raise
        except requests.RequestException as exc:
            raise ImageProviderError("generated image download failed") from exc
