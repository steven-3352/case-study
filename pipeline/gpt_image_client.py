"""Project-level GPT image API client with proxy compatibility.

This module keeps image generation transport concerns in one place:

- normalizes root and ``/v1`` base URLs;
- sends repeated ``image`` multipart fields for multi-reference edits;
- downsizes oversized references in memory before upload;
- accepts both normal and JSON-string-wrapped API payloads;
- decodes ``b64_json`` results or downloads URL results;
- rejects gateway HTML even when a proxy returns HTTP 200.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import math
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

import requests
from PIL import Image


log = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_EDGE = 2048


class GPTImageError(RuntimeError):
    """Raised when the image API or its proxy returns an unusable result."""


@dataclass(frozen=True)
class PreparedImage:
    path: Path
    filename: str
    mime_type: str
    content: bytes
    original_size: tuple[int, int]
    uploaded_size: tuple[int, int]

    @property
    def resized(self) -> bool:
        return self.original_size != self.uploaded_size


def normalize_api_base_url(base_url: str) -> str:
    """Return an API base URL ending in exactly one ``/v1`` segment."""
    parsed = urlsplit(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid GPT image base URL: {base_url!r}")

    path = parsed.path.rstrip("/")
    if not path.endswith("/v1"):
        path = f"{path}/v1" if path else "/v1"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def parse_image_payload(body: bytes | str) -> dict[str, Any]:
    """Parse normal JSON and the extra JSON-string layer used by some proxies."""
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    if text.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise GPTImageError("Image API returned an HTML gateway page instead of JSON")

    value: Any = text
    for _ in range(3):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            snippet = value[:200].replace("\n", " ")
            raise GPTImageError(f"Image API returned invalid JSON: {snippet!r}") from exc

    if not isinstance(value, dict):
        raise GPTImageError(
            f"Image API returned {type(value).__name__}, expected a JSON object"
        )
    return value


def _has_alpha(image: Image.Image) -> bool:
    return "A" in image.getbands() or "transparency" in image.info


def prepare_reference_image(
    path: Path | str,
    *,
    max_edge: int = DEFAULT_MAX_EDGE,
    max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> PreparedImage:
    """Load a reference and shrink it in memory when it exceeds upload limits."""
    source = Path(path)
    raw = source.read_bytes()
    with Image.open(io.BytesIO(raw)) as opened:
        opened.load()
        original_size = opened.size
        image = opened.copy()

    edge_scale = min(1.0, max_edge / max(original_size))
    byte_scale = min(1.0, math.sqrt(max_bytes / len(raw)) * 0.95)
    scale = min(edge_scale, byte_scale)
    if scale == 1.0 and len(raw) <= max_bytes:
        return PreparedImage(
            path=source,
            filename=source.name,
            mime_type=mimetypes.guess_type(source.name)[0] or "application/octet-stream",
            content=raw,
            original_size=original_size,
            uploaded_size=original_size,
        )

    has_alpha = _has_alpha(image)
    output_format = "PNG" if has_alpha else "JPEG"
    suffix = ".png" if has_alpha else ".jpg"
    mime_type = "image/png" if has_alpha else "image/jpeg"
    content = b""

    for _ in range(8):
        width = max(1, round(original_size[0] * scale))
        height = max(1, round(original_size[1] * scale))
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        if has_alpha:
            resized.save(buffer, format=output_format, optimize=True)
        else:
            resized.convert("RGB").save(
                buffer, format=output_format, quality=95, optimize=True
            )
        content = buffer.getvalue()
        if len(content) <= max_bytes:
            break
        scale *= max(0.5, math.sqrt(max_bytes / len(content)) * 0.95)

    if len(content) > max_bytes:
        raise GPTImageError(
            f"Reference remains too large after resizing: {source} ({len(content)} bytes)"
        )

    uploaded_size = (width, height)
    log.info(
        "compressed reference %s: %sx%s/%d KB -> %sx%s/%d KB",
        source,
        *original_size,
        len(raw) // 1024,
        *uploaded_size,
        len(content) // 1024,
    )
    return PreparedImage(
        path=source,
        filename=f"{source.stem}_upload{suffix}",
        mime_type=mime_type,
        content=content,
        original_size=original_size,
        uploaded_size=uploaded_size,
    )


class GPTImageClient:
    """Direct HTTP client for GPT image generation and multi-reference edits."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str = "gpt-image-2",
        timeout: float = 300.0,
        attempts: int = 4,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GPT image API key is required")
        if attempts < 1:
            raise ValueError("attempts must be at least 1")
        self.api_key = api_key
        self.base_url = normalize_api_base_url(base_url)
        self.model = model
        self.timeout = timeout
        self.attempts = attempts
        self.session = session or requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def generate(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        quality: str | None = None,
        output_format: str | None = None,
    ) -> bytes:
        payload = self._base_fields(
            prompt=prompt,
            size=size,
            quality=quality,
            output_format=output_format,
        )
        response = self._post("images/generations", json=payload)
        return self._decode_result(response)

    def edit(
        self,
        *,
        prompt: str,
        images: Sequence[Path | str],
        size: str = "1024x1024",
        quality: str | None = None,
        output_format: str | None = None,
        max_edge: int = DEFAULT_MAX_EDGE,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    ) -> bytes:
        if not images:
            raise ValueError("At least one reference image is required for an edit")

        prepared = [
            prepare_reference_image(
                path, max_edge=max_edge, max_bytes=max_upload_bytes
            )
            for path in images
        ]
        files = [
            ("image", (item.filename, item.content, item.mime_type))
            for item in prepared
        ]
        fields = self._base_fields(
            prompt=prompt,
            size=size,
            quality=quality,
            output_format=output_format,
        )
        response = self._post("images/edits", data=fields, files=files)
        return self._decode_result(response)

    def _base_fields(
        self,
        *,
        prompt: str,
        size: str,
        quality: str | None,
        output_format: str | None,
    ) -> dict[str, str | int]:
        fields: dict[str, str | int] = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
        if quality:
            fields["quality"] = quality
        if output_format:
            fields["output_format"] = output_format
        return fields

    def _post(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                response = self.session.post(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs,
                )
            except requests.RequestException as exc:
                last_error = exc
            else:
                body = response.content
                if 200 <= response.status_code < 300:
                    return parse_image_payload(body)

                snippet = body[:300].decode("utf-8", errors="replace")
                error = GPTImageError(
                    f"Image API HTTP {response.status_code}: {snippet}"
                )
                if response.status_code not in {408, 425, 429} and response.status_code < 500:
                    raise error
                last_error = error

            if attempt == self.attempts:
                break
            log.warning(
                "image API attempt %d/%d failed: %s",
                attempt,
                self.attempts,
                last_error,
            )
            time.sleep(5 * attempt)

        raise GPTImageError(
            f"Image API failed after {self.attempts} attempts: {last_error}"
        ) from last_error

    def _decode_result(self, payload: Mapping[str, Any]) -> bytes:
        items = payload.get("data")
        if not isinstance(items, list) or not items or not isinstance(items[0], Mapping):
            raise GPTImageError("Image API response has no data item")

        first = items[0]
        encoded = first.get("b64_json")
        if isinstance(encoded, str) and encoded:
            try:
                return base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise GPTImageError("Image API returned invalid base64 image data") from exc

        url = first.get("url")
        if isinstance(url, str) and url:
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException as exc:
                raise GPTImageError(f"Failed to download generated image: {exc}") from exc
            return response.content

        raise GPTImageError("Image API result has neither b64_json nor url")
