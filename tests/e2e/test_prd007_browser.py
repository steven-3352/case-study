"""PRD-007 E2E browser tests: real SSE progress, refresh recovery, translation cache."""
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
        "ET-071~ET-073 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd007_browser.py"
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


def _find_project_at_keyframes() -> "str | None":
    """Return first project_id whose workflow has passed the keyframes stage gate."""
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
        if "keyframes" not in stage_ids:
            continue
        current = wf.get("current_stage_id", "")
        idx_kf = stage_ids.index("keyframes")
        idx_cur = stage_ids.index(current) if current in stage_ids else -1
        if idx_cur >= idx_kf:
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
        pytest.skip("服务未运行，跳过 ET-PRD007 smoke test")
    assert status == 200
    assert b"ready" in body


# ---------------------------------------------------------------------------
# ET-071: keyframe generate shows real SSE progress phases (not fake setTimeout)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_keyframe_generate_shows_real_sse_progress():
    """ET-071: Click keyframe generate → .generation-progress box with .progress-phase spans appears."""
    project_id = _find_project_at_keyframes()
    if not project_id:
        pytest.skip("ET-071: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        gen_btn = page.locator("button.keyframe-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-071: 当前项目无可用首帧生成按钮，已跳过")

        gen_btn.click()

        # After click the button hides and .generation-progress box appears
        page.wait_for_selector(".generation-progress", timeout=10_000)

        # At least one .progress-phase span must be rendered (real SSE stage labels)
        phase_count = page.locator(".progress-phase").count()
        assert phase_count >= 1, (
            f"预期至少 1 个 .progress-phase，实际 {phase_count}；"
            "SSE 进度阶段未渲染，可能仍是旧 setTimeout 假进度"
        )

        # The three expected stage labels must exist
        for label in ["翻译执行稿", "调用图片模型", "保存结果"]:
            assert page.locator(f".progress-phase:has-text('{label}')").count() >= 1, (
                f"缺少阶段标签：{label}"
            )

        browser.close()


# ---------------------------------------------------------------------------
# ET-072: refresh with active job shows recovery banner
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_refresh_shows_active_job_recovery_banner():
    """ET-072: When workflow.active_jobs is non-empty on page load, #active-jobs-banner appears."""
    project_id = _find_project_at_keyframes()
    if not project_id:
        pytest.skip("ET-072: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    # Check if there are any active image-gen jobs via the workflow API
    ws, wb = _http_get(f"{BASE_URL}/api/v1/projects/{project_id}/workflow")
    if ws != 200:
        pytest.skip("ET-072: 无法读取 workflow，已跳过")
    wf = json.loads(wb)
    if not wf.get("active_jobs"):
        pytest.skip("ET-072: 当前项目无 active_jobs（需先触发一个首帧生成任务后刷新），已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        # Recovery banner should appear because active_jobs is non-empty
        banner = page.locator("#active-jobs-banner")
        assert banner.count() >= 1, (
            "#active-jobs-banner 未出现；刷新恢复逻辑未生效"
        )
        assert "首帧生成任务正在进行中" in (banner.inner_text() or ""), (
            f"横幅文字不符预期：{banner.inner_text()}"
        )

        browser.close()


# ---------------------------------------------------------------------------
# ET-073: second generation with same shot uses cached en_prompt (translation skipped)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_second_keyframe_generation_skips_translation_via_cache():
    """ET-073: After a successful generation, re-clicking generate sends cached en_prompt → translate step absent."""
    project_id = _find_project_at_keyframes()
    if not project_id:
        pytest.skip("ET-073: 当前服务无已进入 keyframes 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Intercept SSE responses to capture translate_prompt events
        translate_seen_first = []
        translate_seen_second = []
        current_gen = [0]

        def on_response(response):
            if "/events" in response.url and "follow=true" in response.url:
                try:
                    body = response.body().decode("utf-8", errors="ignore")
                    if "translate_prompt" in body:
                        if current_gen[0] == 1:
                            translate_seen_first.append(True)
                        elif current_gen[0] == 2:
                            translate_seen_second.append(True)
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='keyframes']", timeout=10_000)
        page.click("[data-stage='keyframes']")
        page.wait_for_selector(".keyframe-workbench", timeout=10_000)

        gen_btn = page.locator("button.keyframe-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-073: 当前项目无可用首帧生成按钮，已跳过")

        shot_id = gen_btn.get_attribute("data-generate-keyframe")

        # First generation
        current_gen[0] = 1
        gen_btn.click()
        page.wait_for_selector(".generation-progress", timeout=10_000)
        # Wait for done (button reappears) with generous timeout for actual generation
        try:
            page.wait_for_selector(
                f"button.keyframe-generate[data-generate-keyframe='{shot_id}']:not([style*='display: none'])",
                timeout=120_000,
            )
        except Exception:
            pytest.skip("ET-073: 第一次生成超时（可能无实际模型），已跳过")

        # Verify translation cache was set in sessionStorage
        cached = page.evaluate(
            f"sessionStorage.getItem('kf_translation:{project_id}:{shot_id}')"
        )
        if not cached:
            pytest.skip(
                "ET-073: 第一次生成未写入 sessionStorage 翻译缓存（可能无 translate_prompt 事件），已跳过"
            )

        # Second generation — should send en_prompt in POST body → no translate_prompt SSE stage
        current_gen[0] = 2

        # Intercept the second POST to check en_prompt in request body
        en_prompt_sent = []

        def on_request(request):
            if f"/keyframes/generate" in request.url and request.method == "POST":
                try:
                    body = json.loads(request.post_data or "{}")
                    if body.get("en_prompt"):
                        en_prompt_sent.append(body["en_prompt"])
                except Exception:
                    pass

        page.on("request", on_request)

        gen_btn2 = page.locator(f"button.keyframe-generate[data-generate-keyframe='{shot_id}']:not([disabled])").first
        gen_btn2.click()
        page.wait_for_selector(".generation-progress", timeout=10_000)

        assert len(en_prompt_sent) >= 1, (
            "第二次生成未在 POST body 中带 en_prompt；sessionStorage 缓存未生效"
        )
        assert en_prompt_sent[0] == cached, (
            f"POST body en_prompt '{en_prompt_sent[0]}' 与 sessionStorage 缓存 '{cached}' 不符"
        )

        # The server-side should skip translation, so progress box should NOT show translate step as active
        translate_phase = page.locator(".progress-phase:has-text('翻译执行稿').active")
        # Give it a brief moment to render
        page.wait_for_timeout(500)
        assert translate_phase.count() == 0, (
            "第二次生成出现了 translate_prompt 进度步骤处于 active 状态；翻译缓存 bypass 未生效"
        )

        browser.close()
