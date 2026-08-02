"""PRD-001 API contract tests: ApplicationBlocked error response format."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from apps.mv_api import create_app
from apps.runtime import build_service
from mv_platform.application.service import ApplicationBlocked


@pytest.fixture
def service(tmp_path):
    return build_service(tmp_path, with_supervisor=False)


@pytest.fixture
def client(service):
    return TestClient(create_app(service=service))


@pytest.fixture
def project_id(service):
    p = service.create_project("qingyi", {"title": "青衣"})
    return p.project_id


# ---------------------------------------------------------------------------
# CT-001: Translation fail returns 423 + error_stage + error_category
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_translate_fail_includes_error_stage(client, project_id):
    exc = ApplicationBlocked(
        "image prompt translation failed",
        error_stage="translate_prompt",
        error_category="timeout",
    )
    client.app.state.service.submit_generate_background_job = _raise_factory(exc)
    resp = client.post(f"/api/v1/projects/{project_id}/shots/S001/background/generate")

    assert resp.status_code == 423
    body = resp.json()
    assert body["error_stage"] == "translate_prompt"
    assert body["error_category"] == "timeout"
    assert "detail" in body


# ---------------------------------------------------------------------------
# CT-002: ApplicationBlocked without stage/category still returns 423
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_application_blocked_without_stage_still_423(client, project_id):
    exc = ApplicationBlocked("precondition not met")
    client.app.state.service.submit_generate_background_job = _raise_factory(exc)
    resp = client.post(f"/api/v1/projects/{project_id}/shots/S001/background/generate")
    assert resp.status_code == 423
    body = resp.json()
    assert "detail" in body
    assert "error_stage" not in body or body.get("error_stage") == ""


# ---------------------------------------------------------------------------
# CT-003: Precondition fail returns correct stage
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_background_generate_precondition_fail(client, project_id):
    exc = ApplicationBlocked(
        "story is not approved",
        error_stage="precondition",
        error_category="precondition",
    )
    client.app.state.service.submit_generate_background_job = _raise_factory(exc)
    resp = client.post(f"/api/v1/projects/{project_id}/shots/S001/background/generate")
    assert resp.status_code == 423
    body = resp.json()
    assert body.get("error_stage") == "precondition"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raise_factory(exc):
    def _raise(*args, **kwargs):
        raise exc
    return _raise


def _make_blocking_service(exc):
    raise exc
