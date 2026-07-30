from __future__ import annotations

import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from pipeline.gpt_image_client import (
    GPTImageClient,
    GPTImageError,
    normalize_api_base_url,
    parse_image_payload,
    prepare_reference_image,
)


class FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(
        self,
        *,
        post_response: FakeResponse,
        get_response: FakeResponse | None = None,
    ) -> None:
        self.post_response = post_response
        self.get_response = get_response
        self.posts: list[tuple[str, dict[str, Any]]] = []
        self.gets: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append((url, kwargs))
        return self.post_response

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.gets.append((url, kwargs))
        if self.get_response is None:
            raise AssertionError("Unexpected GET")
        return self.get_response


def json_response(payload: object) -> FakeResponse:
    return FakeResponse(json.dumps(payload).encode("utf-8"))


class BaseUrlTests(unittest.TestCase):
    def test_normalizes_root_and_v1_urls(self) -> None:
        self.assertEqual(
            normalize_api_base_url("https://images.example.com"),
            "https://images.example.com/v1",
        )
        self.assertEqual(
            normalize_api_base_url("https://images.example.com/v1/"),
            "https://images.example.com/v1",
        )
        self.assertEqual(
            normalize_api_base_url("https://images.example.com/gateway/v1"),
            "https://images.example.com/gateway/v1",
        )

    def test_rejects_invalid_base_url(self) -> None:
        with self.assertRaises(ValueError):
            normalize_api_base_url("images.example.com")


class ResponseParsingTests(unittest.TestCase):
    def test_parses_json_string_wrapped_payload(self) -> None:
        payload = {"data": [{"b64_json": "aW1hZ2U="}]}
        wrapped = json.dumps(json.dumps(payload)).encode("utf-8")
        self.assertEqual(parse_image_payload(wrapped), payload)

    def test_rejects_html_success_page(self) -> None:
        with self.assertRaisesRegex(GPTImageError, "HTML gateway"):
            parse_image_payload(b"<!doctype html><html></html>")

    def test_decodes_base64_result(self) -> None:
        payload = {"data": [{"b64_json": base64.b64encode(b"png").decode()}]}
        session = FakeSession(post_response=json_response(payload))
        client = GPTImageClient(
            api_key="test",
            base_url="https://images.example.com",
            attempts=1,
            session=session,  # type: ignore[arg-type]
        )

        self.assertEqual(client.generate(prompt="test"), b"png")
        self.assertEqual(
            session.posts[0][0],
            "https://images.example.com/v1/images/generations",
        )

    def test_downloads_url_result(self) -> None:
        session = FakeSession(
            post_response=json_response(
                {"data": [{"url": "https://cdn.example.com/result.png"}]}
            ),
            get_response=FakeResponse(b"downloaded"),
        )
        client = GPTImageClient(
            api_key="test",
            base_url="https://images.example.com/v1",
            attempts=1,
            session=session,  # type: ignore[arg-type]
        )

        self.assertEqual(client.generate(prompt="test"), b"downloaded")
        self.assertEqual(session.gets[0][0], "https://cdn.example.com/result.png")

    def test_rejects_html_even_with_http_200(self) -> None:
        session = FakeSession(
            post_response=FakeResponse(b"<html>gateway application</html>")
        )
        client = GPTImageClient(
            api_key="test",
            base_url="https://images.example.com",
            attempts=4,
            session=session,  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(GPTImageError, "HTML gateway"):
            client.generate(prompt="test")
        self.assertEqual(len(session.posts), 1)


class ReferenceUploadTests(unittest.TestCase):
    def test_downsizes_large_reference_and_preserves_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "large.png"
            Image.new("RGBA", (3000, 1200), (20, 40, 60, 128)).save(path)

            prepared = prepare_reference_image(
                path,
                max_edge=512,
                max_bytes=500_000,
            )

            self.assertEqual(prepared.original_size, (3000, 1200))
            self.assertLessEqual(max(prepared.uploaded_size), 512)
            self.assertEqual(prepared.mime_type, "image/png")
            self.assertLessEqual(len(prepared.content), 500_000)
            with Image.open(io.BytesIO(prepared.content)) as uploaded:
                self.assertEqual(uploaded.mode, "RGBA")

    def test_edit_posts_repeated_image_fields(self) -> None:
        payload = {"data": [{"b64_json": base64.b64encode(b"edited").decode()}]}
        session = FakeSession(post_response=json_response(payload))
        client = GPTImageClient(
            api_key="test",
            base_url="https://images.example.com/",
            attempts=1,
            session=session,  # type: ignore[arg-type]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.png"
            second = Path(temp_dir) / "second.png"
            Image.new("RGB", (64, 64), "red").save(first)
            Image.new("RGBA", (64, 64), (0, 255, 0, 128)).save(second)

            result = client.edit(prompt="combine", images=[first, second])

        self.assertEqual(result, b"edited")
        url, kwargs = session.posts[0]
        self.assertEqual(url, "https://images.example.com/v1/images/edits")
        self.assertEqual([field for field, _ in kwargs["files"]], ["image", "image"])
        self.assertEqual(kwargs["data"]["prompt"], "combine")


if __name__ == "__main__":
    unittest.main()
