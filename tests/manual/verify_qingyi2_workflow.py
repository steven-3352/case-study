"""Real Chromium acceptance for qingyi2's XLSX-driven planning workflow."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8792"
PROJECT_ID = "project-3531246c03670d497567f9eae3ddf2e6"
MATERIALS = Path("/private/tmp/qingyi2-browser-materials")
OUTPUT = Path("/private/tmp/qingyi2-director-contract.png")
STORYBOARD_OUTPUT = Path("/private/tmp/qingyi2-new-storyboard.png")
PAGINATION_OUTPUT = Path("/private/tmp/qingyi2-record-pagination.png")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto(URL, wait_until="networkidle", timeout=30_000)

    project = page.locator(f'button[data-project="{PROJECT_ID}"]')
    project.wait_for(state="visible", timeout=20_000)
    project.click()
    page.locator('[data-stage="music"]').click()
    page.get_by_role("heading", name="音乐与歌词", exact=True).wait_for()
    page.locator(".director-row").first.wait_for(state="visible", timeout=30_000)
    assert page.locator(".director-row").count() == 11
    assert "人物与起止时间是硬约束" in page.locator(".director-contract").inner_text()
    cast_cells = page.locator(".director-row strong").all_inner_texts()
    assert any("锦礼" in value and "安玥" in value for value in cast_cells)
    assert "29.0 - 36.0 秒" in page.locator(".director-contract").inner_text()
    story_step = page.locator('[data-stage="story"]')
    story_step.wait_for(state="visible", timeout=300_000)
    if "awaiting_approval" not in (story_step.get_attribute("class") or ""):
        resume_button = page.locator("[data-resume-planning]")
        if resume_button.count() == 1 and resume_button.is_visible():
            resume_button.click()
        else:
            run_button = page.locator("[data-run-planning]")
            run_button.wait_for(state="visible", timeout=10_000)
            if run_button.is_enabled():
                run_button.click()
        page.wait_for_function(
            """() => {
              const story = document.querySelector('[data-stage="story"]');
              return story && story.classList.contains('awaiting_approval');
            }""",
            timeout=900_000,
        )
    page.locator('[data-stage="music"]').click()
    page.get_by_role("heading", name="音乐与歌词", exact=True).wait_for()
    assert page.locator(".planning-run").count() == 0
    page.screenshot(path=str(OUTPUT), full_page=True)

    page.locator('[data-stage="storyboard"]').click()
    page.get_by_role("heading", name="分镜工作台", exact=True).wait_for()
    page.locator(".shot-card").first.wait_for(state="visible", timeout=30_000)
    shot_count = page.locator(".shot-card").count()
    assert shot_count >= 20
    metric_text = page.locator(".storyboard-metrics").inner_text()
    assert "最长镜头" in metric_text and "符合短镜密度要求" in metric_text
    assert "Excel 第 6 行" in page.locator(".shot-list").inner_text()
    page.locator(".prompt-settings > summary").click()
    assert page.locator(".prompt-card").count() == 2
    assert page.locator("[data-prompt-system]").count() == 2
    assert page.locator("[data-prompt-task]").count() == 2
    review_system = page.locator(
        '[data-prompt-system="visual_score.quality_review_requested"]'
    ).input_value()
    review_task = page.locator(
        '[data-prompt-task="visual_score.quality_review_requested"]'
    ).input_value()
    assert "不得以" in review_system and "符合门禁" in review_system
    assert "提升三档" in review_task
    page.screenshot(path=str(STORYBOARD_OUTPUT), full_page=True)

    page.locator(".operations-drawer > summary").click()
    assert page.locator("#job-list .job-item").count() == 10
    assert page.locator("#cost-ledger .cost-row").count() == 10
    job_first_page = page.locator("#job-list .job-item code").first.inner_text()
    page.locator('[data-page-kind="jobs"][aria-label="下一页"]').click()
    assert "第 2 /" in page.locator('#job-list .pager span').inner_text()
    assert page.locator("#job-list .job-item code").first.inner_text() != job_first_page
    cost_first_page = page.locator("#cost-ledger .cost-row").first.inner_text()
    page.locator('[data-page-kind="costs"][aria-label="下一页"]').click()
    assert "第 2 /" in page.locator('#cost-ledger .pager span').inner_text()
    assert page.locator("#cost-ledger .cost-row").first.inner_text() != cost_first_page
    assert "undefined" not in page.locator("#cost-ledger").inner_text()
    assert "输入 " in page.locator("#cost-ledger .cost-row").first.inner_text()
    page.locator(".operations-drawer").scroll_into_view_if_needed()
    page.screenshot(path=str(PAGINATION_OUTPUT), full_page=False)

    result = {
        "project_id": PROJECT_ID,
        "director_rows": 10,
        "shot_count": shot_count,
        "storyboard_metrics": metric_text,
        "console_errors": errors,
    }
    assert not errors, errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    browser.close()

print(OUTPUT)
print(STORYBOARD_OUTPUT)
print(PAGINATION_OUTPUT)
