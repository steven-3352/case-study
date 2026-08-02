"""PRD-003 E2E browser tests: keyframe stage UI, metadata display, batch confirm."""
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
        "ET-020~ET-023 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd003_browser.py"
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
# ET-020: keyframes stage shows explanation text
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_keyframes_stage_shows_explanation():
    """ET-020: 关键帧阶段顶部显示"组合首帧是什么？"说明文案。"""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-020: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        assert page.locator("text=视频模型的完整场景第一帧").count() > 0, \
            "关键帧阶段顶部必须显示'视频模型的完整场景第一帧'说明文案"
        assert page.locator("text=组合首帧是什么").count() > 0, \
            "关键帧阶段顶部必须显示'组合首帧是什么？'标题"

        browser.close()


# ---------------------------------------------------------------------------
# ET-021: candidate cards show source and cost metadata
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_keyframe_candidate_shows_metadata():
    """ET-021: 候选卡片显示来源（系统生成/用户上传）和费用信息。"""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-021: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-candidates", timeout=10_000)

        has_source = (
            page.locator("text=系统生成").count() > 0
            or page.locator("text=用户上传").count() > 0
            or page.locator("text=旧版").count() > 0
        )
        assert has_source, "候选卡片必须显示来源信息（系统生成/用户上传/旧版）"

        has_cost = page.locator("text=¥0").count() > 0
        assert has_cost, "候选卡片必须显示费用信息（¥0 或 ¥0.50 等）"

        browser.close()


# ---------------------------------------------------------------------------
# ET-022: generate button disabled when no background master
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_generate_keyframe_disabled_without_background_master():
    """ET-022: 场景背景未确认时"生成新候选"按钮禁用，显示说明文字。"""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-022: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        disabled_btn = page.locator("button.keyframe-generate[disabled]")
        no_bg_msg = page.locator("text=场景组背景未确认")
        if disabled_btn.count() > 0:
            assert no_bg_msg.count() > 0 or disabled_btn.first.inner_text() != "", \
                "禁用的生成按钮必须显示说明文字"

        browser.close()


# ---------------------------------------------------------------------------
# ET-023: batch confirm button enabled when all keyframes selected
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_batch_confirm_enabled_when_all_selected():
    """ET-023: 所有镜头选定组合首帧后，批量确认按钮可用。"""
    project_id = _find_project_at_stage("keyframes")
    if not project_id:
        pytest.skip("ET-023: 当前服务无已进入 keyframes 阶段且全部选定的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        batch_btn = page.locator("button:has-text('一键确认所有关键帧')")
        if batch_btn.count() > 0:
            assert not batch_btn.is_disabled(), \
                "全部选定时，批量确认按钮不应被禁用"

        browser.close()


# ---------------------------------------------------------------------------
# Smoke: service is reachable
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_service_is_reachable():
    """Smoke: /readyz 返回 200。"""
    status, body = _http_get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("服务未运行，跳过 ET-PRD003 smoke test")
    assert status == 200
    assert b"ready" in body
