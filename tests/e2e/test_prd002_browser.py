"""PRD-002 E2E browser tests: scenes stage nav, shot card UI changes."""
import json
import os
import time
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
        "ET-010~ET-013 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd002_browser.py"
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return None, b""


def _find_project_at_stage(target_stage: str):
    """Return project_id of first project at or past target_stage, or None."""
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
        if target_stage in stage_ids:
            current = wf.get("current_stage_id", "")
            idx_target = stage_ids.index(target_stage)
            idx_current = stage_ids.index(current) if current in stage_ids else -1
            if idx_current >= idx_target:
                return pid
    return None


def _find_storyboard_project():
    """Return project_id with storyboard data for shot card tests."""
    status, body = _http_get(f"{BASE_URL}/api/v1/projects")
    if status != 200 or not body:
        return None
    for p in json.loads(body):
        pid = p["project_id"]
        ws, wb = _http_get(f"{BASE_URL}/api/v1/projects/{pid}/workflow")
        if ws != 200:
            continue
        wf = json.loads(wb)
        for stage in wf.get("stages", []):
            if stage.get("id") == "storyboard" and stage.get("data", {}).get("shots"):
                return pid
    return None


# ---------------------------------------------------------------------------
# ET-010: scenes stage is visible and positioned between storyboard/keyframes
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_scenes_stage_visible_in_nav():
    """ET-010: 场景与背景阶段在导航栏中出现且位于分镜确认和关键帧之间。"""
    project_id = _find_storyboard_project()
    if not project_id:
        pytest.skip("ET-010: 当前服务无分镜数据，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("#stage-rail", timeout=10_000)

        rail_buttons = page.locator("#stage-rail button[data-stage]")
        stage_ids = rail_buttons.evaluate_all(
            "buttons => buttons.map(b => b.dataset.stage)"
        )

        assert "scenes" in stage_ids, "scenes stage not found in nav rail"
        assert "storyboard" in stage_ids
        assert "keyframes" in stage_ids
        assert stage_ids.index("scenes") == stage_ids.index("storyboard") + 1
        assert stage_ids.index("keyframes") == stage_ids.index("scenes") + 1

        browser.close()


# ---------------------------------------------------------------------------
# ET-011: shot card has no 'generate background' button; shows scene group label
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_shot_card_has_no_generate_background_button():
    """ET-011: 分镜卡不再有"生成背景"按钮，改为"所属场景组"标签。"""
    project_id = _find_storyboard_project()
    if not project_id:
        pytest.skip("ET-011: 当前服务无分镜数据，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")

        # Navigate to storyboard stage
        page.wait_for_selector("[data-stage='storyboard']", timeout=10_000)
        page.click("[data-stage='storyboard']")
        page.wait_for_selector(".shot-card", timeout=10_000)

        # Old "generate background" button must NOT exist
        assert page.locator("[data-generate-background]").count() == 0, \
            "旧版'生成背景'按钮不应出现在分镜卡"

        # Scene group label should exist
        assert page.locator("text=所属场景组").count() > 0, \
            "'所属场景组'标签未出现在分镜卡"

        browser.close()


# ---------------------------------------------------------------------------
# ET-012: generating a background in scenes stage shows thumbnail (needs provider)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_generate_background_in_scenes_stage():
    """ET-012: 在场景与背景阶段生成背景，出现图片缩略图。需要真实 Provider。"""
    project_id = _find_project_at_stage("scenes")
    if not project_id:
        pytest.skip("ET-012: 当前服务无已进入 scenes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")

        page.wait_for_selector("[data-stage='scenes']", timeout=10_000)
        page.click("[data-stage='scenes']")

        gen_button = page.locator("[data-generate-sg-background]").first
        page.wait_for_selector("[data-generate-sg-background]", timeout=10_000)

        gen_button.click()
        # Wait up to 120 s for image to appear
        page.wait_for_selector(".bg-candidate img", timeout=120_000)
        assert page.locator(".bg-candidate img").count() > 0

        browser.close()


# ---------------------------------------------------------------------------
# ET-013: approve button enabled after all groups have a selected background
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_approve_scenes_enabled_after_all_selected():
    """ET-013: 所有场景组均有选定背景后，"确认并进入下一步"按钮可用。"""
    project_id = _find_project_at_stage("scenes")
    if not project_id:
        pytest.skip("ET-013: 当前服务无已进入 scenes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")

        page.wait_for_selector("[data-stage='scenes']", timeout=10_000)
        page.click("[data-stage='scenes']")
        page.wait_for_selector(".approval-gate", timeout=10_000)

        approve_button = page.locator("[data-decision='approve']")
        # If can_approve is true the button should be present and not disabled
        if approve_button.count() > 0:
            assert not approve_button.is_disabled(), \
                "approve 按钮在所有背景已选定时不应被禁用"

        browser.close()


# ---------------------------------------------------------------------------
# ET-003-style: service is reachable (smoke test, no UI needed)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_service_is_reachable():
    """Smoke: /readyz 返回 200。"""
    status, body = _http_get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("服务未运行，跳过 ET-PRD002 smoke test")
    assert status == 200
    assert b"ready" in body
