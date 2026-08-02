"""PRD-005 E2E browser tests: SSE progress UI, async generate buttons."""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE_URL = "http://127.0.0.1:8792"

_UI_TESTS_ENABLED = os.environ.get("E2E_UI_TESTS", "0") == "1"

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

requires_ui = pytest.mark.skipif(
    not (_PLAYWRIGHT_AVAILABLE and _UI_TESTS_ENABLED),
    reason=(
        "ET-041~ET-043 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd005_browser.py"
    ),
)


def _http_get(url: str, timeout: float = 3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return None, b""


def _find_project_at_stage(target_stage: str):
    status, body = _http_get(f"{BASE_URL}/api/v1/projects")
    if status != 200 or not body:
        return None
    for p in json.loads(body):
        pid = p["project_id"]
        ws, wb = _http_get(f"{BASE_URL}/api/v1/projects/{pid}/workflow")
        if ws != 200:
            continue
        wf = json.loads(wb)
        stage_ids = [s["id"] for s in wf.get("stages", [])]
        if target_stage not in stage_ids:
            continue
        current = wf.get("current_stage_id", "")
        idx_target = stage_ids.index(target_stage)
        idx_current = stage_ids.index(current) if current in stage_ids else -1
        if idx_current >= idx_target:
            return pid
    return None


# ---------------------------------------------------------------------------
# Smoke: service is reachable
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_service_is_reachable():
    """Smoke: /readyz returns 200."""
    status, body = _http_get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("服务未运行，跳过 ET-PRD005 smoke test")
    assert status == 200
    assert b"ready" in body


# ---------------------------------------------------------------------------
# ET-041: background generate button returns 202 (async response)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_background_generate_shows_async_progress():
    """ET-041: Click generate background → UI shows job_id or progress indicator (async 202)."""
    project_id = _find_project_at_stage("backgrounds")
    if not project_id:
        pytest.skip("ET-041: 当前服务无已进入 backgrounds 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='backgrounds']", timeout=10_000)
        page.click("[data-stage='backgrounds']")
        page.wait_for_selector(".backgrounds-workbench, .scene-group", timeout=10_000)

        gen_btn = page.locator("button.bg-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-041: 当前项目无可用背景生成按钮，已跳过")

        gen_btn.click()
        page.wait_for_selector("text=生成中, .progress-bar, [data-job-id]", timeout=15_000)

        browser.close()


# ---------------------------------------------------------------------------
# ET-042: keyframe generate button returns 202 (async response)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_keyframe_generate_shows_async_progress():
    """ET-042: Click generate keyframe → UI shows async progress (job_id in DOM or spinner)."""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-042: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframes-workbench, .shot", timeout=10_000)

        gen_btn = page.locator("button.kf-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-042: 当前项目无可用首帧生成按钮，已跳过")

        gen_btn.click()
        page.wait_for_selector("text=生成中, .progress-bar, [data-job-id]", timeout=15_000)

        browser.close()


# ---------------------------------------------------------------------------
# ET-043: SSE events shown as progress steps in UI
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_sse_progress_steps_visible_in_ui():
    """ET-043: During async image generation, SSE progress events render as step indicators."""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-043: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframes-workbench, .shot", timeout=10_000)

        gen_btn = page.locator("button.kf-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-043: 当前项目无可用首帧生成按钮，已跳过")

        gen_btn.click()
        progress_visible = page.locator(".progress-step, [data-stage='translate_prompt']").count() > 0
        if not progress_visible:
            page.wait_for_selector(
                ".progress-step, [data-stage='translate_prompt'], text=翻译提示词",
                timeout=30_000,
            )
        assert page.locator(
            ".progress-step, [data-stage='translate_prompt'], text=翻译提示词"
        ).count() > 0, "SSE progress steps must be rendered in UI"

        browser.close()
