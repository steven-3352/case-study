import io
import json
import sqlite3
import zipfile
from datetime import datetime, timezone

import pytest
import yaml
from PIL import Image

from mv_platform.application import (
    ApplicationBlocked,
    ApplicationConflict,
    ApplicationError,
    ApplicationNotFound,
    ApplicationService,
)
from mv_platform.config import Settings
from mv_platform.domain import JobStatus
from mv_platform.domain.states import RuntimeState
from mv_platform.infrastructure import Database
from mvstudio.director.drafting import ModelResult


H1 = "sha256:" + "1" * 64


def write_image(path, color=(120, 90, 60)):
    Image.new("RGB", (24, 32), color).save(path)


def make_service(tmp_path, supervisor=None, initialize=True, semantic_port=None, semantic_model=None,
                 image_provider=None):
    settings = Settings()
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(
        settings, database, supervisor=supervisor, workspace_root=tmp_path,
        semantic_port=semantic_port, semantic_model=semantic_model,
        image_provider=image_provider,
    )
    if initialize:
        service.initialize()
    return service, database


def test_construction_has_no_side_effect_and_initialize_is_idempotent(tmp_path):
    service, database = make_service(tmp_path, initialize=False)
    assert not database.path.exists()
    assert not (tmp_path / "projects").exists()
    service.initialize()
    service.initialize()
    assert database.path.exists()
    assert (tmp_path / "projects").is_dir()
    assert (tmp_path / ".mvstudio" / "jobs").is_dir()


def test_initialize_rejects_symlink_escape_before_database_write(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (tmp_path / "projects").symlink_to(outside, target_is_directory=True)
    settings = Settings(project_root="projects")
    database = Database(tmp_path / settings.db_path)
    service = ApplicationService(settings, database, workspace_root=tmp_path)
    with pytest.raises(ApplicationBlocked):
        service.initialize()
    assert not database.path.exists()


def test_project_is_canonical_atomic_and_slug_participates_in_identity(tmp_path):
    service, _ = make_service(tmp_path)
    first = service.create_project("first", {"b": [2], "a": 1})
    same = service.create_project("first", {"a": 1, "b": [2]})
    second = service.create_project("second", {"a": 1, "b": [2]})
    assert same.project_id == first.project_id
    assert second.project_id != first.project_id
    brief_path = tmp_path / "projects" / "first" / "brief.json"
    assert brief_path.read_bytes() == b'{"a":1,"b":[2]}'
    assert not list(brief_path.parent.glob(".brief-*"))
    expected_directories = {
        "inputs/audio", "inputs/lyrics", "inputs/characters", "creative",
        "assets/source", "assets/generated", "outputs",
        ".mvstudio/jobs", ".mvstudio/work", ".mvstudio/logs",
    }
    assert expected_directories <= {
        path.relative_to(brief_path.parent).as_posix() for path in brief_path.parent.rglob("*") if path.is_dir()
    }
    with pytest.raises(TypeError):
        first.brief["x"] = 1


def test_project_idempotency_detects_disk_tampering_and_conflicts(tmp_path):
    service, _ = make_service(tmp_path)
    created = service.create_project("film", {"a": 1})
    brief_path = tmp_path / "projects" / "film" / "brief.json"
    brief_path.write_text('{"a":2}', encoding="utf-8")
    with pytest.raises(ApplicationConflict):
        service.create_project("film", {"a": 1})
    with pytest.raises(ApplicationConflict):
        service.create_project("film", {"a": 2}, project_id=created.project_id)


def test_browser_asset_import_classifies_files_and_preserves_xlsx_lyrics(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"audio")
    lyrics = tmp_path / "lyrics.xlsx"
    shared = (
        '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<si><t>歌词</t></si><si><t>起始时间</t></si><si><t>第一句</t></si><si><t>2</t></si></sst>'
    )
    sheet = (
        '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
        '<row><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row></sheetData></worksheet>'
    )
    with zipfile.ZipFile(lyrics, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)

    audio_result = service.import_project_asset(project.project_id, audio, "song.wav")
    lyric_result = service.import_project_asset(project.project_id, lyrics, "lyrics.xlsx")
    ignored = service.import_project_asset(project.project_id, audio, ".DS_Store")

    assert audio_result["kind"] == "audio"
    assert lyric_result["kind"] == "lyrics"
    assert lyric_result["relative_path"].endswith(".xlsx")
    lyric_path = tmp_path / "projects" / "film" / lyric_result["relative_path"]
    assert lyric_path.read_bytes() == lyrics.read_bytes()
    assert ignored == {"ignored": True, "name": ".DS_Store"}


def test_background_references_and_complete_keyframes_gate_shot_production(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "MV", "canvas": "9:16"})
    root = tmp_path / "projects" / "film"
    portrait = root / "inputs" / "characters" / "lead.png"
    portrait.write_bytes(b"portrait")
    (root / "creative" / "character_map.yaml").write_text(json.dumps({
        "characters": [{"id": "C01", "name": "主角", "source_asset":
                        "inputs/characters/lead.png", "director_function": "主视角"}],
    }), encoding="utf-8")
    (root / "creative" / "story_framework.yaml").write_text(json.dumps({
        "status": "draft_self_generated", "premise": "测试故事", "sections": [],
        "approval_required": True,
    }), encoding="utf-8")
    shots = [{
        "id": shot_id, "time": [index * 2, index * 2 + 2], "characters": ["C01"],
        "lyric": {"text": "歌词"}, "composition": {"shot_size": "full"},
        "first_frame": "主角站在戏台中央", "assets": {
            "use": ["inputs/characters/lead.png"], "missing": [],
        },
    } for index, shot_id in enumerate(("S001", "S002"))]
    (root / "creative" / "visual_score.yaml").write_text(json.dumps({
        "status": "draft_self_generated", "shots": shots,
    }), encoding="utf-8")

    background_source = tmp_path / "stage.png"
    write_image(background_source)
    imported = service.import_project_asset(
        project.project_id, background_source, "戏台.png", kind_hint="backgrounds",
    )
    assert imported["kind"] == "backgrounds"
    workflow = service.bind_shot_background(
        project.project_id, "S001", imported["relative_path"],
    )
    intake = next(item for item in workflow["stages"] if item["id"] == "intake")
    assert intake["data"]["backgrounds"][0]["path"] == imported["relative_path"]
    storyboard = next(item for item in workflow["stages"] if item["id"] == "storyboard")
    assert storyboard["data"]["shots"][0]["background"]["status"] == "reference_bound"
    assert storyboard["data"]["shots"][1]["background"]["status"] == "planned_for_generation"
    assert service.get_project_file(project.project_id, imported["relative_path"]).is_file()

    service.record_workflow_decision(project.project_id, "story", "approve")
    service.record_workflow_decision(project.project_id, "storyboard", "approve")
    _dp = root / "creative" / "workflow-decisions.json"
    _d = json.loads(_dp.read_text()) if _dp.exists() else {}
    _d["scenes"] = {"action": "approve", "note": "", "decided_at": datetime.now(timezone.utc).isoformat(), "actor": "local_user"}
    _dp.write_text(json.dumps(_d, ensure_ascii=False))
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    write_image(first, (100, 60, 30))
    write_image(second, (30, 70, 100))
    workflow = service.import_shot_keyframe(project.project_id, "S001", first, "候选一.png")
    keyframes = next(item for item in workflow["stages"] if item["id"] == "keyframes")
    assert keyframes["status"] == "pending"
    assert keyframes["data"]["selected_count"] == 1
    assert not keyframes["can_approve"]
    assert next(item for item in workflow["stages"] if item["id"] == "shots")["status"] == "locked"

    workflow = service.import_shot_keyframe(project.project_id, "S002", second, "候选二.png")
    keyframes = next(item for item in workflow["stages"] if item["id"] == "keyframes")
    assert keyframes["status"] == "awaiting_approval"
    assert keyframes["data"]["selected_count"] == 2
    assert keyframes["can_approve"]
    approved = service.record_workflow_decision(project.project_id, "keyframes", "approve")
    assert next(item for item in approved["stages"] if item["id"] == "shots")["status"] == "pending"
    selected = keyframes["data"]["shots"][0]["selected_keyframe"]
    assert service.get_project_file(project.project_id, selected).is_file()


def test_shot_reference_paths_are_project_scoped(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "MV"})
    root = tmp_path / "projects" / "film"
    (root / "creative" / "visual_score.yaml").write_text(
        json.dumps({"shots": [{"id": "S001"}]}), encoding="utf-8",
    )
    with pytest.raises(ApplicationConflict):
        service.bind_shot_background(project.project_id, "S001", "../outside.png")
    with pytest.raises(ApplicationNotFound):
        service.bind_shot_background(
            project.project_id, "S001", "inputs/backgrounds/missing.png",
        )
    bad = tmp_path / "candidate.txt"
    bad.write_text("not an image", encoding="utf-8")
    with pytest.raises(ApplicationConflict):
        service.import_shot_keyframe(project.project_id, "S001", bad, "candidate.txt")
    disguised = tmp_path / "candidate.png"
    disguised.write_text("not an image", encoding="utf-8")
    with pytest.raises(ApplicationConflict, match="reference image is invalid"):
        service.import_shot_keyframe(project.project_id, "S001", disguised, "candidate.png")
    with pytest.raises(ApplicationConflict, match="reference image is invalid"):
        service.import_project_asset(
            project.project_id, disguised, "background.png", kind_hint="backgrounds",
        )


def test_gpt_image_background_and_keyframe_use_full_director_context_and_bill(tmp_path):
    class TranslatingPort:
        def __init__(self):
            self.tasks = []

        def run(self, task):
            self.tasks.append(task)
            return ModelResult({"english_prompt": "production prompt"}, 120, 30, 20)

    class ImageProvider:
        model = "gpt-image-2"

        def __init__(self):
            self.calls = []

        def generate(self, prompt, references=(), size=""):
            self.calls.append({"prompt": prompt, "references": tuple(references), "size": size})
            output = io.BytesIO()
            Image.new("RGB", (64, 96), (80, 70, 55)).save(output, format="PNG")
            return output.getvalue()

    translator = TranslatingPort()
    image_provider = ImageProvider()
    service, _ = make_service(
        tmp_path, semantic_port=translator, semantic_model="semantic-model",
        image_provider=image_provider,
    )
    project = service.create_project("generated-frames", {"title": "青衣", "canvas": "9:16"})
    root = tmp_path / "projects" / project.slug
    portrait = root / "inputs" / "characters" / "lead.png"
    write_image(portrait)
    (root / "creative" / "character_map.yaml").write_text(json.dumps({
        "characters": [{"id": "C01", "name": "锦礼", "source_asset":
                        "inputs/characters/lead.png", "director_function": "守望者",
                        "traits": ["青衣水袖", "克制坚定"]}],
    }), encoding="utf-8")
    (root / "creative" / "music_map.yaml").write_text(json.dumps({
        "sections": [{"id": "verse", "emotion": "含蓄哀伤", "energy": 3}],
    }), encoding="utf-8")
    (root / "creative" / "story_framework.yaml").write_text(json.dumps({
        "premise": "戏台内外的身份交错", "sections": [{"id": "verse", "emotion": "忍而不发"}],
    }), encoding="utf-8")
    (root / "creative" / "visual_score.yaml").write_text(json.dumps({
        "shots": [
            {"id": "S000", "last_frame": "水袖从画面左侧掠过"},
            {"id": "S001", "time": [2, 4], "section": "verse", "energy": 3,
             "characters": ["C01"], "purpose": "身份揭示", "lyric": {"text": "我本戏中人"},
             "composition": {"shot_size": "full", "arrangement": "人物位于右侧三分线"},
             "primary_action": "抬眼看向镜外", "first_frame": "空戏台留出右侧人物位",
             "last_frame": "灯影收拢到水袖", "transition_out": {"type": "action_match"}},
            {"id": "S002", "first_frame": "水袖落在镜前"},
        ],
    }), encoding="utf-8")
    service.record_workflow_decision(project.project_id, "story", "approve")

    workflow = service.generate_shot_background(project.project_id, "S001")
    storyboard = next(item for item in workflow["stages"] if item["id"] == "storyboard")
    shot = next(item for item in storyboard["data"]["shots"] if item["id"] == "S001")
    assert shot["background"]["reference"].startswith("assets/generated/backgrounds/S001-")
    context = translator.tasks[0].payload["director_context"]
    assert context["shot"]["lyric"]["text"] == "我本戏中人"
    assert context["characters"][0]["traits"] == ["青衣水袖", "克制坚定"]
    assert context["continuity"] == {
        "previous": "水袖从画面左侧掠过", "next": "水袖落在镜前",
    }
    assert image_provider.calls[0]["references"] == (portrait,)
    assert image_provider.calls[0]["size"] == "1024x1536"

    service.record_workflow_decision(project.project_id, "storyboard", "approve")
    _dp2 = root / "creative" / "workflow-decisions.json"
    _d2 = json.loads(_dp2.read_text()) if _dp2.exists() else {}
    _d2["scenes"] = {"action": "approve", "note": "", "decided_at": datetime.now(timezone.utc).isoformat(), "actor": "local_user"}
    _dp2.write_text(json.dumps(_d2, ensure_ascii=False))
    workflow = service.generate_shot_keyframe(project.project_id, "S001")
    keyframes = next(item for item in workflow["stages"] if item["id"] == "keyframes")
    shot = next(item for item in keyframes["data"]["shots"] if item["id"] == "S001")
    assert shot["selected_keyframe"].startswith("assets/generated/keyframes/S001-")
    assert image_provider.calls[1]["references"][0].name.startswith("S001-")
    assert image_provider.calls[1]["references"][1] == portrait
    costs = service.get_project_costs(project.project_id)
    assert costs["by_type"]["image"] == 1.0
    assert [item["metadata"]["shot_id"] for item in costs["entries"]].count("S001") == 4


def test_project_rejects_non_json_and_project_symlink(tmp_path):
    service, _ = make_service(tmp_path)
    with pytest.raises(ApplicationConflict):
        service.create_project("bad", {"x": object()})
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "projects" / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ApplicationBlocked):
        service.create_project("linked", {"x": 1})


def test_project_workflow_surfaces_storyboard_and_requires_explicit_user_gates(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "MV", "canvas": "9:16"})
    root = tmp_path / "projects" / "film"
    portrait = root / "inputs" / "characters" / "lead.png"
    portrait.write_bytes(b"image")
    (root / "creative" / "character_map.yaml").write_text(json.dumps({
        "characters": [{"id": "C01", "name": "Lead", "source_asset":
                        "inputs/characters/lead.png", "director_function": "Singer"}],
    }), encoding="utf-8")
    (root / "creative" / "story_framework.yaml").write_text(json.dumps({
        "status": "draft_self_generated", "premise": "A test story", "sections": [],
        "approval_required": True,
    }), encoding="utf-8")
    (root / "creative" / "visual_score.yaml").write_text(json.dumps({
        "status": "draft_self_generated", "shots": [{
            "id": "S001", "time": [0, 2], "characters": ["C01"],
            "lyric": {"text": "line"}, "composition": {"shot_size": "full"},
            "assets": {"use": ["inputs/characters/lead.png"], "missing": []},
        }],
    }), encoding="utf-8")

    workflow = service.get_project_workflow(project.project_id)
    assert len(workflow["stages"]) == 10  # PRD-007B added scene_planning stage
    assert workflow["current_stage_id"] == "story"
    assert next(item for item in workflow["stages"] if item["id"] == "story")["can_approve"]
    storyboard = next(item for item in workflow["stages"] if item["id"] == "storyboard")
    assert storyboard["status"] == "preview_only"
    assert storyboard["data"]["shots"][0]["characters"][0]["name"] == "Lead"
    assert service.get_project_file(project.project_id, "inputs/characters/lead.png") == portrait

    approved = service.record_workflow_decision(project.project_id, "story", "approve", "OK")
    assert approved["current_stage_id"] == "storyboard"
    storyboard = next(item for item in approved["stages"] if item["id"] == "storyboard")
    assert storyboard["status"] == "awaiting_approval"
    assert storyboard["can_approve"]


def test_character_asset_removal_is_recoverable_and_invalidates_workflow(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "MV"})
    portrait = tmp_path / "projects" / "film" / "inputs" / "characters" / "lead.png"
    portrait.write_bytes(b"image")
    relative = "inputs/characters/lead.png"

    workflow = service.remove_project_character_asset(
        project.project_id, relative, "lead.png",
    )
    assert not portrait.exists()
    intake = next(item for item in workflow["stages"] if item["id"] == "intake")
    assert intake["data"]["assets_changed"] is False
    music = next(item for item in workflow["stages"] if item["id"] == "music")
    assert music["status"] == "locked"
    assert intake["data"]["removed_characters"][0]["original_path"] == relative
    trash = tmp_path / "projects" / "film" / intake["data"]["removed_characters"][0]["trash_path"]
    assert trash.read_bytes() == b"image"
    with pytest.raises(ApplicationNotFound):
        service.get_project_file(project.project_id, relative)
    with pytest.raises(ApplicationConflict):
        service.remove_project_character_asset(project.project_id, relative, "wrong.png")

    restored = service.restore_project_character_asset(project.project_id, relative)
    assert portrait.read_bytes() == b"image"
    assert not trash.exists()
    intake = next(item for item in restored["stages"] if item["id"] == "intake")
    assert intake["data"]["removed_characters"] == []


def test_completed_intake_exposes_music_as_the_next_runnable_stage(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "测试项目"})
    refs = ("inputs/audio/song.wav", "inputs/lyrics/song.lrc", "inputs/characters/lead.png")
    job = service.submit_job(project.project_id, "analyze", H1, input_refs=refs)
    now = datetime.now(timezone.utc)
    status = service.repository.get_status(job.job_id)
    service.repository.set_status(
        status.transition(RuntimeState.RUNNING, now).transition(RuntimeState.SUCCEEDED, now)
    )
    manifest = tmp_path / ".mvstudio" / "jobs" / job.job_id / "intake" / "intake_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "audio": {"path": "inputs/audio/song.wav"},
        "lyrics": {"path": "inputs/lyrics/song.lrc"},
        "characters": [{"path": "inputs/characters/lead.png"}],
    }), encoding="utf-8")

    workflow = service.get_project_workflow(project.project_id)
    music = next(item for item in workflow["stages"] if item["id"] == "music")
    assert workflow["current_stage_id"] == "music"
    assert workflow["blocking_reason"] == "请在当前步骤开始制作"
    assert music["status"] == "pending"


def test_new_intake_inputs_invalidate_stale_director_outputs(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "测试项目"})
    old_refs = ("inputs/audio/old.wav", "inputs/lyrics/old.lrc", "inputs/characters/old.png")
    director = service.submit_job(project.project_id, "animatic", H1, input_refs=old_refs)
    now = datetime.now(timezone.utc)
    director_status = service.repository.get_status(director.job_id)
    service.repository.set_status(
        director_status.transition(RuntimeState.RUNNING, now).transition(RuntimeState.SUCCEEDED, now)
    )
    root = tmp_path / "projects" / "film"
    (root / "creative" / "music_map.yaml").write_text(
        json.dumps({"duration": 30, "sections": []}), encoding="utf-8",
    )
    (root / "creative" / "story_framework.yaml").write_text(
        json.dumps({"status": "draft_self_generated", "sections": []}), encoding="utf-8",
    )
    (root / "creative" / "visual_score.yaml").write_text(
        json.dumps({"status": "draft_self_generated", "shots": []}), encoding="utf-8",
    )
    (root / "creative" / "workflow-decisions.json").write_text(json.dumps({
        "story": {"action": "approve", "decided_at": now.isoformat()},
        "storyboard": {"action": "approve", "decided_at": now.isoformat()},
    }), encoding="utf-8")

    new_refs = ("inputs/audio/new.wav", "inputs/lyrics/new.xlsx", "inputs/characters/new.png")
    intake_job = service.submit_job(project.project_id, "analyze", H1, input_refs=new_refs)
    intake_status = service.repository.get_status(intake_job.job_id)
    later = datetime.now(timezone.utc)
    service.repository.set_status(
        intake_status.transition(RuntimeState.RUNNING, later).transition(RuntimeState.SUCCEEDED, later)
    )
    manifest = tmp_path / ".mvstudio" / "jobs" / intake_job.job_id / "intake" / "intake_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "audio": {"path": new_refs[0]},
        "lyrics": {"path": new_refs[1]},
        "characters": [{"path": new_refs[2]}],
    }), encoding="utf-8")

    workflow = service.get_project_workflow(project.project_id)
    music = next(item for item in workflow["stages"] if item["id"] == "music")
    story = next(item for item in workflow["stages"] if item["id"] == "story")
    storyboard = next(item for item in workflow["stages"] if item["id"] == "storyboard")
    assert workflow["current_stage_id"] == "music"
    assert workflow["blocking_reason"] == "新素材已导入，需要重新分析音乐、歌词、故事和分镜"
    assert music["status"] == "pending"
    assert music["data"]["inputs_changed"] is True
    assert story["status"] == "revision"
    assert story["can_approve"] is False
    assert storyboard["status"] != "approved"


def test_reordered_input_refs_do_not_invalidate_director_outputs(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "测试项目"})
    refs = ("inputs/audio/song.wav", "inputs/lyrics/song.xlsx", "inputs/characters/lead.png")
    now = datetime.now(timezone.utc)

    intake_job = service.submit_job(
        project.project_id, "analyze", H1, input_refs=(refs[2], refs[0], refs[1])
    )
    intake_status = service.repository.get_status(intake_job.job_id)
    service.repository.set_status(
        intake_status.transition(RuntimeState.RUNNING, now).transition(RuntimeState.SUCCEEDED, now)
    )
    manifest = tmp_path / ".mvstudio" / "jobs" / intake_job.job_id / "intake" / "intake_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "audio": {"path": refs[0]},
        "lyrics": {"path": refs[1]},
        "characters": [{"path": refs[2]}],
    }), encoding="utf-8")

    director = service.submit_job(project.project_id, "animatic", H1, input_refs=refs)
    director_status = service.repository.get_status(director.job_id)
    service.repository.set_status(
        director_status.transition(RuntimeState.RUNNING, now).transition(RuntimeState.SUCCEEDED, now)
    )
    root = tmp_path / "projects" / "film" / "creative"
    (root / "music_map.yaml").write_text(
        json.dumps({"duration": 30, "sections": []}), encoding="utf-8",
    )
    (root / "story_framework.yaml").write_text(
        json.dumps({"status": "draft_self_generated", "sections": []}), encoding="utf-8",
    )

    workflow = service.get_project_workflow(project.project_id)
    music = next(item for item in workflow["stages"] if item["id"] == "music")
    story = next(item for item in workflow["stages"] if item["id"] == "story")
    assert music["data"]["inputs_changed"] is False
    assert music["status"] == "completed"
    assert story["status"] == "awaiting_approval"


def test_prompt_settings_include_chinese_system_and_task_prompts(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "MV"})
    prompts = service.get_project_prompts(project.project_id)
    assert "lyrics.semantic_segment.requested" in prompts
    assert "system::lyrics.semantic_segment.requested" in prompts
    assert "prompt.translate_requested" in prompts
    assert "音乐叙事分析师" in prompts["system::lyrics.semantic_segment.requested"]
    prompts["lyrics.semantic_segment.requested"] = "中文任务提示词"
    saved = service.update_project_prompts(project.project_id, prompts)
    assert saved["lyrics.semantic_segment.requested"] == "中文任务提示词"


def test_user_facing_chinese_is_editable_and_keeps_english_execution_copy(tmp_path):
    from mvstudio.director.drafting import ModelResult

    class TranslationPort:
        def run(self, task):
            prefix = "中文：" if task.payload["target_language"] == "zh-CN" else "English: "
            return ModelResult({"translations": [
                {"field_id": item["field_id"], "translated_text": prefix + item["source_text"]}
                for item in task.payload["items"]
            ]}, 120, 60, 10)

    service, _ = make_service(
        tmp_path, semantic_port=TranslationPort(), semantic_model="translation-test",
    )
    project = service.create_project("film", {"title": "音乐视频"})
    root = tmp_path / "projects" / "film" / "creative"
    (root / "story_framework.yaml").write_text(
        "premise: An English story\nsections: []\n", encoding="utf-8",
    )

    localized = service.localize_project_content(project.project_id)
    story = next(stage for stage in localized["stages"] if stage["id"] == "story")
    assert story["data"]["story"]["premise"] == "中文：An English story"

    updated = service.update_project_display_content(
        project.project_id, {"story.premise": "一段新的中文故事"},
    )
    story = next(stage for stage in updated["stages"] if stage["id"] == "story")
    assert story["data"]["story"]["premise"] == "一段新的中文故事"
    internal = yaml.safe_load((root / "story_framework.yaml").read_text(encoding="utf-8"))
    assert internal["premise"] == "English: 一段新的中文故事"
    entries = service.get_project_costs(project.project_id)["entries"]
    assert {item["step_id"] for item in entries} == {
        "content.localize_requested", "content.translate_requested",
    }


def test_localization_preserves_existing_chinese_names_without_model_call(tmp_path):
    class RejectingPort:
        def run(self, _task):
            raise AssertionError("Chinese source fields must not be translated again")

    service, _ = make_service(
        tmp_path, semantic_port=RejectingPort(), semantic_model="translation-test",
    )
    project = service.create_project("film", {"title": "音乐视频"})
    root = tmp_path / "projects" / "film" / "creative"
    (root / "story_framework.yaml").write_text(
        "premise: 锦礼与安玥在戏台重逢\nsections: []\n", encoding="utf-8",
    )

    localized = service.localize_project_content(project.project_id)
    story = next(stage for stage in localized["stages"] if stage["id"] == "story")
    assert story["data"]["story"]["premise"] == "锦礼与安玥在戏台重逢"
    assert service.get_project_costs(project.project_id)["entries"] == []


def test_model_audit_recovery_restores_each_repeated_batch_cost_once(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"title": "音乐视频"})
    job = service.submit_job(project.project_id, "animatic", H1)
    metadata = {
        "model": "fixture", "event_type": "visual_score.creative_draft_requested",
    }
    service.record_llm_cost(
        project.project_id, job.job_id, "visual_score.creative_draft_requested",
        100, 0, 50, metadata,
    )
    audit_path = tmp_path / ".mvstudio" / "jobs" / job.job_id / "creative" / "model_audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps({"calls": [
        {
            "event_type": "visual_score.creative_draft_requested",
            "model": "fixture", "usage": {"input_tokens": 100, "output_tokens": 50},
        },
        {
            "event_type": "visual_score.creative_draft_requested",
            "model": "fixture", "usage": {"input_tokens": 110, "output_tokens": 60},
        },
        {
            "event_type": "visual_score.creative_draft_requested",
            "model": "fixture", "usage": {"input_tokens": 120, "output_tokens": 70},
        },
    ]}), encoding="utf-8")

    service._recover_model_audit_costs(project.project_id, job.job_id)
    service._recover_model_audit_costs(project.project_id, job.job_id)

    entries = [
        item for item in service.get_project_costs(project.project_id)["entries"]
        if item["step_id"] == "visual_score.creative_draft_requested"
    ]
    assert len(entries) == 3
    assert sorted(item["output_tokens"] for item in entries) == [50, 60, 70]
    recovered = [item for item in entries if item["metadata"].get("recovered_from_audit")]
    assert sorted(item["metadata"]["invocation"] for item in recovered) == [2, 3]


def test_job_submission_is_deterministic_and_idempotency_conflicts(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    first = service.submit_job(project.project_id, "analyze", H1, input_refs=("assets/a.png",))
    same = service.submit_job(project.project_id, "analyze", H1, input_refs=("assets/a.png",))
    assert same.job_id == first.job_id
    assert same.canonical_job_digest == first.canonical_job_digest
    with pytest.raises(ApplicationConflict):
        service.submit_job(project.project_id, "render", H1, idempotency_key=first.job_spec.idempotency_key)
    for kwargs in ({"input_refs": "assets/a.png"}, {"input_digest": "bad"}, {"operation": "bad"}):
        request = {"project_id": project.project_id, "operation": "analyze", "input_digest": H1}
        request.update(kwargs)
        with pytest.raises(ApplicationConflict):
            service.submit_job(**request)


def test_job_and_status_insert_roll_back_together(tmp_path):
    service, database = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    with database.connect() as connection:
        connection.execute("CREATE TRIGGER reject_status BEFORE INSERT ON job_status BEGIN SELECT RAISE(ABORT, 'no status'); END")
    with pytest.raises(ApplicationConflict):
        service.submit_job(project.project_id, "analyze", H1)
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0


class RecordingSupervisor:
    def __init__(self):
        self.service = None
        self.started = []
        self.cancelled = []
        self.recovered = False
        self.stopped = False

    def submit(self, job_id, executor, executor_input):
        inspection = self.service.inspect_job(job_id)
        assert inspection.status.runtime_state is RuntimeState.QUEUED
        self.started.append((job_id, executor, executor_input))
        return inspection

    def cancel(self, job_id, grace):
        self.cancelled.append((job_id, grace))
        status = self.service.repository.get_status(job_id)
        self.service.repository.set_status(status.transition(RuntimeState.CANCELLED, datetime.now(timezone.utc)))

    def recover(self): self.recovered = True
    def shutdown(self): self.stopped = True


def test_auto_start_occurs_after_atomic_persistence_and_delegates(tmp_path):
    supervisor = RecordingSupervisor()
    service, _ = make_service(tmp_path, supervisor)
    supervisor.service = service
    project = service.create_project("film", {"x": 1})
    result = service.submit_job(project.project_id, "analyze", H1, auto_start=True, executor_input={"steps": 1})
    assert result.job_id == supervisor.started[0][0]
    service.recover()
    service.shutdown()
    assert supervisor.recovered and supervisor.stopped


def test_inspect_events_artifacts_cursor_and_missing(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    job = service.submit_job(project.project_id, "analyze", H1)
    inspection = service.inspect_job(job.job_id)
    assert inspection.events == () and inspection.artifacts == ()
    assert inspection.job_digest == job.canonical_job_digest
    for value in (True, -1, 1.5, "1"):
        with pytest.raises(ApplicationConflict):
            service.list_events(job.job_id, value)
    with pytest.raises(ApplicationNotFound):
        service.inspect_job("missing")


def test_no_supervisor_start_recover_shutdown_are_blocked(tmp_path):
    service, _ = make_service(tmp_path)
    for call in (lambda: service.start_job("missing"), service.recover, service.shutdown):
        with pytest.raises(ApplicationBlocked):
            call()


def test_queued_cancel_status_and_event_are_atomic(tmp_path):
    service, database = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    job = service.submit_job(project.project_id, "analyze", H1)
    with database.connect() as connection:
        connection.execute("CREATE TRIGGER reject_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'no event'); END")
    with pytest.raises(ApplicationError):
        service.cancel_job(job.job_id)
    assert service.inspect_job(job.job_id).status.runtime_state is RuntimeState.QUEUED
    assert service.list_events(job.job_id) == ()


def test_terminal_cancel_is_idempotent_and_does_not_overwrite_success(tmp_path):
    service, _ = make_service(tmp_path)
    project = service.create_project("film", {"x": 1})
    cancelled = service.submit_job(project.project_id, "analyze", H1)
    first = service.cancel_job(cancelled.job_id)
    second = service.cancel_job(cancelled.job_id)
    assert first.status.runtime_state is second.status.runtime_state is RuntimeState.CANCELLED
    assert len(service.list_events(cancelled.job_id)) == 1

    success = service.submit_job(project.project_id, "render", H1)
    status = service.repository.get_status(success.job_id)
    service.repository.set_status(status.transition(RuntimeState.RUNNING, datetime.now(timezone.utc)).transition(RuntimeState.SUCCEEDED, datetime.now(timezone.utc)))
    assert service.cancel_job(success.job_id).status.runtime_state is RuntimeState.SUCCEEDED
