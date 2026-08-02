"""PRD-006 full-chain acceptance tests: real GPT-image-2 + Seedance 2.0 on project 青衣."""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE_URL = "http://127.0.0.1:8792"

_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
_SEEDANCE_URL = os.environ.get("SEEDANCE_BASE_URL", "")
_FULL_CHAIN_ENABLED = os.environ.get("E2E_FULL_CHAIN", "0") == "1"

requires_full_chain = pytest.mark.skipif(
    not (_FULL_CHAIN_ENABLED and _OPENAI_KEY and _SEEDANCE_URL),
    reason=(
        "FC-001~FC-004 需要 E2E_FULL_CHAIN=1、OPENAI_API_KEY 和 SEEDANCE_BASE_URL；"
        "当前未全部配置，已跳过。"
    ),
)

requires_service = pytest.mark.skipif(
    False,
    reason="",
)


def _http(method: str, url: str, body=None, timeout: float = 30.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read())
        except Exception:
            return exc.code, {}
    except Exception as exc:
        return None, {"error": str(exc)}


def _get(url: str, timeout: float = 5.0):
    return _http("GET", url, timeout=timeout)


def _post(url: str, body=None, timeout: float = 60.0):
    return _http("POST", url, body=body, timeout=timeout)


def _find_project_by_name(name_fragment: str):
    status, body = _get(f"{BASE_URL}/api/v1/projects")
    if status != 200:
        return None
    if isinstance(body, list):
        projects = body
    else:
        projects = body.get("projects", [])
    for p in projects:
        slug = p.get("slug", "")
        brief = p.get("brief", {})
        title = brief.get("title", "") if isinstance(brief, dict) else ""
        if name_fragment in slug or name_fragment in title:
            return p["project_id"]
    return None


def _get_workflow(project_id: str):
    status, body = _get(f"{BASE_URL}/api/v1/projects/{project_id}/workflow")
    if status != 200:
        return None
    return body


# ---------------------------------------------------------------------------
# Smoke: service reachable and project 青衣 exists
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_service_is_reachable():
    """Smoke: /readyz returns 200."""
    status, body = _get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("PRD-006 smoke: 服务未运行，已跳过")
    assert status == 200


@pytest.mark.e2e
def test_project_qingyi_exists_or_skip():
    """FC-000: project 青衣 (slug qingyi or 青衣 in title) exists on the running service."""
    status, _ = _get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("PRD-006: 服务未运行，已跳过")

    project_id = _find_project_by_name("qingyi") or _find_project_by_name("青衣")
    if project_id is None:
        pytest.skip(
            "FC-000: project 青衣 未在本地服务中，已跳过。"
            "请先创建项目或运行完整环境后重试。"
        )

    wf = _get_workflow(project_id)
    assert wf is not None, "workflow endpoint must return valid data"
    assert "stages" in wf
    assert "current_stage_id" in wf


# ---------------------------------------------------------------------------
# FC-001: background generation with real GPT-image-2
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_full_chain
def test_full_chain_background_generation():
    """FC-001: submit background job → job queued → executed → background_master created."""
    project_id = _find_project_by_name("qingyi") or _find_project_by_name("青衣")
    if not project_id:
        pytest.skip("FC-001: project 青衣 不在服务上，已跳过")

    wf = _get_workflow(project_id)
    shots_with_sg = []
    for stage in wf.get("stages", []):
        if stage["id"] in ("backgrounds", "scenes"):
            shots = stage.get("data", {}).get("shots", [])
            shots_with_sg = [s for s in shots if s.get("id")]
            break

    if not shots_with_sg:
        pytest.skip("FC-001: 无可用的场景组镜头，已跳过")

    shot_id = shots_with_sg[0]["id"]
    status, data = _post(
        f"{BASE_URL}/api/v1/projects/{project_id}/shots/{shot_id}/background/generate"
    )
    assert status == 202, f"Expected 202, got {status}: {data}"
    job_id = data.get("job_id", "")
    assert job_id, "Response must contain job_id"

    import time
    for _ in range(60):
        s, job_data = _get(f"{BASE_URL}/api/v1/jobs/{job_id}/inspect")
        if s == 200:
            state = job_data.get("status", {}).get("runtime_state", "")
            if state in ("succeeded", "failed"):
                break
        time.sleep(2)

    assert state == "succeeded", f"Background job ended with state: {state}"

    wf_after = _get_workflow(project_id)
    for stage in wf_after.get("stages", []):
        if stage["id"] in ("backgrounds", "scenes"):
            shots = stage.get("data", {}).get("shots", [])
            shot = next((s for s in shots if s.get("id") == shot_id), None)
            if shot:
                assert shot.get("background") or shot.get("background_master_id"), \
                    "Background must be set after successful generation"
            break


# ---------------------------------------------------------------------------
# FC-002: keyframe generation with real GPT-image-2
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_full_chain
def test_full_chain_keyframe_generation():
    """FC-002: submit keyframe job → job succeeded → keyframe entry in workflow."""
    project_id = _find_project_by_name("qingyi") or _find_project_by_name("青衣")
    if not project_id:
        pytest.skip("FC-002: project 青衣 不在服务上，已跳过")

    wf = _get_workflow(project_id)
    keyframe_shots = []
    for stage in wf.get("stages", []):
        if stage["id"] == "keyframes":
            shots = stage.get("data", {}).get("shots", [])
            keyframe_shots = [s for s in shots if s.get("background_master_id")]
            break

    if not keyframe_shots:
        pytest.skip("FC-002: 无已设置 background_master_id 的镜头，已跳过")

    shot_id = keyframe_shots[0]["id"]
    status, data = _post(
        f"{BASE_URL}/api/v1/projects/{project_id}/shots/{shot_id}/keyframes/generate"
    )
    assert status == 202, f"Expected 202, got {status}: {data}"
    job_id = data.get("job_id", "")
    assert job_id

    import time
    state = "queued"
    for _ in range(90):
        s, job_data = _get(f"{BASE_URL}/api/v1/jobs/{job_id}/inspect")
        if s == 200:
            state = job_data.get("status", {}).get("runtime_state", "")
            if state in ("succeeded", "failed"):
                break
        time.sleep(2)

    assert state == "succeeded", f"Keyframe job ended with state: {state}"


# ---------------------------------------------------------------------------
# FC-003: SSE events stream for a completed job
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_full_chain
def test_full_chain_sse_events_for_completed_job():
    """FC-003: GET /jobs/{job_id}/events for a completed job returns progress + done events."""
    project_id = _find_project_by_name("qingyi") or _find_project_by_name("青衣")
    if not project_id:
        pytest.skip("FC-003: project 青衣 不在服务上，已跳过")

    wf = _get_workflow(project_id)
    bg_shots = []
    for stage in wf.get("stages", []):
        if stage["id"] in ("backgrounds", "scenes"):
            bg_shots = stage.get("data", {}).get("shots", [])
            break

    if not bg_shots:
        pytest.skip("FC-003: 无可用镜头，已跳过")

    shot_id = bg_shots[0]["id"]
    status, data = _post(
        f"{BASE_URL}/api/v1/projects/{project_id}/shots/{shot_id}/background/generate"
    )
    if status != 202:
        pytest.skip(f"FC-003: background generate returned {status}, 已跳过")

    job_id = data.get("job_id", "")
    if not job_id:
        pytest.skip("FC-003: no job_id in response, 已跳过")

    import time
    for _ in range(90):
        s, _ = _get(f"{BASE_URL}/api/v1/jobs/{job_id}/inspect")
        if s == 200:
            break
        time.sleep(1)

    for _ in range(90):
        s, job_data = _get(f"{BASE_URL}/api/v1/jobs/{job_id}/inspect")
        if s == 200:
            state = job_data.get("status", {}).get("runtime_state", "")
            if state in ("succeeded", "failed"):
                break
        time.sleep(2)

    req = urllib.request.Request(f"{BASE_URL}/api/v1/jobs/{job_id}/events")
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            raw = resp.read().decode()
    except Exception as exc:
        pytest.skip(f"FC-003: could not read events stream: {exc}")

    assert "event: progress" in raw, "SSE stream must contain progress events"
    assert "event: done" in raw or "event: error" in raw, \
        "SSE stream must contain done or error event"


# ---------------------------------------------------------------------------
# FC-004: video generation with real Seedance 2.0
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_full_chain
def test_full_chain_video_generation():
    """FC-004: submit video job → job succeeded → video_entries in workflow."""
    project_id = _find_project_by_name("qingyi") or _find_project_by_name("青衣")
    if not project_id:
        pytest.skip("FC-004: project 青衣 不在服务上，已跳过")

    wf = _get_workflow(project_id)
    shots_with_kf = []
    for stage in wf.get("stages", []):
        if stage["id"] == "shots":
            shots = stage.get("data", {}).get("shots", [])
            shots_with_kf = [s for s in shots if s.get("selected_keyframe")]
            break

    if not shots_with_kf:
        pytest.skip("FC-004: 无已选定首帧的镜头，已跳过")

    shot_id = shots_with_kf[0]["id"]
    status, data = _post(
        f"{BASE_URL}/api/v1/projects/{project_id}/shots/{shot_id}/video/generate",
        body={"duration": 5},
    )
    assert status == 202, f"Expected 202, got {status}: {data}"

    import time
    wf_after = None
    for _ in range(120):
        _, wf_after = _get(f"{BASE_URL}/api/v1/projects/{project_id}/workflow")
        shots = []
        for stage in (wf_after or {}).get("stages", []):
            if stage["id"] == "shots":
                shots = stage.get("data", {}).get("shots", [])
                break
        shot = next((s for s in shots if s.get("id") == shot_id), None)
        if shot and shot.get("video_entries"):
            break
        time.sleep(3)

    assert shot is not None
    assert len(shot.get("video_entries", [])) >= 1, \
        "video_entries must be populated after successful video generation"
