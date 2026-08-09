from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from conductor import tools
from conductor.pipeline import STEP_BY_ID
from conductor.tools import intake_validate


def _image(path: Path) -> None:
    Image.new("RGB", (80, 120), (230, 220, 200)).save(path)


def _request(out_dir: Path, rights: dict | None = None, **extra) -> None:
    body = {"aspect_ratio": "9:16", "rights": rights or {}}
    body.update(extra)
    (out_dir / "request.yaml").write_text(
        yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")


def _stub_video_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.media, "video_duration_seconds", lambda path: 12.5)
    monkeypatch.setattr(tools, "_video_resolution", lambda path: (1080, 1920))


def test_intake_scans_project_material_directories_and_hashes_all_files(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "00_intake"
    out_dir.mkdir()
    for folder in ("reference", "product", "brief"):
        (tmp_path / folder).mkdir()
    (tmp_path / "reference" / "source.mp4").write_bytes(b"reference-video")
    for name in ("sku-front.png", "sku-back.png", "sku-side.png"):
        _image(tmp_path / "product" / name)
    (tmp_path / "brief" / "requirements.md").write_text(
        "商品卖点和新视频要求", encoding="utf-8")
    _request(out_dir, {
        "source": "user_owned", "declared_by": "owner", "usage": "ad production",
    })
    _stub_video_probe(monkeypatch)

    result = intake_validate([], out_dir, {})
    manifest = yaml.safe_load((out_dir / "manifest.yaml").read_text(encoding="utf-8"))
    report = yaml.safe_load((out_dir / "preflight-report.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert result.outputs[-1] == "preflight-report.yaml"
    assert report["result"] == "pass"
    assert manifest["reference_video"]["duration_seconds"] == 12.5
    assert manifest["reference_video"]["width"] == 1080
    assert manifest["reference_video"]["digest"].startswith("sha256:")
    assert len(manifest["images"]) == 3
    assert all(item["digest"].startswith("sha256:") for item in manifest["images"])
    assert manifest["brief"]["files"][0]["digest"].startswith("sha256:")


def test_missing_rights_blocks_after_persisting_preflight(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "00_intake"
    out_dir.mkdir()
    reference = tmp_path / "reference.mp4"
    reference.write_bytes(b"reference")
    product = tmp_path / "front.png"
    _image(product)
    _request(out_dir, reference_video=str(reference), images=[{
        "path": str(product), "role": "product", "view": "front",
    }], brief_text="new video brief")
    _stub_video_probe(monkeypatch)

    result = intake_validate([], out_dir, {})
    report = yaml.safe_load((out_dir / "preflight-report.yaml").read_text(encoding="utf-8"))

    assert not result.ok
    assert result.error["code"] == "material_preflight_blocked"
    assert report["result"] == "blocked"
    assert any(issue["id"] == "MAT-006" for issue in report["blocking_issues"])
    package = result.meta["recommendations"]
    assert package["status"] == "blocked_with_recommendations"
    assert len(package["options"]) == 2
    assert package["recommended_option"] == "O1"
    assert package["resume_from"] == "N01_material_preflight"


def test_missing_product_views_is_fixable_and_can_continue(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "00_intake"
    out_dir.mkdir()
    reference = tmp_path / "reference.mp4"
    reference.write_bytes(b"reference")
    product = tmp_path / "front.png"
    _image(product)
    _request(
        out_dir,
        {"source": "licensed", "declared_by": "producer", "usage": "advertising"},
        reference_video={"path": str(reference)},
        images=[{"path": str(product), "role": "product", "view": "front"}],
        brief_text="new video brief",
    )
    _stub_video_probe(monkeypatch)

    result = intake_validate([], out_dir, {})
    report = yaml.safe_load((out_dir / "preflight-report.yaml").read_text(encoding="utf-8"))

    assert result.ok
    assert report["result"] == "conditional_pass"
    assert {item["id"] for item in report["fixable_issues"]} == {"MAT-004", "MAT-005"}


def test_conflicting_declared_skus_are_blocking(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "00_intake"
    out_dir.mkdir()
    reference = tmp_path / "reference.mp4"
    reference.write_bytes(b"reference")
    front, back = tmp_path / "front.png", tmp_path / "back.png"
    _image(front)
    _image(back)
    _request(
        out_dir,
        {"source": "owned", "declared_by": "owner", "usage": "advertising"},
        reference_video=str(reference), brief_text="brief", images=[
            {"path": str(front), "role": "product", "view": "front", "sku": "SKU-A"},
            {"path": str(back), "role": "product", "view": "back", "sku": "SKU-B"},
        ],
    )
    _stub_video_probe(monkeypatch)

    result = intake_validate([], out_dir, {})
    report = yaml.safe_load((out_dir / "preflight-report.yaml").read_text(encoding="utf-8"))

    assert not result.ok
    assert any(item["id"] == "MAT-007" for item in report["blocking_issues"])


def test_unreadable_reference_is_blocking_and_report_is_persisted(tmp_path: Path) -> None:
    out_dir = tmp_path / "00_intake"
    out_dir.mkdir()
    front, back, side = (tmp_path / "front.png", tmp_path / "back.png",
                         tmp_path / "side.png")
    for path in (front, back, side):
        _image(path)
    _request(
        out_dir,
        {"source": "owned", "declared_by": "owner", "usage": "advertising"},
        reference_video=str(tmp_path / "missing.mp4"), brief_text="brief", images=[
            {"path": str(front), "role": "product", "view": "front"},
            {"path": str(back), "role": "product", "view": "back"},
            {"path": str(side), "role": "product", "view": "side"},
        ],
    )

    result = intake_validate([], out_dir, {})
    report_path = out_dir / "preflight-report.yaml"
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))

    assert not result.ok
    assert report_path.is_file()
    assert report["result"] == "blocked"
    assert any("参考视频不可读" in item["issue"] for item in report["blocking_issues"])


def test_shot_generation_declares_intake_dependency() -> None:
    assert STEP_BY_ID["04_shots"].input_from == ["03_keyframes", "00_intake"]
