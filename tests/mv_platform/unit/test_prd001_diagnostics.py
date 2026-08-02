"""PRD-001 unit tests: diagnostics, ApplicationBlocked, error logging, retry."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[4] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mv_platform.application.service import ApplicationBlocked, ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure import Database
from mvstudio.providers.semantic_openai import SemanticProviderError, SemanticResponseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _NoopLogs:
    def __init__(self):
        self.records = []
    def append(self, source, event):
        self.records.append({"source": source, **event})


def make_service(tmp_path, semantic_port=None, semantic_model="test-model", error_logs=None):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(
        settings, database, workspace_root=tmp_path,
        semantic_port=semantic_port, semantic_model=semantic_model,
        error_logs=error_logs,
    )
    service.initialize()
    return service


# ---------------------------------------------------------------------------
# UT-006: ApplicationBlocked carries error_stage and error_category
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_application_blocked_carries_stage_and_category():
    exc = ApplicationBlocked("test", error_stage="translate_prompt", error_category="timeout")
    assert exc.error_stage == "translate_prompt"
    assert exc.error_category == "timeout"
    assert str(exc) == "test"


# ---------------------------------------------------------------------------
# UT-007: Existing ApplicationBlocked calls (no stage/category) still work
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_application_blocked_backward_compatible():
    exc = ApplicationBlocked("workspace_root is required")
    assert exc.error_stage == ""
    assert exc.error_category == ""
    assert str(exc) == "workspace_root is required"


# ---------------------------------------------------------------------------
# Fixtures for _translate_image_prompt tests
# ---------------------------------------------------------------------------

EVENT_TYPE = "image.background.generate_requested"


@pytest.fixture
def project_with_prompts(tmp_path):
    """Return (service, project_id, logs, port) with prompts set up."""
    logs = _NoopLogs()
    port = MagicMock()
    service = make_service(tmp_path, semantic_port=port, error_logs=logs)

    result = service.create_project("qingyi", {"title": "青衣2"})
    project_id = result.project_id
    return service, project_id, logs, port


def _make_context(shot_id="S001"):  # noqa: E302
    return {
        "shot": {"id": shot_id, "index": 0},
        "characters": [],
        "backgrounds": [],
        "scenes": [],
        "story": {"approved_text": "测试故事"},
        "previous": "",
        "next": "",
    }


# ---------------------------------------------------------------------------
# UT-001: Timeout logs error_category=timeout
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_logs_timeout_category(project_with_prompts):
    service, project_id, logs, port = project_with_prompts
    port.run.side_effect = SemanticProviderError("semantic provider request timed out")

    with pytest.raises(ApplicationBlocked) as exc_info:
        service._translate_image_prompt(project_id, EVENT_TYPE, _make_context(), "req-001")

    assert exc_info.value.error_category == "timeout"
    fail_records = [r for r in logs.records if r.get("event") == "image_prompt_translation_failed"]
    assert fail_records, "expected a failed log record"
    assert fail_records[-1]["error_category"] == "timeout"
    assert fail_records[-1]["request_id"] == "req-001"
    assert fail_records[-1]["model"] != ""


# ---------------------------------------------------------------------------
# UT-002: Content filter logs error_category=content_filtered
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_logs_content_filtered(project_with_prompts):
    service, project_id, logs, port = project_with_prompts
    port.run.side_effect = SemanticResponseError(
        "content filtered", finish_reason="content_filter"
    )

    with pytest.raises(ApplicationBlocked) as exc_info:
        service._translate_image_prompt(project_id, EVENT_TYPE, _make_context(), "req-002")

    assert exc_info.value.error_category == "content_filtered"
    fail_records = [r for r in logs.records if r.get("event") == "image_prompt_translation_failed"]
    assert fail_records[-1]["error_category"] == "content_filtered"
    assert port.run.call_count == 1  # no retry


# ---------------------------------------------------------------------------
# UT-003: Truncated logs error_category=truncated, no retry
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_logs_truncated_no_retry(project_with_prompts):
    service, project_id, logs, port = project_with_prompts
    port.run.side_effect = SemanticResponseError(
        "truncated", finish_reason="length"
    )

    with pytest.raises(ApplicationBlocked) as exc_info:
        service._translate_image_prompt(project_id, EVENT_TYPE, _make_context(), "req-003")

    assert exc_info.value.error_category == "truncated"
    assert port.run.call_count == 1  # no retry


# ---------------------------------------------------------------------------
# UT-004: Network error retries once then succeeds
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_retries_once_on_http_error(project_with_prompts):
    from mvstudio.director.drafting import ModelResult
    service, project_id, logs, port = project_with_prompts
    success_result = ModelResult(
        output={"english_prompt": "English production prompt"},
        input_tokens=10, output_tokens=20, cache_read_tokens=0,
    )
    port.run.side_effect = [
        SemanticProviderError("request failed with 503"),
        success_result,
    ]

    result_prompt, _ = service._translate_image_prompt(
        project_id, EVENT_TYPE, _make_context(), "req-004"
    )

    assert result_prompt == "English production prompt"
    assert port.run.call_count == 2
    retry_records = [r for r in logs.records if r.get("event") == "image_prompt_translation_retrying"]
    assert len(retry_records) == 1


# ---------------------------------------------------------------------------
# UT-005: Two consecutive failures → final ApplicationBlocked with http_error
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_translate_fails_after_one_retry(project_with_prompts):
    service, project_id, logs, port = project_with_prompts
    port.run.side_effect = SemanticProviderError("request failed with 503")

    with pytest.raises(ApplicationBlocked) as exc_info:
        service._translate_image_prompt(project_id, EVENT_TYPE, _make_context(), "req-005")

    assert exc_info.value.error_category == "http_error"
    assert port.run.call_count == 2
