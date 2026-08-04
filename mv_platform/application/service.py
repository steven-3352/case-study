import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import tempfile
import threading
import uuid
import zipfile
import xml.etree.ElementTree as ET
import yaml
from PIL import Image, UnidentifiedImageError
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from mv_platform.domain import Artifact, DomainValidationError, Event, JobSpec, JobStatus, Project
from mv_platform.domain.hashing import canonical_hash, canonical_json, freeze_json
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.repositories import Repository, RepositoryConflict, RepositoryNotFound
from mv_platform.infrastructure.artifacts import ArtifactStore, UnsafePathError
from mv_platform.application.control_plane import (
    ControlPlaneError, apply_environment, merge_runtime_config, public_config,
    read_config, write_config,
)


class ApplicationError(Exception):
    pass


class ApplicationConflict(ApplicationError):
    pass


class ApplicationNotFound(ApplicationError):
    pass


class ApplicationBlocked(ApplicationError):
    def __init__(self, message: str, *, error_stage: str = "", error_category: str = ""):
        super().__init__(message)
        self.error_stage = error_stage
        self.error_category = error_category


class MaterializeError(ApplicationError):
    """Raised when automatic input materialization cannot proceed."""
    pass


def _immutable(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_immutable(item) for item in value)
    return value


@dataclass(frozen=True)
class ProjectResult:
    project: Project
    brief: Mapping

    @property
    def project_id(self): return self.project.project_id

    @property
    def slug(self): return self.project.slug

    @property
    def brief_sha256(self): return self.project.brief_sha256


@dataclass(frozen=True)
class JobResult:
    job_spec: JobSpec
    status: JobStatus

    @property
    def job_id(self): return self.job_spec.job_id

    @property
    def canonical_job_digest(self): return self.job_spec.canonical_digest()


@dataclass(frozen=True)
class JobInspection:
    job_spec: JobSpec
    status: JobStatus
    events: tuple
    artifacts: tuple
    job_digest: str

    @property
    def canonical_job_digest(self): return self.job_digest

    @property
    def job_id(self): return self.job_spec.job_id


_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_SG_ID_RE = re.compile(r"^SG\d{3,}$")
_BG_ID_RE = re.compile(r"^BG\d{3,}$")


@dataclass(frozen=True)
class SceneGroup:
    id: str
    name: str
    source_section_id: str
    shot_ids: tuple
    location: str = ""
    time_of_day: str = ""
    weather: str = ""
    emotional_state: str = ""
    narrative_world_state: str = ""
    created_by: str = "system"
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class BackgroundMaster:
    id: str
    scene_group_id: str
    status: str
    source: str
    relative_path: str
    prompt_zh: str = ""
    prompt_en: str = ""
    model: str = ""
    request_id: str = ""
    cost_yuan: float = 0.0
    created_at: str = ""


class _NoopErrorLogs:
    """No-op error log store used when no real store is injected (tests, CLI)."""
    def append(self, source, event):
        pass


class ApplicationService:
    _PROJECT_DIRECTORIES = (
        "inputs/audio", "inputs/lyrics", "inputs/characters", "inputs/backgrounds",
        "inputs/materials",
        "creative", "assets/source", "assets/source/keyframes", "assets/generated", "outputs",
        ".mvstudio/jobs", ".mvstudio/work", ".mvstudio/logs",
    )

    def __init__(
        self,
        settings,
        database,
        supervisor=None,
        workspace_root=None,
        source_root=None,
        semantic_port=None,
        semantic_model=None,
        alignment_port=None,
        seedance_port=None,
        image_provider=None,
        workspace_pointer_path=None,
        error_logs=None,
    ):
        self.settings = settings
        self.database = database
        self.supervisor = supervisor
        if workspace_root is None:
            raise ApplicationBlocked("workspace_root is required")
        self.workspace_root = Path(workspace_root).resolve()
        self.repository = Repository(database)
        self.source_root = Path(source_root).resolve() if source_root is not None else None
        self.semantic_port = semantic_port
        self.semantic_model = semantic_model
        self.alignment_port = alignment_port
        self.seedance_port = seedance_port
        self.image_provider = image_provider
        self.workspace_pointer_path = (
            Path(workspace_pointer_path).expanduser().absolute()
            if workspace_pointer_path is not None else None
        )
        self.error_logs = error_logs or _NoopErrorLogs()
        self._initialized = False
        # Serializes read-modify-write cycles on shot-references.json so that a
        # long-running image/video generation job cannot overwrite concurrent
        # updates with a stale in-memory snapshot (lost-update race).
        self._shot_references_lock = threading.RLock()

    def _reject_source_workspace(self):
        if self.source_root is None:
            return
        if self.workspace_root == self.source_root or self.source_root in self.workspace_root.parents:
            raise ApplicationBlocked("workspace must be outside the application source tree")

    def _under_workspace(self, relative, label):
        path = Path(relative)
        if path.is_absolute() or "\\" in str(relative) or any(part == ".." for part in path.parts):
            raise ApplicationBlocked(label + " escapes workspace")
        candidate = (self.workspace_root / path).absolute()
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ApplicationBlocked(label + " escapes workspace") from exc
        return candidate

    def _project_root(self): return self._under_workspace(self.settings.project_root, "project root")
    def _data_root(self): return self._under_workspace(self.settings.data_root, "data root")
    def _job_root(self): return self._under_workspace(str(Path(self.settings.data_root) / "jobs"), "job root")

    def initialize(self):
        # Resolve every configured root before making any directory or database change.
        self._reject_source_workspace()
        project_root = self._project_root()
        data_root = self._data_root()
        job_root = self._job_root()
        db_path = self._under_workspace(self.settings.db_path, "database")
        if Path(self.database.path).resolve() != db_path.resolve():
            raise ApplicationBlocked("database path does not match workspace settings")
        for path in (project_root, data_root, job_root):
            if path.is_symlink() or path.resolve() != path:
                raise ApplicationBlocked("configured root is unsafe")
        self.database.migrate()
        for path in (project_root, data_root, job_root):
            path.mkdir(parents=True, exist_ok=True)
            if path.is_symlink() or path.resolve() != path:
                raise ApplicationBlocked("configured root is unsafe")
        try:
            apply_environment(read_config(self._settings_path(), self.workspace_root))
        except ControlPlaneError as exc:
            raise ApplicationBlocked(str(exc)) from exc
        self._initialized = True
        return None

    def _settings_path(self):
        return self._under_workspace(str(Path(self.settings.data_root) / "user-settings.json"), "settings")

    def get_runtime_configuration(self):
        self._require_initialized()
        try:
            result = public_config(read_config(self._settings_path(), self.workspace_root))
            result["saved_configuration"] = self._settings_path().is_file()
            self._add_workspace_transition(result)
            return result
        except ControlPlaneError as exc:
            raise ApplicationBlocked(str(exc)) from exc

    def update_runtime_configuration(self, update):
        self._require_initialized()
        try:
            update = json.loads(json.dumps(update))
            requested_workspace = update.get("paths", {}).pop("workspace_root", None)
            if requested_workspace is not None:
                self._save_workspace_pointer(requested_workspace)
            current = read_config(self._settings_path(), self.workspace_root)
            merged = merge_runtime_config(current, update, self.workspace_root)
            # Empty secret inputs mean "keep the saved key".
            for section in ("llm", "image", "video"):
                if update.get(section, {}).get("api_key") == "":
                    merged[section]["api_key"] = current[section]["api_key"]
            write_config(self._settings_path(), merged)
            apply_environment(merged)
            result = public_config(merged)
            result["saved_configuration"] = True
            self._add_workspace_transition(result)
            return result
        except ControlPlaneError as exc:
            raise ApplicationConflict(str(exc)) from exc

    def _saved_workspace_pointer(self):
        if self.workspace_pointer_path is None or not self.workspace_pointer_path.is_file():
            return self.workspace_root
        if self.workspace_pointer_path.is_symlink():
            raise ApplicationBlocked("workspace configuration path is unsafe")
        try:
            value = json.loads(self.workspace_pointer_path.read_text(encoding="utf-8"))
            return Path(value["workspace_root"]).expanduser().absolute()
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ApplicationBlocked("workspace configuration is invalid") from exc

    def _save_workspace_pointer(self, value):
        if self.workspace_pointer_path is None:
            raise ApplicationBlocked("workspace changes are not supported by this runtime")
        if not isinstance(value, str) or not value.strip() or "\x00" in value:
            raise ApplicationConflict("workspace path is invalid")
        target = Path(value.strip()).expanduser()
        if not target.is_absolute():
            raise ApplicationConflict("workspace path must be absolute")
        target = target.absolute()
        if self.source_root is not None and (
            target == self.source_root or self.source_root in target.parents
        ):
            raise ApplicationBlocked("workspace must be outside the application source tree")
        if target.exists() and (target.is_symlink() or not target.is_dir()):
            raise ApplicationBlocked("workspace path is unsafe")
        write_config(self.workspace_pointer_path, {"workspace_root": str(target)})

    def _add_workspace_transition(self, result):
        requested = self._saved_workspace_pointer()
        result["paths"]["active_workspace_root"] = str(self.workspace_root)
        result["paths"]["workspace_root"] = str(requested)
        result["paths"]["workspace_change_pending"] = requested != self.workspace_root

    def _project_directory(self, project_id):
        try:
            project = self.repository.get_project(project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(project_id) from exc
        return project, self._project_root() / project.slug

    def get_project_file(self, project_id, relative):
        """Resolve a user-visible project artifact without exposing arbitrary local paths."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        if not isinstance(relative, str) or not relative.startswith(
            ("outputs/", "assets/generated/", "assets/source/keyframes/", "creative/",
             "inputs/characters/", "inputs/backgrounds/")
        ):
            raise ApplicationConflict("project file path is invalid")
        path = Path(relative)
        if path.is_absolute() or "\\" in relative or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ApplicationConflict("project file path is invalid")
        candidate = root / path
        if candidate.is_symlink() or not candidate.is_file():
            raise ApplicationNotFound(relative)
        try:
            candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise ApplicationBlocked("project file escapes workspace") from exc
        return candidate

    @staticmethod
    def _read_structured_file(path):
        if path.is_symlink() or not path.is_file():
            return None
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                return json.loads(text)
            return yaml.safe_load(text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError):
            return None

    def _workflow_decisions(self, root):
        value = self._read_structured_file(root / "creative" / "workflow-decisions.json")
        return value if isinstance(value, dict) else {}

    def _scene_groups(self, root):
        value = self._read_structured_file(root / "creative" / "scene-groups.json")
        if not isinstance(value, dict) or not isinstance(value.get("scene_groups"), list):
            return None
        return value

    def _write_scene_groups(self, root, value):
        self._write_atomic_file(
            root / "creative" / "scene-groups.json",
            canonical_json(value), ".scene-groups-",
        )

    def _scene_planning(self, root):
        path = root / "creative" / "scene-planning.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return None

    def _write_scene_planning(self, root, value):
        path = root / "creative" / "scene-planning.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def _background_masters(self, root):
        value = self._read_structured_file(root / "creative" / "background-masters.json")
        if not isinstance(value, dict) or not isinstance(value.get("backgrounds"), list):
            return {"version": 1, "backgrounds": []}
        return value

    def _write_background_masters(self, root, value):
        self._write_atomic_file(
            root / "creative" / "background-masters.json",
            canonical_json(value), ".background-masters-",
        )

    def _shot_references(self, root):
        value = self._read_structured_file(root / "creative" / "shot-references.json")
        if not isinstance(value, dict) or not isinstance(value.get("shots"), dict):
            return {"version": 1, "shots": {}}
        return value

    @staticmethod
    def _read_keyframe_entries(shot: dict) -> list:
        result = []
        for item in shot.get("keyframes", []):
            if isinstance(item, str):
                result.append({
                    "path": item, "source": "legacy", "background_master_id": "",
                    "character_ids": [], "prompt_zh": "", "prompt_en": "",
                    "model": "", "request_id": "", "cost_yuan": 0.0, "created_at": "",
                })
            elif isinstance(item, dict) and item.get("path"):
                result.append(item)
        return result

    def _write_shot_references(self, root, value):
        self._write_atomic_file(
            root / "creative" / "shot-references.json",
            canonical_json(value), ".shot-references-",
        )

    @staticmethod
    def _parse_mp4_duration(video_bytes: bytes) -> float:
        """Parse duration (seconds) from MP4 mvhd box; return 0.0 on failure."""
        try:
            i = 0
            n = len(video_bytes)
            while i + 8 <= n:
                box_size = int.from_bytes(video_bytes[i:i+4], "big")
                box_type = video_bytes[i+4:i+8]
                if box_size < 8:
                    break
                if box_type == b"moov":
                    # recurse into moov
                    j = i + 8
                    while j + 8 <= i + box_size:
                        inner_size = int.from_bytes(video_bytes[j:j+4], "big")
                        inner_type = video_bytes[j+4:j+8]
                        if inner_size < 8:
                            break
                        if inner_type == b"mvhd":
                            version = video_bytes[j+8]
                            if version == 1 and j + 44 <= n:
                                timescale = int.from_bytes(video_bytes[j+28:j+32], "big")
                                duration = int.from_bytes(video_bytes[j+32:j+40], "big")
                            else:
                                if j + 28 > n:
                                    return 0.0
                                timescale = int.from_bytes(video_bytes[j+20:j+24], "big")
                                duration = int.from_bytes(video_bytes[j+24:j+28], "big")
                            if timescale == 0:
                                return 0.0
                            return round(duration / timescale, 3)
                        j += inner_size
                i += box_size
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _qc_video(video_bytes: bytes, duration_requested: int) -> "tuple[bool, dict]":
        """QC-check a video blob; return (passed, info_dict)."""
        issues = []
        if len(video_bytes) < 8 or video_bytes[4:8] != b"ftyp":
            issues.append("not_mp4")
        size = len(video_bytes)
        if size < 100_000:
            issues.append("file_too_small")
        if size > 200_000_000:
            issues.append("file_too_large")
        duration_actual = ApplicationService._parse_mp4_duration(video_bytes)
        if duration_actual == 0.0:
            issues.append("duration_parse_failed")
        elif abs(duration_actual - duration_requested) > 2.0:
            issues.append(f"duration_mismatch:{duration_actual:.1f}s_vs_{duration_requested}s")
        return len(issues) == 0, {
            "duration_actual": duration_actual,
            "file_size_bytes": size,
            "qc_issues": issues,
        }

    def _image_generation_audit(self, root):
        value = self._read_structured_file(root / "creative" / "image-generation-audit.json")
        return value if isinstance(value, dict) and isinstance(value.get("calls"), list) else {
            "version": 1, "calls": [],
        }

    def _append_image_generation_audit(self, root, call):
        audit = self._image_generation_audit(root)
        audit["calls"].append(call)
        self._write_atomic_file(
            root / "creative" / "image-generation-audit.json",
            canonical_json(audit), ".image-generation-audit-",
        )

    @staticmethod
    def _reference_assets(root, relative_directory):
        directory = root / relative_directory
        if not directory.is_dir() or directory.is_symlink():
            return []
        return [
            {"path": path.relative_to(root).as_posix(), "name": path.name}
            for path in sorted(directory.rglob("*"))
            if path.is_file() and not path.is_symlink()
            and path.suffix.lower() in {".jpeg", ".jpg", ".png", ".webp"}
        ]

    def _require_shot(self, root, shot_id):
        if not isinstance(shot_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", shot_id):
            raise ApplicationConflict("shot reference id is invalid")
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml")
        shots = visual.get("shots", []) if isinstance(visual, dict) else []
        shot = next(
            (item for item in shots if isinstance(item, dict) and item.get("id") == shot_id),
            None,
        )
        if shot is None:
            raise ApplicationNotFound(shot_id)
        return shot

    @staticmethod
    def _invalidate_decisions(root, stages):
        target = root / "creative" / "workflow-decisions.json"
        value = ApplicationService._read_structured_file(target)
        decisions = value if isinstance(value, dict) else {}
        updated = {key: item for key, item in decisions.items() if key not in set(stages)}
        return target, updated

    def _workflow_display_content(self, root):
        value = self._read_structured_file(root / "creative" / "user-facing-content.json")
        if not isinstance(value, dict) or not isinstance(value.get("fields"), dict):
            return {"version": 1, "fields": {}}
        return value

    @staticmethod
    def _workflow_content_fields(music, characters, story, visual):
        fields = {}

        def add(field_id, value):
            if isinstance(value, str) and value.strip():
                fields[field_id] = value.strip()

        if isinstance(music, dict):
            for item in music.get("sections", []):
                if isinstance(item, dict):
                    add("music.section.%s.emotion" % item.get("id", ""), item.get("emotion"))
        if isinstance(characters, dict):
            for item in characters.get("characters", []):
                if not isinstance(item, dict):
                    continue
                prefix = "character.%s." % item.get("id", "")
                add(prefix + "director_function", item.get("director_function"))
                traits = item.get("traits")
                if isinstance(traits, list):
                    add(prefix + "traits", "、".join(str(value) for value in traits))
        if isinstance(story, dict):
            add("story.premise", story.get("premise"))
            for item in story.get("sections", []):
                if isinstance(item, dict):
                    add("story.section.%s.emotion" % item.get("id", ""), item.get("emotion"))
        if isinstance(visual, dict):
            for item in visual.get("shots", []):
                if not isinstance(item, dict):
                    continue
                prefix = "shot.%s." % item.get("id", "")
                add(prefix + "purpose", item.get("purpose"))
                add(prefix + "primary_action", item.get("primary_action"))
                add(prefix + "first_frame", item.get("first_frame"))
                add(prefix + "last_frame", item.get("last_frame"))
                composition = item.get("composition", {})
                if isinstance(composition, dict):
                    add(prefix + "composition.arrangement", composition.get("arrangement"))
                transition = item.get("transition_out", {})
                if isinstance(transition, dict):
                    add(prefix + "transition_out.shared_element", transition.get("shared_element"))
        return fields

    @staticmethod
    def _apply_workflow_content(music, characters, story, visual, values):
        def value(field_id, current):
            replacement = values.get(field_id)
            return replacement if isinstance(replacement, str) and replacement.strip() else current

        if isinstance(music, dict):
            for item in music.get("sections", []):
                if isinstance(item, dict):
                    key = "music.section.%s.emotion" % item.get("id", "")
                    item["emotion"] = value(key, item.get("emotion", ""))
        if isinstance(characters, dict):
            for item in characters.get("characters", []):
                if not isinstance(item, dict):
                    continue
                prefix = "character.%s." % item.get("id", "")
                item["director_function"] = value(
                    prefix + "director_function", item.get("director_function", "")
                )
                traits = value(prefix + "traits", "、".join(item.get("traits", [])))
                item["traits"] = [part.strip() for part in re.split(r"[、,/]+", traits) if part.strip()]
        if isinstance(story, dict):
            story["premise"] = value("story.premise", story.get("premise", ""))
            for item in story.get("sections", []):
                if isinstance(item, dict):
                    key = "story.section.%s.emotion" % item.get("id", "")
                    item["emotion"] = value(key, item.get("emotion", ""))
        if isinstance(visual, dict):
            for item in visual.get("shots", []):
                if not isinstance(item, dict):
                    continue
                prefix = "shot.%s." % item.get("id", "")
                for key in ("purpose", "primary_action", "first_frame", "last_frame"):
                    item[key] = value(prefix + key, item.get(key, ""))
                composition = item.get("composition")
                if isinstance(composition, dict):
                    key = prefix + "composition.arrangement"
                    composition["arrangement"] = value(key, composition.get("arrangement", ""))
                transition = item.get("transition_out")
                if isinstance(transition, dict):
                    key = prefix + "transition_out.shared_element"
                    transition["shared_element"] = value(key, transition.get("shared_element", ""))

    def _translate_workflow_content(self, project_id, fields, target_language):
        if not fields:
            return {}
        from mvstudio.director.drafting import ModelBudget, ModelResult, ModelTask
        from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort

        provider = self.semantic_port or OpenAICompatibleSemanticPort.from_env()
        model = self.semantic_model or os.environ.get("LLM_MODEL", "")
        if not isinstance(model, str) or not model.strip():
            raise ApplicationBlocked("text model is not configured")
        schema = {"translations": [{"field_id": "text", "translated_text": "text"}]}
        target_name = "Simplified Chinese" if target_language == "zh-CN" else "professional English"
        instruction = (
            "You translate audiovisual production text into " + target_name + ". "
            "Preserve field_id, meaning, names, numbers and technical intent. Return exactly one "
            "translation for every input item and no commentary."
        )
        translated = {}
        entries = list(fields.items())
        batch_size = 4
        for offset in range(0, len(entries), batch_size):
            batch = dict(entries[offset:offset + batch_size])
            items = [{"field_id": key, "source_text": value} for key, value in batch.items()]
            payload = {"target_language": target_language, "items": items}
            if len(canonical_json(payload)) > 65536:
                raise ApplicationConflict("user-facing content is too large")
            task = ModelTask(
                event_type=("content.localize_requested" if target_language == "zh-CN"
                            else "content.translate_requested"),
                model=model.strip(), budget=ModelBudget(max_tokens=1600),
                reason="Maintain separate user-facing Chinese and internal English production text.",
                input_contract_hash=canonical_hash(payload),
                output_schema_hash=canonical_hash(schema), output_schema=schema,
                payload=payload, instruction=instruction,
            )
            try:
                result = provider.run(task)
            except Exception as exc:
                usage = (
                    getattr(exc, "input_tokens", 0),
                    getattr(exc, "cache_read_tokens", 0),
                    getattr(exc, "output_tokens", 0),
                )
                if any(usage):
                    self.record_llm_cost(
                        project_id, None, task.event_type, usage[0], usage[1], usage[2],
                        {"model": task.model, "target_language": target_language,
                         "content_hash": canonical_hash(batch),
                         "batch": offset // batch_size + 1,
                         "outcome": "invalid_response",
                         "finish_reason": getattr(exc, "finish_reason", "")},
                    )
                raise ApplicationBlocked("content translation model call failed") from exc
            if not isinstance(result, ModelResult):
                raise ApplicationBlocked("content translation returned an invalid result")
            rows = result.output.get("translations")
            if not isinstance(rows, list):
                raise ApplicationBlocked("content translation returned an invalid result")
            batch_result = {}
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                field_id = row.get("field_id")
                text = row.get("translated_text")
                if field_id in batch and isinstance(text, str) and text.strip():
                    batch_result[field_id] = text.strip()
            if set(batch_result) != set(batch):
                raise ApplicationBlocked("content translation is incomplete")
            translated.update(batch_result)
            self.record_llm_cost(
                project_id, None, task.event_type, result.input_tokens,
                result.cache_read_tokens, result.output_tokens,
                {"model": task.model, "target_language": target_language,
                 "content_hash": canonical_hash(batch),
                 "batch": offset // batch_size + 1},
            )
        return translated

    def localize_project_content(self, project_id):
        """Create a Chinese display layer for legacy English project artifacts."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        music = self._read_structured_file(root / "creative" / "music_map.yaml")
        characters = self._read_structured_file(root / "creative" / "character_map.yaml")
        story = self._read_structured_file(root / "creative" / "story_framework.yaml")
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml")
        fields = self._workflow_content_fields(music, characters, story, visual)
        record = self._workflow_display_content(root)
        # Model drafts may already be Chinese. Re-translating those fields can corrupt
        # names and fixed terms, so preserve them byte-for-byte in the display layer.
        for key, value in fields.items():
            if re.search(r"[\u3400-\u9fff]", value):
                record["fields"][key] = {"zh": value, "en": value}
        missing = {
            key: value for key, value in fields.items()
            if not re.search(r"[\u3400-\u9fff]", value)
            and not isinstance(record["fields"].get(key, {}).get("zh"), str)
        }
        translated = self._translate_workflow_content(project_id, missing, "zh-CN")
        for key, text in translated.items():
            record["fields"][key] = {"zh": text, "en": fields[key]}
        self._write_atomic_file(
            root / "creative" / "user-facing-content.json",
            canonical_json(record), ".user-facing-content-",
        )
        return self.get_project_workflow(project_id)

    def update_project_display_content(self, project_id, fields):
        """Save Chinese user edits and maintain an English execution copy."""
        self._require_initialized()
        if not isinstance(fields, dict) or not fields or len(fields) > 100:
            raise ApplicationConflict("user-facing content is invalid")
        _project, root = self._project_directory(project_id)
        paths = {
            "music": root / "creative" / "music_map.yaml",
            "characters": root / "creative" / "character_map.yaml",
            "story": root / "creative" / "story_framework.yaml",
            "visual": root / "creative" / "visual_score.yaml",
        }
        documents = {key: self._read_structured_file(path) for key, path in paths.items()}
        known = self._workflow_content_fields(
            documents["music"], documents["characters"], documents["story"], documents["visual"]
        )
        cleaned = {}
        for key, value in fields.items():
            if key not in known or not isinstance(value, str) or not value.strip():
                raise ApplicationConflict("user-facing content field is invalid")
            if len(value.encode("utf-8")) > 8000:
                raise ApplicationConflict("user-facing content field is too large")
            cleaned[key] = value.strip()
        english = self._translate_workflow_content(project_id, cleaned, "en")
        record = self._workflow_display_content(root)
        for key in cleaned:
            record["fields"][key] = {"zh": cleaned[key], "en": english[key]}
        self._apply_workflow_content(
            documents["music"], documents["characters"], documents["story"],
            documents["visual"], english,
        )
        for key, document in documents.items():
            if isinstance(document, dict) and paths[key].is_file():
                self._write_atomic_file(
                    paths[key], yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode("utf-8"),
                    ".execution-content-",
                )
        self._write_atomic_file(
            root / "creative" / "user-facing-content.json",
            canonical_json(record), ".user-facing-content-",
        )
        decisions = self._workflow_decisions(root)
        if any(key.startswith(("music.", "character.", "story.")) for key in cleaned):
            invalidate = {"story", "storyboard", "keyframes", "shots", "delivery"}
        else:
            invalidate = {"storyboard", "keyframes", "shots", "delivery"}
        decisions = {key: value for key, value in decisions.items() if key not in invalidate}
        self._write_atomic_file(
            root / "creative" / "workflow-decisions.json",
            canonical_json(decisions), ".workflow-decision-",
        )
        return self.get_project_workflow(project_id)

    def record_workflow_decision(self, project_id, stage_id, action, note=""):
        """Persist explicit user gates separately from automated test approvals."""
        self._require_initialized()
        allowed_stages = {"story", "storyboard", "scenes", "keyframes", "shots", "delivery"}
        if stage_id not in allowed_stages or action not in {"approve", "request_revision"}:
            raise ApplicationConflict("workflow decision is invalid")
        if not isinstance(note, str) or len(note.encode("utf-8")) > 8000:
            raise ApplicationConflict("workflow decision note is invalid")
        _project, root = self._project_directory(project_id)
        workflow = self.get_project_workflow(project_id)
        stage = next((item for item in workflow["stages"] if item["id"] == stage_id), None)
        if stage is None or (action == "approve" and not stage["can_approve"]):
            raise ApplicationConflict("workflow stage is not ready for approval")
        decisions = self._workflow_decisions(root)
        decisions[stage_id] = {
            "action": action,
            "note": note.strip(),
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "actor": "local_user",
        }
        self._write_atomic_file(
            root / "creative" / "workflow-decisions.json",
            canonical_json(decisions), ".workflow-decision-",
        )
        return self.get_project_workflow(project_id)

    def get_project_workflow(self, project_id):
        """Build the user-facing production workflow from canonical project artifacts."""
        self._require_initialized()
        project, root = self._project_directory(project_id)
        jobs = list(self.list_project_jobs(project_id))
        successful = [item for item in jobs if item.status.runtime_state is RuntimeState.SUCCEEDED]
        director_jobs = [item for item in successful if item.job_spec.operation in {"animatic", "compile"}]
        director = director_jobs[0] if director_jobs else None
        planning_jobs = [item for item in jobs if item.job_spec.operation == "animatic"]
        latest_planning = planning_jobs[0] if planning_jobs else None
        staging_source = director or latest_planning
        staging = self._job_root() / staging_source.job_id if staging_source else None

        def load(relative, fallback_staging=None):
            value = self._read_structured_file(root / relative)
            if value is None and staging is not None and fallback_staging:
                value = self._read_structured_file(staging / fallback_staging)
            return value

        intake = None
        lyrics_timed = None
        intake_source_job = None
        intake_jobs = [item for item in successful if item.job_spec.operation == "analyze"]
        # Queued analyze job: used by the frontend to unlock the auto-fill button even
        # before intake runs (so manifest.audio being empty does not hide fill controls).
        pending_analyze_jobs = [
            item for item in jobs
            if item.job_spec.operation == "analyze"
            and item.status.runtime_state is RuntimeState.QUEUED
        ]
        pending_analyze_job = pending_analyze_jobs[0] if pending_analyze_jobs else None
        for item in intake_jobs + ([director] if director else []):
            if item is None:
                continue
            intake = self._read_structured_file(
                self._job_root() / item.job_id / "intake" / "intake_manifest.json"
            )
            if isinstance(intake, dict):
                intake_source_job = item
                lyrics_timed = self._read_structured_file(
                    self._job_root() / item.job_id / "intake" / "lyrics_timed.json"
                )
                break
        removed_assets = self._removed_project_assets(root)
        removed_paths = {
            item.get("original_path") for item in removed_assets
            if isinstance(item.get("original_path"), str)
        }
        if isinstance(intake, dict) and isinstance(intake.get("characters"), list):
            intake["characters"] = [
                item for item in intake["characters"]
                if isinstance(item, dict) and item.get("path") not in removed_paths
            ]
        duplicate_groups = []
        if isinstance(intake, dict):
            grouped = {}
            for item in intake.get("characters", []):
                stem = Path(str(item.get("path", ""))).stem
                label = stem.rsplit("-", 1)[0] if "-" in stem else stem
                grouped.setdefault(label, []).append(item)
            for label, candidates in grouped.items():
                if len(candidates) < 2:
                    continue
                preferred = max(
                    candidates,
                    key=lambda item: int(item.get("width", 0)) * int(item.get("height", 0)),
                )
                duplicate_groups.append({
                    "person_label": label,
                    "preferred_path": preferred.get("path", ""),
                    "candidate_paths": [item.get("path", "") for item in candidates],
                    "reason": "同一人物标识存在多个分辨率版本，默认建议保留像素面积最大的原始图",
                })
        music = load("creative/music_map.yaml", "creative/music_map.yaml")
        characters = load("creative/character_map.yaml", "creative/character_map.yaml")
        story = load("creative/story_framework.yaml", "creative/story_framework.yaml")
        visual = load("creative/visual_score.yaml", "creative/visual_score.yaml")
        brief = load("brief.json") or {}
        display_content = self._workflow_display_content(root)
        display_values = {
            key: item.get("zh") for key, item in display_content["fields"].items()
            if isinstance(item, dict) and isinstance(item.get("zh"), str)
        }
        self._apply_workflow_content(music, characters, story, visual, display_values)
        audit = load("creative/model_audit.json", "creative/model_audit.json")
        qc = load("outputs/qc_report.json", "outputs/qc_report.json")
        decisions = self._workflow_decisions(root)
        costs = self.get_project_costs(project_id)
        prompts = self.get_project_prompts(project_id)
        reference_registry = self._shot_references(root)
        background_assets = (
            self._reference_assets(root, "inputs/backgrounds")
            + self._reference_assets(root, "assets/generated/backgrounds")
        )
        calls = audit.get("calls", []) if isinstance(audit, dict) else []
        image_calls = self._image_generation_audit(root).get("calls", [])
        calls = [*calls, *image_calls]
        calls_by_event = {
            item.get("event_type"): item for item in calls if isinstance(item, dict) and item.get("event_type")
        }
        cost_by_step = {}
        cost_by_job = {}
        cost_by_shot = {}
        translation_cost_by_source = {}
        for entry in costs["entries"]:
            cost_by_job[entry["job_id"]] = round(
                cost_by_job.get(entry["job_id"], 0) + entry["amount_yuan"], 8
            )
            cost_by_step[entry["step_id"]] = round(
                cost_by_step.get(entry["step_id"], 0) + entry["amount_yuan"], 8
            )
            shot_id = entry.get("metadata", {}).get("shot_id", "")
            if shot_id:
                cost_by_shot[shot_id] = round(
                    cost_by_shot.get(shot_id, 0) + entry["amount_yuan"], 8
                )
            if entry["step_id"] == "prompt.translate_requested":
                source_event = entry.get("metadata", {}).get("source_event", "")
                if source_event:
                    translation_cost_by_source[source_event] = round(
                        translation_cost_by_source.get(source_event, 0) + entry["amount_yuan"], 8
                    )

        character_items = []
        if isinstance(characters, dict):
            for item in characters.get("characters", []):
                if not isinstance(item, dict):
                    continue
                character_items.append({
                    "id": item.get("id", ""), "name": item.get("name", ""),
                    "source_asset": item.get("source_asset", ""),
                    "director_function": item.get("director_function", ""),
                    "traits": item.get("traits", []),
                })
        character_items = [
            item for item in character_items if item["source_asset"] not in removed_paths
        ]
        character_index = {item["id"]: item for item in character_items}
        bg_doc = self._background_masters(root)
        shots = []
        if isinstance(visual, dict):
            for shot in visual.get("shots", []):
                if not isinstance(shot, dict):
                    continue
                cast = [
                    character_index[value] for value in shot.get("characters", [])
                    if value in character_index
                ]
                shot_references = reference_registry["shots"].get(shot.get("id", ""), {})
                background_reference = shot_references.get("background", "")
                if background_reference and not (root / background_reference).is_file():
                    background_reference = ""
                # PRD-007B: fall back to background_master path if per-shot field is empty
                if not background_reference:
                    bg_master_id = shot_references.get("background_master_id", "")
                    if bg_master_id and bg_doc:
                        master_bg = next(
                            (b for b in bg_doc.get("backgrounds", []) if b.get("id") == bg_master_id),
                            None,
                        )
                        if master_bg:
                            bg_path = master_bg.get("relative_path", "")
                            if bg_path and (root / bg_path).is_file():
                                background_reference = bg_path
                keyframe_entries_raw = self._read_keyframe_entries(shot_references)
                keyframe_candidates = [
                    e["path"] for e in keyframe_entries_raw
                    if (root / e["path"]).is_file() and not (root / e["path"]).is_symlink()
                ]
                selected_keyframe = shot_references.get("selected_keyframe", "")
                if selected_keyframe not in keyframe_candidates:
                    selected_keyframe = ""
                keyframe_entries = [
                    {
                        "path": e["path"],
                        "source": e.get("source", "legacy"),
                        "background_master_id": e.get("background_master_id", ""),
                        "character_ids": e.get("character_ids", []),
                        "prompt_zh": e.get("prompt_zh", ""),
                        "model": e.get("model", ""),
                        "cost_yuan": e.get("cost_yuan", 0.0),
                        "created_at": e.get("created_at", ""),
                        "is_selected": e["path"] == selected_keyframe,
                    }
                    for e in keyframe_entries_raw
                    if (root / e["path"]).is_file() and not (root / e["path"]).is_symlink()
                ]
                shots.append({
                    "id": shot.get("id", ""), "time": shot.get("time", []),
                    "background_master_id": shot_references.get("background_master_id", ""),
                    "scene_group_id": shot_references.get("scene_group_id", ""),
                    "skipped": bool(shot_references.get("skipped", False)),
                    "section": shot.get("section", ""), "energy": shot.get("energy", 0),
                    "purpose": shot.get("purpose", ""), "lyric": shot.get("lyric", {}),
                    "composition": shot.get("composition", {}),
                    "primary_action": shot.get("primary_action", ""),
                    "first_frame": shot.get("first_frame", ""),
                    "last_frame": shot.get("last_frame", ""),
                    "transition_out": shot.get("transition_out", {}),
                    "director_beat": shot.get("director_beat", {}),
                    "visual_events": shot.get("visual_events", []),
                    "technique": shot.get("technique", ""), "assets": shot.get("assets", {}),
                    "characters": cast, "status": "planned",
                    "background": {
                        "description": shot.get("first_frame", ""),
                        "reference": background_reference,
                        "status": "reference_bound" if background_reference else "planned_for_generation",
                    },
                    "keyframes": keyframe_candidates,
                    "keyframe_entries": keyframe_entries,
                    "selected_keyframe": selected_keyframe,
                    "video_entries": [
                        {
                            "path": e["path"],
                            "duration_requested": e.get("duration_requested", 0),
                            "duration_actual": e.get("duration_actual", 0.0),
                            "cost_yuan": e.get("cost_yuan", 0.0),
                            "qc_passed": e.get("qc_passed", False),
                            "is_selected": e["path"] == shot_references.get("selected_video", ""),
                            "created_at": e.get("created_at", ""),
                        }
                        for e in shot_references.get("video_entries", [])
                        if isinstance(e, dict) and e.get("path")
                    ],
                    "selected_video": shot_references.get("selected_video", ""),
                    "cost_yuan": cost_by_shot.get(shot.get("id", ""), 0),
                })

        def prompt_info(keys):
            from mv_platform.application.prompt_catalog import SYSTEM_PREFIX
            items = []
            for key in keys:
                call = calls_by_event.get(key)
                task_text = prompts.get(key, "")
                system_text = prompts.get(SYSTEM_PREFIX + key, "")
                source_instruction = (
                    system_text.strip() + "\n\n本步骤任务要求：\n" + task_text.strip()
                )
                prompt_hash = "sha256:" + hashlib.sha256(
                    source_instruction.encode("utf-8")
                ).hexdigest()
                used_hash = call.get("source_prompt_hash", call.get("prompt_hash")) if call else ""
                used_current_prompt = bool(call and used_hash == prompt_hash)
                translation = call.get("prompt_translation", {}) if call else {}
                items.append({
                    "key": key, "text": task_text, "task_text": task_text,
                    "system_text": system_text, "used": used_current_prompt,
                    "call_recorded": bool(call),
                    "model": call.get("model", "") if call else "",
                    "usage": call.get("usage", {}) if call else {},
                    "cost_yuan": cost_by_step.get(key, 0),
                    "translation": {
                        "enabled": True,
                        "system_text": prompts.get(SYSTEM_PREFIX + "prompt.translate_requested", ""),
                        "task_text": prompts.get("prompt.translate_requested", ""),
                        "used": bool(translation),
                        "usage": translation.get("usage", {}),
                        "cost_yuan": translation_cost_by_source.get(key, 0),
                    },
                })
            return items

        story_decision = decisions.get("story", {})
        storyboard_decision = decisions.get("storyboard", {})
        keyframes_decision = decisions.get("keyframes", {})
        story_approved = story_decision.get("action") == "approve"
        storyboard_approved = storyboard_decision.get("action") == "approve"
        keyframes_approved = keyframes_decision.get("action") == "approve"
        structural_test = bool(
            isinstance(visual, dict)
            and visual.get("purpose") == "structural_animatic_test_only"
        )
        active_character_paths = {
            item.get("path")
            for item in (intake.get("characters", []) if isinstance(intake, dict) else [])
            if isinstance(item, dict) and item.get("path")
        }
        analyzed_character_paths = {
            item.get("source_asset")
            for item in (characters.get("characters", []) if isinstance(characters, dict) else [])
            if isinstance(item, dict) and item.get("source_asset")
        }
        # Trash history must not keep a regenerated project permanently blocked.
        assets_changed = bool(removed_assets) and bool(analyzed_character_paths) and (
            active_character_paths != analyzed_character_paths
        )
        inputs_changed = bool(
            intake_source_job is not None
            and director is not None
            and tuple(sorted(intake_source_job.job_spec.input_refs))
            != tuple(sorted(director.job_spec.input_refs))
        )
        if structural_test or assets_changed or inputs_changed:
            story_approved = False
            storyboard_approved = False
            keyframes_approved = False
        active_shots = [item for item in shots if not item.get("skipped")]
        selected_keyframe_count = sum(bool(item.get("selected_keyframe")) for item in active_shots)
        all_keyframes_selected = bool(active_shots) and selected_keyframe_count == len(active_shots)
        if not all_keyframes_selected:
            keyframes_approved = False

        # PRD-002: scenes stage
        if storyboard_approved and self._scene_groups(root) is None and shots:
            self._migrate_to_scene_groups(root)
        sg_doc = self._scene_groups(root)
        # PRD-007B: scene planning stage
        sp_data = self._scene_planning(root)
        sp_status = sp_data.get("status", "draft") if sp_data else None
        scene_planning_approved = bool(sp_status == "approved")
        scenes_decision = decisions.get("scenes", {})
        scenes_approved = scenes_decision.get("action") == "approve"
        scene_groups_data = []
        all_have_background = False
        if sg_doc is not None:
            bgs_by_sg = {}
            for bg in bg_doc.get("backgrounds", []):
                bgs_by_sg.setdefault(bg.get("scene_group_id", ""), []).append(bg)
            for sg in sg_doc.get("scene_groups", []):
                sg_entry = dict(sg)
                sg_bgs = bgs_by_sg.get(sg.get("id", ""), [])
                sg_entry["backgrounds"] = sg_bgs
                has_selected = any(b.get("status") == "selected" for b in sg_bgs)
                sg_entry["has_selected_background"] = has_selected
                scene_groups_data.append(sg_entry)
            all_have_background = bool(scene_groups_data) and all(
                sg.get("has_selected_background") for sg in scene_groups_data
            )
        if not scenes_approved and not all_have_background:
            keyframes_approved = False

        animatic_path = "outputs/animatic.mp4" if (root / "outputs/animatic.mp4").is_file() else ""
        final_paths = sorted(
            path.relative_to(root).as_posix() for path in (root / "outputs").glob("*.mp4")
            if path.is_file() and path.name != "animatic.mp4"
        ) if (root / "outputs").is_dir() else []
        auto_test = any("final_mvp_" in value for value in final_paths)

        def stage(stage_id, title, subtitle, status, decision, can_approve, data=None,
                  stage_prompts=(), artifact_paths=(), cost_steps=()):
            return {
                "id": stage_id, "title": title, "subtitle": subtitle, "status": status,
                "decision": decision or None, "can_approve": bool(can_approve),
                "data": data or {}, "prompts": prompt_info(stage_prompts),
                "artifacts": [
                    path for path in artifact_paths
                    if path and (root / path).is_file() and not (root / path).is_symlink()
                ],
                "cost_yuan": round(
                    sum(cost_by_step.get(key, 0) for key in cost_steps)
                    + sum(translation_cost_by_source.get(key, 0) for key in stage_prompts), 8
                ),
            }

        stages = [
            stage("intake", "素材与需求", "确认音频、歌词、人物和交付方向", "completed" if intake else "pending",
                  None, False, {"manifest": intake or {}, "brief": brief,
                                "backgrounds": background_assets,
                                "removed_characters": removed_assets,
                                "assets_changed": assets_changed,
                                "inputs_changed": inputs_changed,
                                "duplicate_groups": duplicate_groups,
                                "pending_materialization": self.pending_materialization(project_id),
                                # Exposed so the frontend can show the auto-fill button even
                                # when manifest.audio is still empty (intake not yet run).
                                "analyze_job_id": pending_analyze_job.job_id if pending_analyze_job else None},
                  ("asset.curate_requested",), artifact_paths=()),
            stage("music", "音乐与歌词", "校准时间轴、段落、情绪和能量", "pending" if inputs_changed else ("completed" if music else ("pending" if intake else "locked")),
                  None, False, {"music_map": music or {}, "characters": character_items,
                                "inputs_changed": inputs_changed,
                                "has_lyrics": bool(intake and intake.get("lyrics")),
                                "director_entries": (
                                    lyrics_timed.get("entries", [])
                                    if isinstance(lyrics_timed, dict) else []
                                ),
                                "director_contract": (
                                    (intake.get("lyrics") or {}).get("director_contract")
                                    if isinstance(intake, dict) else None
                                )},
                  ("lyrics.semantic_segment.requested",),
                  ("creative/music_map.yaml", "creative/lyrics_semantic.json"),
                  ("lyrics.semantic_segment.requested",)),
            stage("story", "故事框架", "确认人物关系、情绪推进、高潮与结尾", "approved" if story_approved else ("revision" if story_decision.get("action") == "request_revision" else ("awaiting_approval" if story else "locked")),
                  story_decision, bool(story and not structural_test and not assets_changed and not inputs_changed),
                  {"story": story or {}, "characters": character_items,
                   "has_characters": bool(intake and intake.get("characters")),
                   "structural_test": structural_test, "assets_changed": assets_changed,
                   "inputs_changed": inputs_changed},
                  ("relationship_map.draft_requested",), ("creative/story_framework.yaml",),
                  ("relationship_map.draft_requested",)),
            stage("storyboard", "分镜工作台", "逐镜确认人物、场景组归属、动作与转场", "approved" if storyboard_approved else ("revision" if storyboard_decision.get("action") == "request_revision" else ("awaiting_approval" if story_approved and shots else ("preview_only" if shots else "locked"))),
                  storyboard_decision, bool((story_approved and shots) or (inputs_changed and storyboard_decision.get("action") == "approve" and shots)), {"shots": shots,
                  "backgrounds": background_assets, "preview_only": not story_approved},
                  ("visual_score.creative_draft_requested", "visual_score.quality_review_requested",
                   "image.background.generate_requested"),
                  ("creative/visual_score.yaml", "creative/storyboard.md", animatic_path),
                  ("visual_score.creative_draft_requested", "visual_score.quality_review_requested",
                   "image.background.generate_requested")),
            stage("scene_planning", "场景组规划", "LLM 建议分组、用户调整并锁定",
                  "approved" if scene_planning_approved else (
                      "locked" if not storyboard_approved else (
                          "pending" if sp_data is None else "in_progress"
                      )
                  ),
                  None, False,
                  {"groups": sp_data.get("groups", []) if sp_data else [],
                   "llm_suggestion_used": sp_data.get("llm_suggestion_used", False) if sp_data else False,
                   "status": sp_status or "pending",
                   "system_prompt": sp_data.get("system_prompt", "") if sp_data else "",
                   "task_prompt": sp_data.get("task_prompt", "") if sp_data else ""}),
            stage("scenes", "场景与背景", "确认场景分组和每组背景母版",
                  "approved" if scenes_approved else (
                      "locked" if not scene_planning_approved else (
                          "awaiting_approval" if all_have_background else "pending"
                      )
                  ),
                  scenes_decision, bool(scene_planning_approved and all_have_background),
                  {"scene_groups": scene_groups_data, "all_have_background": all_have_background, "shots": shots},
                  ("image.background.generate_requested",),
                  cost_steps=("image.background.generate_requested",)),
            stage("keyframes", "关键帧选择", "确认人物与背景组合后的完整场景首帧", "approved" if keyframes_approved else ("locked" if not scenes_approved else ("awaiting_approval" if all_keyframes_selected else "pending")),
                  keyframes_decision, bool(scenes_approved and all_keyframes_selected),
                  {"shots": shots, "selected_count": selected_keyframe_count,
                   "total_count": len(active_shots),
                   "reason": "请为每个分镜上传或生成完整场景首帧，并选择最终版本"},
                  ("image.keyframe.generate_requested",), cost_steps=("image.keyframe.generate_requested",)),
            stage("shots", "单镜制作", "逐镜生成、诊断、预览和返修", "locked" if not keyframes_approved else "pending",
                  decisions.get("shots"), False, {"shots": shots, "shot_count": len(shots), "generated_count": 0,
                  "reason": "关键帧确认后，逐镜视频制作才会开放"},
                  ("video.shot.generate_requested",), cost_steps=("video.shot.generate_requested",)),
            stage("composite", "合成验收", "检查字幕、声音、时长、画幅和连续性", "test_output" if final_paths else ("preview" if animatic_path else "locked"),
                  None, False, {"animatic": animatic_path, "finals": final_paths, "qc": qc or {}, "automated_test": auto_test},
                  artifact_paths=(animatic_path, *final_paths)),
            stage("delivery", "最终交付", "用户确认后再外发成片", "awaiting_approval" if final_paths else "locked",
                  decisions.get("delivery"), bool(final_paths), {"finals": final_paths, "automated_test": auto_test},
                  artifact_paths=tuple(final_paths)),
        ]
        if structural_test or assets_changed or inputs_changed:
            story_stage = next(item for item in stages if item["id"] == "story")
            story_stage["status"] = "revision"
        current = (
            next(item for item in stages if item["id"] == "music")
            if inputs_changed else
            next(
                (item for item in stages if item["status"] in {"awaiting_approval", "revision"}),
                next(
                    (item for item in stages if item["status"] not in {"completed", "approved"}),
                    stages[-1],
                ),
            )
        )
        return {
            "project": {"project_id": project.project_id, "slug": project.slug,
                        "display_name": brief.get("title", project.slug)},
            "current_stage_id": current["id"], "current_stage_title": current["title"],
            "blocking_reason": (
                "新素材已导入，需要重新分析音乐、歌词、故事和分镜"
                if inputs_changed else
                ("人物素材已变更，需要重新分析并生成故事方案"
                if assets_changed else
                ("当前仅有结构测试草稿，需要重做正式故事方案"
                if structural_test else
                ("等待用户确认后才能进入下一步" if current["status"] == "awaiting_approval" else
                 ("请在当前步骤开始制作" if current["status"] == "pending" else ""))
                ))
            ),
            "automated_test_output": auto_test, "costs": costs, "stages": stages,
            "display_content": {
                "localized_fields": len(display_values),
                "available_fields": len(self._workflow_content_fields(music, characters, story, visual)),
            },
            "runs": [{
                "job_id": item.job_id,
                "operation": item.job_spec.operation,
                "runtime_state": item.status.runtime_state.value,
                "business_stage": item.status.business_stage.value,
                "updated_at": item.status.updated_at.isoformat(),
                "error_code": item.status.error_code,
                "cost_yuan": cost_by_job.get(item.job_id, 0),
                "checkpoint": (
                    "视觉总谱与分镜"
                    if (self._job_root() / item.job_id / "creative" / "music_map.yaml").is_file()
                    else "准备输入素材"
                ),
                "failure_message": (
                    "视觉总谱返回内容不完整，歌词、音乐结构和人物关系已经保留。"
                    if item.status.runtime_state is RuntimeState.FAILED
                    and (self._job_root() / item.job_id / "creative" / "music_map.yaml").is_file()
                    else ("任务执行失败，请查看错误日志。"
                          if item.status.runtime_state is RuntimeState.FAILED else "")
                ),
                "can_resume": bool(
                    item.status.runtime_state is RuntimeState.FAILED
                    and item.job_spec.operation == "animatic"
                    and (self._job_root() / item.job_id / "creative" / "music_map.yaml").is_file()
                    and (self._job_root() / item.job_id / "creative" / "character_map.yaml").is_file()
                    and (self._job_root() / item.job_id / "creative" / "lyrics_semantic.json").is_file()
                    and (self._job_root() / item.job_id / "creative" / "visual_score.yaml").is_file()
                ),
            } for item in jobs],
            "active_jobs": self._get_active_image_jobs(project_id),
        }

    def _get_active_image_jobs(self, project_id: str) -> list:
        """Return queued/running image-gen jobs for active_jobs workflow field."""
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT jobs.job_id, jobs.operation, jobs.input_refs, "
                "job_status.runtime_state, job_status.updated_at "
                "FROM jobs JOIN job_status ON job_status.job_id=jobs.job_id "
                "WHERE jobs.project_id=? "
                "AND jobs.operation IN ('generate_background', 'generate_keyframe') "
                "AND job_status.runtime_state IN ('queued', 'running') "
                "ORDER BY job_status.updated_at DESC",
                (project_id,),
            ).fetchall()
        result = []
        for row in rows:
            job_id, operation, input_refs_str, state, updated_at = row
            params = json.loads(input_refs_str)
            shot_id = params[0] if params else ""
            job_type = (
                "generate_background" if operation == "generate_background"
                else "generate_keyframe"
            )
            result.append({
                "job_id": job_id,
                "type": job_type,
                "shot_id": shot_id,
                "status": state,
                "started_at": updated_at,
            })
        return result

    _IMPORT_EXTENSIONS = {
        "audio": {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"},
        "lyrics": {".lrc", ".txt", ".xlsx"},
        "characters": {".jpeg", ".jpg", ".png", ".webp"},
        "backgrounds": {".jpeg", ".jpg", ".png", ".webp"},
    }
    _REFERENCE_IMAGE_MAX_BYTES = 40 * 1024 * 1024
    _REFERENCE_IMAGE_FORMATS = {
        ".jpeg": "JPEG", ".jpg": "JPEG", ".png": "PNG", ".webp": "WEBP",
    }

    @classmethod
    def _validate_reference_image(cls, path, extension):
        try:
            if path.stat().st_size > cls._REFERENCE_IMAGE_MAX_BYTES:
                raise ApplicationConflict("reference image is too large")
            with Image.open(path) as image:
                width, height = image.size
                actual_format = (image.format or "").upper()
                if actual_format != cls._REFERENCE_IMAGE_FORMATS.get(extension):
                    raise ApplicationConflict("reference image extension does not match content")
                if width < 1 or height < 1 or width > 32768 or height > 32768:
                    raise ApplicationConflict("reference image dimensions are unsupported")
                image.verify()
        except ApplicationConflict:
            raise
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApplicationConflict("reference image is invalid") from exc

    @staticmethod
    def _xlsx_lyrics(path):
        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        try:
            with zipfile.ZipFile(path) as archive:
                if len(archive.infolist()) > 200 or any(
                    item.file_size > 20 * 1024 * 1024 for item in archive.infolist()
                ):
                    raise ApplicationConflict("spreadsheet is too large")
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(item.itertext()) for item in shared_root.findall("x:si", namespace)]
                sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        except (KeyError, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
            raise ApplicationConflict("lyrics spreadsheet is invalid") from exc

        rows = []
        for row in sheet.findall(".//x:sheetData/x:row", namespace):
            values = {}
            for cell in row.findall("x:c", namespace):
                reference = cell.get("r", "")
                column = "".join(char for char in reference if char.isalpha())
                value_node = cell.find("x:v", namespace)
                if not column or value_node is None or value_node.text is None:
                    continue
                value = value_node.text
                if cell.get("t") == "s":
                    try:
                        value = shared[int(value)]
                    except (ValueError, IndexError) as exc:
                        raise ApplicationConflict("lyrics spreadsheet is invalid") from exc
                values[column] = value.strip()
            if values:
                rows.append(values)
        if not rows:
            raise ApplicationConflict("lyrics spreadsheet is empty")
        headers = {value: column for column, value in rows[0].items()}
        lyric_column = headers.get("歌词")
        start_column = headers.get("起始时间")
        if not lyric_column:
            raise ApplicationConflict("lyrics spreadsheet needs a lyrics column")
        lines = []
        for row in rows[1:]:
            lyric = row.get(lyric_column, "").strip()
            if not lyric:
                continue
            if start_column and row.get(start_column, "").strip():
                try:
                    seconds = float(row[start_column])
                except ValueError as exc:
                    raise ApplicationConflict("lyrics spreadsheet start time is invalid") from exc
                minutes, remainder = divmod(max(0, seconds), 60)
                lines.append(f"[{int(minutes):02d}:{remainder:05.2f}]{lyric}")
            else:
                lines.append(lyric)
        if not lines:
            raise ApplicationConflict("lyrics spreadsheet has no lyrics")
        return ("\n".join(lines) + "\n").encode("utf-8")

    def import_project_asset(self, project_id, source_path, original_name, kind_hint=""):
        """Import a browser-selected file without accepting a client destination path."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        if not isinstance(original_name, str) or not original_name.strip() or "\x00" in original_name:
            raise ApplicationConflict("asset name is invalid")
        name = Path(original_name.replace("\\", "/")).name
        if name.startswith("."):
            return {"ignored": True, "name": name}
        extension = Path(name).suffix.lower()
        if kind_hint and kind_hint not in self._IMPORT_EXTENSIONS:
            raise ApplicationConflict("asset type is invalid")
        kind = kind_hint or next(
            (key for key, values in self._IMPORT_EXTENSIONS.items() if extension in values), None
        )
        if kind is None:
            kind = "materials"
        elif extension not in self._IMPORT_EXTENSIONS[kind]:
            raise ApplicationConflict("asset extension does not match its type")
        source = Path(source_path)
        if source.is_symlink() or not source.is_file():
            raise ApplicationBlocked("asset upload is not a regular file")
        if kind == "backgrounds":
            self._validate_reference_image(source, extension)
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        suffix = digest.hexdigest()[:10]
        output_name = Path(name).stem + "-" + suffix + extension
        destination = root / "inputs" / kind / output_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            raise ApplicationBlocked("asset destination is unsafe")
        if not destination.exists():
            self._atomic_copy(source, destination)
        result = {
            "ignored": False,
            "kind": kind,
            "bucket": "inputs/" + kind,
            "relative_path": destination.relative_to(root).as_posix(),
            "name": name,
        }
        return result

    def bind_shot_background(self, project_id, shot_id, relative):
        """Bind a project background reference to one planned shot."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        self._require_shot(root, shot_id)
        if not isinstance(relative, str) or not relative.startswith(
            ("inputs/backgrounds/", "assets/generated/backgrounds/")
        ):
            raise ApplicationConflict("shot background path is invalid")
        path = Path(relative)
        if path.is_absolute() or "\\" in relative or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ApplicationConflict("shot background path is invalid")
        source = root / path
        if source.is_symlink() or not source.is_file():
            raise ApplicationNotFound(relative)
        try:
            source.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise ApplicationBlocked("shot background escapes project") from exc
        self._validate_reference_image(source, path.suffix.lower())
        references = self._shot_references(root)
        record = references["shots"].setdefault(shot_id, {})
        record["background"] = relative
        record["background_bound_at"] = datetime.now(timezone.utc).isoformat()
        self._write_shot_references(root, references)
        target, decisions = self._invalidate_decisions(
            root, {"storyboard", "keyframes", "shots", "delivery"},
        )
        self._write_atomic_file(
            target, canonical_json(decisions), ".workflow-decision-",
        )
        return self.get_project_workflow(project_id)

    def import_shot_keyframe(self, project_id, shot_id, source_path, original_name):
        """Import a complete character-and-background frame as a shot candidate."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        self._require_shot(root, shot_id)
        if not isinstance(original_name, str) or not original_name.strip() or "\x00" in original_name:
            raise ApplicationConflict("keyframe name is invalid")
        name = Path(original_name.replace("\\", "/")).name
        extension = Path(name).suffix.lower()
        if extension not in self._IMPORT_EXTENSIONS["backgrounds"]:
            raise ApplicationConflict("keyframe must be an image")
        source = Path(source_path)
        if source.is_symlink() or not source.is_file():
            raise ApplicationBlocked("keyframe upload is not a regular file")
        self._validate_reference_image(source, extension)
        digest_value = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest_value.update(chunk)
        digest = digest_value.hexdigest()
        output_name = Path(name).stem + "-" + digest[:10] + extension
        relative = Path("assets/source/keyframes") / shot_id / output_name
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            raise ApplicationBlocked("keyframe destination is unsafe")
        if not destination.exists():
            self._atomic_copy(source, destination)
        relative_text = relative.as_posix()
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].setdefault(shot_id, {})
            candidates = record.setdefault("keyframes", [])
            existing_paths = [e["path"] if isinstance(e, dict) else e for e in candidates]
            entry = {
                "path": relative_text,
                "source": "uploaded",
                "background_master_id": "",
                "character_ids": [],
                "prompt_zh": "", "prompt_en": "",
                "model": "", "request_id": "",
                "cost_yuan": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if relative_text not in existing_paths:
                candidates.append(entry)
            if not record.get("selected_keyframe"):
                record["selected_keyframe"] = relative_text
            record["keyframes_updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_shot_references(root, references)
            target, decisions = self._invalidate_decisions(root, {"keyframes", "shots", "delivery"})
            self._write_atomic_file(target, canonical_json(decisions), ".workflow-decision-")
        return self.get_project_workflow(project_id)

    def set_shot_skipped(self, project_id, shot_id, skipped: bool):
        """Mark or unmark a shot as skipped. Skipped shots are excluded from keyframe/video/composite."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        self._require_shot(root, shot_id)
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].setdefault(shot_id, {})
            record["skipped"] = bool(skipped)
            record["skipped_at"] = datetime.now(timezone.utc).isoformat() if skipped else ""
            self._write_shot_references(root, references)
        target, decisions = self._invalidate_decisions(root, {"keyframes", "shots", "delivery"})
        self._write_atomic_file(target, canonical_json(decisions), ".workflow-decision-")
        return self.get_project_workflow(project_id)

    def delete_shot_keyframe(self, project_id, shot_id, relative):
        """Remove a keyframe candidate from a shot (does not delete the file)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        self._require_shot(root, shot_id)
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].get(shot_id, {})
            candidates = record.get("keyframes", [])
            filtered = [
                e for e in candidates
                if (e["path"] if isinstance(e, dict) else e) != relative
            ]
            if len(filtered) == len(candidates):
                raise ApplicationNotFound(relative)
            record["keyframes"] = filtered
            entries = record.get("keyframe_entries", [])
            record["keyframe_entries"] = [
                e for e in entries
                if not (isinstance(e, dict) and e.get("path") == relative)
            ]
            if record.get("selected_keyframe") == relative:
                record["selected_keyframe"] = ""
            self._write_shot_references(root, references)
        target, decisions = self._invalidate_decisions(root, {"keyframes", "shots", "delivery"})
        self._write_atomic_file(target, canonical_json(decisions), ".workflow-decision-")
        return self.get_project_workflow(project_id)

    def select_shot_keyframe(self, project_id, shot_id, relative):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        self._require_shot(root, shot_id)
        candidate = root / Path(relative)
        if candidate.is_symlink() or not candidate.is_file():
            raise ApplicationNotFound(relative)
        self._validate_reference_image(candidate, candidate.suffix.lower())
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].get(shot_id, {})
            candidate_paths = [
                e["path"] if isinstance(e, dict) else e
                for e in record.get("keyframes", [])
            ]
            if relative not in candidate_paths:
                raise ApplicationConflict("keyframe candidate is invalid")
            record["selected_keyframe"] = relative
            record["keyframe_selected_at"] = datetime.now(timezone.utc).isoformat()
            self._write_shot_references(root, references)
        target, decisions = self._invalidate_decisions(root, {"keyframes", "shots", "delivery"})
        self._write_atomic_file(target, canonical_json(decisions), ".workflow-decision-")
        return self.get_project_workflow(project_id)

    @staticmethod
    def _generated_png(content):
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.load()
                if image.width < 1 or image.height < 1:
                    raise ValueError("empty image")
                output = io.BytesIO()
                image.convert("RGB").save(output, format="PNG", optimize=True)
                return output.getvalue()
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as exc:
            raise ApplicationBlocked("image provider returned an invalid image") from exc

    def _shot_generation_context(self, root, shot_id):
        shot = self._require_shot(root, shot_id)
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml") or {}
        all_shots = [item for item in visual.get("shots", []) if isinstance(item, dict)]
        index = next(i for i, item in enumerate(all_shots) if item.get("id") == shot_id)
        character_map = self._read_structured_file(root / "creative" / "character_map.yaml") or {}
        character_index = {
            item.get("id"): item for item in character_map.get("characters", [])
            if isinstance(item, dict) and item.get("id")
        }
        cast = [
            character_index[value] for value in shot.get("characters", [])
            if value in character_index
        ]
        brief = self._read_structured_file(root / "brief.json") or {}
        music = self._read_structured_file(root / "creative" / "music_map.yaml") or {}
        story = self._read_structured_file(root / "creative" / "story_framework.yaml") or {}
        return {
            "project": {
                "title": brief.get("title", ""), "canvas": brief.get("canvas", "9:16"),
                "resolution": brief.get("resolution", "720p"),
                "creative_direction": brief.get("creative_direction", ""),
            },
            "shot": {
                key: shot.get(key) for key in (
                    "id", "time", "section", "energy", "purpose", "lyric", "composition",
                    "primary_action", "first_frame", "last_frame", "transition_out",
                    "director_beat", "visual_events", "technique",
                )
            },
            "characters": [{
                "id": item.get("id", ""), "name": item.get("name", ""),
                "director_function": item.get("director_function", ""),
                "traits": item.get("traits", []), "source_asset": item.get("source_asset", ""),
            } for item in cast],
            "music_section": next((
                item for item in music.get("sections", [])
                if isinstance(item, dict) and item.get("id") == shot.get("section")
            ), {}),
            "story_section": next((
                item for item in story.get("sections", [])
                if isinstance(item, dict) and item.get("id") == shot.get("section")
            ), {}),
            "continuity": {
                "previous": all_shots[index - 1].get("last_frame", "") if index else "",
                "next": all_shots[index + 1].get("first_frame", "")
                if index + 1 < len(all_shots) else "",
            },
        }

    @staticmethod
    def _classify_translation_error(exc):
        from mvstudio.providers.semantic_openai import SemanticProviderError, SemanticResponseError
        if isinstance(exc, SemanticResponseError):
            fr = exc.finish_reason
            if fr == "length":
                return "truncated"
            if fr == "content_filter":
                return "content_filtered"
            return "invalid_response"
        if isinstance(exc, SemanticProviderError):
            if "timed out" in str(exc).lower():
                return "timeout"
            return "http_error"
        return "unknown"

    def _translate_image_prompt(self, project_id, event_type, context, request_id):
        from mv_platform.application.prompt_catalog import SYSTEM_PREFIX
        from mvstudio.director.drafting import ModelBudget, ModelResult, ModelTask
        from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort

        prompts = self.get_project_prompts(project_id)
        system_text = prompts[SYSTEM_PREFIX + event_type]
        task_text = prompts[event_type]
        source_instruction = system_text.strip() + "\n\n本步骤任务要求：\n" + task_text.strip()
        schema = {"english_prompt": "one complete production-ready English image prompt"}
        payload = {
            "chinese_system_prompt": system_text,
            "chinese_task_prompt": task_text,
            "director_context": context,
        }
        model = self.semantic_model or os.environ.get("LLM_MODEL", "")
        if not model:
            raise ApplicationBlocked("text model is not configured")
        provider = self.semantic_port or OpenAICompatibleSemanticPort.from_env()
        provider_url = getattr(provider, "base_url", "") or ""
        try:
            from urllib.parse import urlparse
            provider_host = urlparse(str(provider_url)).hostname or str(provider_url)
        except Exception:
            provider_host = ""
        task = ModelTask(
            event_type="prompt.translate_requested", model=model,
            budget=ModelBudget(max_input_bytes=65536, max_output_bytes=12000, max_tokens=2200),
            reason="Translate the approved Chinese image direction and its shot context into one English production prompt.",
            input_contract_hash=canonical_hash(payload), output_schema_hash=canonical_hash(schema),
            output_schema=schema, payload=payload,
            instruction=(
                prompts[SYSTEM_PREFIX + "prompt.translate_requested"] + "\n" +
                prompts["prompt.translate_requested"] +
                " Return exactly one english_prompt. Integrate every supplied director_context field; "
                "do not invent identity, costume, lyrics, time, cast, or story facts."
            ),
        )

        _RETRYABLE = {"timeout", "http_error"}

        def _attempt():
            try:
                return provider.run(task)
            except Exception as exc:
                usage = (
                    getattr(exc, "input_tokens", 0), getattr(exc, "cache_read_tokens", 0),
                    getattr(exc, "output_tokens", 0),
                )
                if any(usage):
                    self.record_llm_cost(
                        project_id, None, task.event_type, *usage,
                        {"source_event": event_type, "shot_id": context["shot"]["id"],
                         "model": model, "request_id": request_id, "outcome": "invalid_response"},
                    )
                return exc

        raw = _attempt()
        if isinstance(raw, Exception):
            error_category = self._classify_translation_error(raw)
            if error_category in _RETRYABLE:
                self.error_logs.append("backend", {
                    "event": "image_prompt_translation_retrying",
                    "error_category": error_category,
                    "error_message": str(raw)[:500],
                    "model": model,
                    "request_id": request_id,
                    "shot_id": context["shot"]["id"],
                })
                raw = _attempt()

        if isinstance(raw, Exception):
            exc = raw
            error_category = self._classify_translation_error(exc)
            self.error_logs.append("backend", {
                "event": "image_prompt_translation_failed",
                "error_category": error_category,
                "error_message": str(exc)[:500],
                "finish_reason": getattr(exc, "finish_reason", ""),
                "model": model,
                "provider_base_url": provider_host,
                "request_id": request_id,
                "shot_id": context["shot"]["id"],
                "available_input_tokens": getattr(exc, "input_tokens", 0),
                "available_output_tokens": getattr(exc, "output_tokens", 0),
            })
            raise ApplicationBlocked(
                "image prompt translation failed",
                error_stage="translate_prompt",
                error_category=error_category,
            ) from exc

        result = raw
        if not isinstance(result, ModelResult):
            raise ApplicationBlocked("image prompt translation returned an invalid result")
        english_prompt = result.output.get("english_prompt")
        if not isinstance(english_prompt, str) or not english_prompt.strip():
            raise ApplicationBlocked("image prompt translation returned an invalid result")
        self.record_llm_cost(
            project_id, None, task.event_type, result.input_tokens,
            result.cache_read_tokens, result.output_tokens,
            {"source_event": event_type, "shot_id": context["shot"]["id"],
             "model": model, "request_id": request_id},
        )
        return english_prompt.strip(), {
            "usage": {"input_tokens": result.input_tokens,
                      "cache_read_tokens": result.cache_read_tokens,
                      "output_tokens": result.output_tokens},
            "model": model,
            "source_prompt_hash": "sha256:" + hashlib.sha256(
                source_instruction.encode("utf-8")
            ).hexdigest(),
        }

    def _image_reference_paths(self, root, context, include_background=""):
        values = [include_background] if include_background else []
        values.extend(item.get("source_asset", "") for item in context["characters"])
        paths = []
        for value in values:
            if not isinstance(value, str) or not value:
                continue
            candidate = root / Path(value)
            if candidate.is_symlink() or not candidate.is_file():
                raise ApplicationBlocked("image generation reference is missing")
            try:
                candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
            except (FileNotFoundError, ValueError) as exc:
                raise ApplicationBlocked("image generation reference escapes project") from exc
            paths.append(candidate)
        return paths[:8]

    def _resolve_shot_background(self, root, shot_id) -> str:
        """Resolve a shot's background reference path.

        Falls back to the scene-group background master when the per-shot
        ``background`` field is empty (PRD-007B: ``select_background_master``
        only records ``background_master_id`` on grouped shots, never the
        per-shot ``background`` string). Mirrors the workflow view-model logic.
        """
        shot_ref = self._shot_references(root)["shots"].get(shot_id, {})
        background = shot_ref.get("background", "")
        if isinstance(background, str) and background and (root / background).is_file():
            return background
        bg_master_id = shot_ref.get("background_master_id", "")
        if not bg_master_id:
            return ""
        master_bg = next(
            (
                b for b in self._background_masters(root).get("backgrounds", [])
                if b.get("id") == bg_master_id
            ),
            None,
        )
        if master_bg is None:
            return ""
        bg_path = master_bg.get("relative_path", "")
        if bg_path and (root / bg_path).is_file():
            return bg_path
        return ""

    def _generate_shot_image(self, project_id, shot_id, event_type, output_kind,
                             include_background=False, en_prompt: "str | None" = None):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        context = self._shot_generation_context(root, shot_id)
        references = self._shot_references(root)
        background = references["shots"].get(shot_id, {}).get("background", "")
        if include_background and not background:
            background = self._resolve_shot_background(root, shot_id)
        if include_background and not background:
            raise ApplicationBlocked("shot background is required before keyframe generation")
        context["generation_contract"] = {
            "output": "complete character-and-background first frame"
            if include_background else "background plate without any person",
            "reference_order": (
                "reference image 1 is the approved background; remaining images are character identity, costume and style anchors"
                if include_background else
                "all reference images are character artwork used only to match linework, rendering and world style; do not draw a person"
            ),
            "forbidden": [
                "unapproved characters", "identity drift", "costume changes", "style drift",
                "text", "watermark", "logo", "cheap gradient", "generic decorative filler",
            ],
        }
        request_id = "image-" + uuid.uuid4().hex
        if en_prompt:
            prompt = en_prompt
            translation = {"source_prompt_hash": "", "used": False, "usage": {}}
        else:
            prompt, translation = self._translate_image_prompt(
                project_id, event_type, context, request_id,
            )
        provider = self.image_provider
        if provider is None:
            from mvstudio.providers.image_openai import OpenAICompatibleImageProvider
            try:
                provider = OpenAICompatibleImageProvider.from_env(os.environ)
            except Exception as exc:
                raise ApplicationBlocked("image provider is not configured") from exc
        source_paths = self._image_reference_paths(
            root, context, background if include_background else "",
        )
        canvas = str(context["project"].get("canvas", "9:16"))
        size = "1536x1024" if canvas == "16:9" else "1024x1536"
        provider_completed = False
        try:
            content = provider.generate(prompt, references=source_paths, size=size)
            provider_completed = True
            png = self._generated_png(content)
            relative = Path("assets/generated") / output_kind / (
                shot_id + "-" + request_id[-10:] + ".png"
            )
            self._write_atomic_file(root / relative, png, ".generated-image-")
        except Exception as exc:
            metadata = {
                "shot_id": shot_id, "model": getattr(provider, "model", "gpt-image-2"),
                "request_id": request_id, "outcome": "invalid_output" if provider_completed else "failed",
            }
            if provider_completed:
                self.record_image_cost(project_id, None, event_type, metadata=metadata)
            else:
                self._record_cost(
                    project_id, None, event_type, "image", 0, Decimal("0.5"), 0,
                    metadata=metadata,
                )
            if isinstance(exc, ApplicationBlocked):
                raise
            raise ApplicationBlocked("image generation failed") from exc
        relative_text = relative.as_posix()
        # Re-read shot-references from disk under the lock: the early snapshot
        # read above is now stale (provider.generate can take minutes, during
        # which other jobs may have registered their own keyframes). Merging
        # into the fresh copy prevents a lost-update race that would erase
        # concurrently-generated keyframes on the next write. (PRD-003 bug)
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].setdefault(shot_id, {})
            if output_kind == "backgrounds":
                record["background"] = relative_text
                record["background_bound_at"] = datetime.now(timezone.utc).isoformat()
                invalidated = {"storyboard", "keyframes", "shots", "delivery"}
            else:
                candidates = record.setdefault("keyframes", [])
                existing_paths = [e["path"] if isinstance(e, dict) else e for e in candidates]
                if relative_text not in existing_paths:
                    prompts_catalog = self.get_project_prompts(project_id)
                    prompt_zh = prompts_catalog.get(event_type, "")
                    kf_entry = {
                        "path": relative_text,
                        "source": "generated",
                        "background_master_id": record.get("background_master_id", ""),
                        "character_ids": [c["id"] for c in context.get("characters", []) if isinstance(c, dict) and c.get("id")],
                        "prompt_zh": prompt_zh,
                        "prompt_en": prompt,
                        "model": getattr(provider, "model", ""),
                        "request_id": request_id,
                        "cost_yuan": 0.5,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    candidates.append(kf_entry)
                record["selected_keyframe"] = relative_text
                record["keyframe_selected_at"] = datetime.now(timezone.utc).isoformat()
                invalidated = {"keyframes", "shots", "delivery"}
            self._write_shot_references(root, references)
            target, decisions = self._invalidate_decisions(root, invalidated)
            self._write_atomic_file(target, canonical_json(decisions), ".workflow-decision-")
        self.record_image_cost(
            project_id, None, event_type,
            metadata={"shot_id": shot_id, "model": getattr(provider, "model", "gpt-image-2"),
                      "request_id": request_id, "outcome": "succeeded",
                      "output_path": relative_text},
        )
        self._append_image_generation_audit(root, {
            "event_type": event_type, "shot_id": shot_id,
            "model": getattr(provider, "model", "gpt-image-2"),
            "source_prompt_hash": translation["source_prompt_hash"],
            "usage": {}, "prompt_translation": translation,
            "output_path": relative_text, "request_id": request_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return self.get_project_workflow(project_id)

    # -----------------------------------------------------------------------
    # PRD-002: Scene groups & background masters
    # -----------------------------------------------------------------------

    @staticmethod
    def suggest_scene_groups(shots, story_sections):
        groups = {}
        for shot in shots:
            if not isinstance(shot, dict):
                continue
            section_id = shot.get("section") or "_default"
            groups.setdefault(section_id, []).append(shot.get("id", ""))
        section_names = {
            s["id"]: s.get("emotion", "")
            for s in story_sections
            if isinstance(s, dict) and s.get("id")
        }
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for i, (section_id, shot_ids) in enumerate(groups.items()):
            name = section_names.get(section_id, "") or f"场景{i + 1}"
            result.append(SceneGroup(
                id=f"SG{i + 1:03d}",
                name=name,
                source_section_id=section_id,
                shot_ids=tuple(shot_ids),
                created_by="system",
                created_at=now,
                updated_at=now,
            ))
        return result

    def _migrate_to_scene_groups(self, root):
        """One-time migration: build scene-groups.json from visual_score.yaml."""
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml")
        if not isinstance(visual, dict):
            return
        shots = [s for s in visual.get("shots", []) if isinstance(s, dict)]
        if not shots:
            return
        story = self._read_structured_file(root / "creative" / "story_framework.yaml")
        story_sections = []
        if isinstance(story, dict):
            story_sections = [s for s in story.get("sections", []) if isinstance(s, dict)]

        scene_groups = self.suggest_scene_groups(shots, story_sections)
        sg_list = [
            {
                "id": sg.id, "name": sg.name, "location": sg.location,
                "time_of_day": sg.time_of_day, "weather": sg.weather,
                "emotional_state": sg.emotional_state,
                "narrative_world_state": sg.narrative_world_state,
                "source_section_id": sg.source_section_id,
                "shot_ids": list(sg.shot_ids),
                "created_by": sg.created_by,
                "created_at": sg.created_at, "updated_at": sg.updated_at,
            }
            for sg in scene_groups
        ]
        shot_to_sg = {
            sid: sg.id
            for sg in scene_groups
            for sid in sg.shot_ids
        }

        references = self._shot_references(root)
        backgrounds = []
        bg_counter = 0
        shot_to_bg = {}
        now = datetime.now(timezone.utc).isoformat()

        for shot_id, shot_ref in references.get("shots", {}).items():
            if not isinstance(shot_ref, dict):
                continue
            bg_path = shot_ref.get("background", "")
            if not bg_path:
                continue
            sg_id = shot_to_sg.get(shot_id, "")
            if not sg_id:
                continue
            existing_bg = next(
                (b for b in backgrounds if b.get("relative_path") == bg_path and b.get("scene_group_id") == sg_id),
                None,
            )
            if existing_bg is None:
                bg_counter += 1
                bg_id = f"BG{bg_counter:03d}"
                backgrounds.append({
                    "id": bg_id, "scene_group_id": sg_id,
                    "status": "candidate", "source": "uploaded",
                    "relative_path": bg_path,
                    "prompt_zh": "", "prompt_en": "", "model": "",
                    "request_id": "", "cost_yuan": 0.0, "created_at": now,
                })
                shot_to_bg[shot_id] = bg_id
            else:
                shot_to_bg[shot_id] = existing_bg["id"]

        # Only one selected per scene group: the last one wins
        sg_selected = {}
        for shot_id, bg_id in shot_to_bg.items():
            sg_id = shot_to_sg.get(shot_id, "")
            if sg_id:
                sg_selected[sg_id] = bg_id
        for bg in backgrounds:
            if bg["id"] in sg_selected.values() and sg_selected.get(bg["scene_group_id"]) == bg["id"]:
                bg["status"] = "selected"

        new_shots = {}
        for shot_id, shot_ref in references.get("shots", {}).items():
            entry = dict(shot_ref)
            if shot_id in shot_to_bg:
                entry.setdefault("background_master_id", shot_to_bg[shot_id])
                entry.setdefault("background_variant", {
                    "shot_size": "", "camera_angle": "",
                    "lighting_note": "", "prop_note": "", "crop_note": "",
                })
            new_shots[shot_id] = entry

        new_references = dict(references)
        new_references["version"] = 2
        new_references["shots"] = new_shots

        now_ts = datetime.now(timezone.utc).isoformat()
        sg_doc = {
            "version": 1, "generated_by": "system_heuristic",
            "generated_at": now_ts, "scene_groups": sg_list,
        }
        bg_doc = {"version": 1, "backgrounds": backgrounds}

        try:
            self._write_scene_groups(root, sg_doc)
            self._write_background_masters(root, bg_doc)
            self._write_shot_references(root, new_references)
        except Exception:
            logger.exception("scene_group_migration_failed")

    def get_scene_groups(self, project_id):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sg_doc = self._scene_groups(root)
        if sg_doc is None:
            return {"version": 1, "generated_by": "none",
                    "generated_at": "", "scene_groups": []}
        bg_doc = self._background_masters(root)
        bgs_by_sg = {}
        for bg in bg_doc.get("backgrounds", []):
            bgs_by_sg.setdefault(bg.get("scene_group_id", ""), []).append(bg)
        result = []
        for sg in sg_doc.get("scene_groups", []):
            sg_entry = dict(sg)
            sg_entry["backgrounds"] = bgs_by_sg.get(sg.get("id", ""), [])
            result.append(sg_entry)
        return {
            "version": sg_doc.get("version", 1),
            "generated_by": sg_doc.get("generated_by", ""),
            "generated_at": sg_doc.get("generated_at", ""),
            "scene_groups": result,
        }

    def suggest_and_save_scene_groups(self, project_id):
        """Run heuristic suggestion and write scene-groups.json; returns workflow."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("storyboard", {}).get("action") != "approve":
            raise ApplicationBlocked("storyboard approval is required before suggesting scene groups")
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml")
        if not isinstance(visual, dict):
            raise ApplicationBlocked("visual_score.yaml is missing; run planning first")
        shots = [s for s in visual.get("shots", []) if isinstance(s, dict)]
        story = self._read_structured_file(root / "creative" / "story_framework.yaml")
        story_sections = []
        if isinstance(story, dict):
            story_sections = [s for s in story.get("sections", []) if isinstance(s, dict)]
        scene_groups = self.suggest_scene_groups(shots, story_sections)
        sg_list = [
            {
                "id": sg.id, "name": sg.name, "location": sg.location,
                "time_of_day": sg.time_of_day, "weather": sg.weather,
                "emotional_state": sg.emotional_state,
                "narrative_world_state": sg.narrative_world_state,
                "source_section_id": sg.source_section_id,
                "shot_ids": list(sg.shot_ids),
                "created_by": sg.created_by,
                "created_at": sg.created_at, "updated_at": sg.updated_at,
            }
            for sg in scene_groups
        ]
        now_ts = datetime.now(timezone.utc).isoformat()
        sg_doc = {
            "version": 1, "generated_by": "system_heuristic",
            "generated_at": now_ts, "scene_groups": sg_list,
        }
        self._write_scene_groups(root, sg_doc)
        return self.get_project_workflow(project_id)

    def update_scene_group(self, project_id, sg_id, name=None, shot_ids=None):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sg_doc = self._scene_groups(root)
        if sg_doc is None:
            raise ApplicationNotFound(sg_id)
        groups = sg_doc.get("scene_groups", [])
        target = next((g for g in groups if g.get("id") == sg_id), None)
        if target is None:
            raise ApplicationNotFound(sg_id)
        if name is not None:
            if not isinstance(name, str) or not name.strip() or len(name) > 40:
                raise ApplicationConflict("scene group name is invalid")
            target["name"] = name.strip()
        if shot_ids is not None:
            if not isinstance(shot_ids, list):
                raise ApplicationConflict("shot_ids must be a list")
            # Remove these shots from other groups first
            for grp in groups:
                if grp.get("id") != sg_id:
                    grp["shot_ids"] = [s for s in grp.get("shot_ids", []) if s not in shot_ids]
            target["shot_ids"] = shot_ids
        target["updated_at"] = datetime.now(timezone.utc).isoformat()
        sg_doc["scene_groups"] = groups
        self._write_scene_groups(root, sg_doc)
        return self.get_project_workflow(project_id)

    def merge_scene_groups(self, project_id, source_ids, target_name):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sg_doc = self._scene_groups(root)
        if sg_doc is None:
            raise ApplicationNotFound("scene groups")
        if not isinstance(source_ids, list) or len(source_ids) < 2:
            raise ApplicationConflict("merge requires at least two source_ids")
        groups = sg_doc.get("scene_groups", [])
        to_merge = [g for g in groups if g.get("id") in source_ids]
        if len(to_merge) < 2:
            raise ApplicationNotFound("one or more source scene groups not found")
        merged_shots = []
        for g in to_merge:
            merged_shots.extend(g.get("shot_ids", []))
        now = datetime.now(timezone.utc).isoformat()
        new_id = to_merge[0]["id"]
        merged_group = {
            "id": new_id,
            "name": (target_name or to_merge[0].get("name", "合并场景")).strip(),
            "location": "", "time_of_day": "", "weather": "",
            "emotional_state": "", "narrative_world_state": "",
            "source_section_id": to_merge[0].get("source_section_id", ""),
            "shot_ids": merged_shots,
            "created_by": "user", "created_at": now, "updated_at": now,
        }
        remaining = [g for g in groups if g.get("id") not in source_ids]
        remaining.insert(0, merged_group)
        sg_doc["scene_groups"] = remaining
        self._write_scene_groups(root, sg_doc)
        return self.get_project_workflow(project_id)

    def select_background_master(self, project_id, sg_id, bg_id):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        bg_doc = self._background_masters(root)
        backgrounds = bg_doc.get("backgrounds", [])
        target = next((b for b in backgrounds if b.get("id") == bg_id), None)
        if target is None:
            raise ApplicationNotFound(bg_id)
        if target.get("scene_group_id") != sg_id:
            raise ApplicationConflict("background does not belong to this scene group")
        for bg in backgrounds:
            if bg.get("scene_group_id") == sg_id:
                bg["status"] = "candidate"
        target["status"] = "selected"
        bg_doc["backgrounds"] = backgrounds
        self._write_background_masters(root, bg_doc)
        # Auto-update shots in this scene group (PRD-007B §4.6)
        sg_doc = self._scene_groups(root)
        shots_updated = []
        if sg_doc is not None:
            target_sg = next((g for g in sg_doc.get("scene_groups", []) if g.get("id") == sg_id), None)
            if target_sg:
                refs = self._shot_references(root)
                for sid in target_sg.get("shot_ids", []):
                    record = refs["shots"].setdefault(sid, {})
                    record["background_master_id"] = bg_id
                    shots_updated.append(sid)
                self._write_shot_references(root, refs)
        return {"group_id": sg_id, "master_id": bg_id, "shots_updated": shots_updated}

    def generate_scene_group_background(self, project_id, sg_id):
        """Generate a background image for a scene group (PRD-002 §6.1)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("storyboard", {}).get("action") != "approve":
            raise ApplicationBlocked("storyboard approval is required before background generation")
        sg_doc = self._scene_groups(root)
        if sg_doc is None:
            raise ApplicationBlocked(
                "请先在场景与背景阶段建立场景组",
                error_stage="precondition",
            )
        target_sg = next(
            (g for g in sg_doc.get("scene_groups", []) if g.get("id") == sg_id),
            None,
        )
        if target_sg is None:
            raise ApplicationNotFound(sg_id)
        shot_ids = target_sg.get("shot_ids", [])
        if not shot_ids:
            raise ApplicationBlocked(
                "场景组内没有分镜，无法生成背景",
                error_stage="precondition",
            )
        representative_shot_id = shot_ids[0]
        workflow = self._generate_shot_image(
            project_id, representative_shot_id,
            "image.background.generate_requested", "backgrounds",
        )
        # Move the generated background into background-masters.json
        references = self._shot_references(root)
        new_bg_path = references["shots"].get(representative_shot_id, {}).get("background", "")
        if new_bg_path:
            bg_doc = self._background_masters(root)
            existing_ids = [b.get("id", "") for b in bg_doc.get("backgrounds", [])]
            counter = len(existing_ids) + 1
            while f"BG{counter:03d}" in existing_ids:
                counter += 1
            bg_id = f"BG{counter:03d}"
            now = datetime.now(timezone.utc).isoformat()
            bg_doc.setdefault("backgrounds", []).append({
                "id": bg_id, "scene_group_id": sg_id,
                "status": "candidate", "source": "generated",
                "relative_path": new_bg_path,
                "prompt_zh": "", "prompt_en": "", "model": "",
                "request_id": "", "cost_yuan": 0.5, "created_at": now,
            })
            self._write_background_masters(root, bg_doc)
        return self.get_project_workflow(project_id)

    _DEFAULT_SCENE_GROUP_SYSTEM_PROMPT = (
        '你是一位专业的影视分镜分析师。\n'
        '根据分镜描述，将镜头按“背景场景组”归类：同一地点、相近时间段、背景视觉高度相似的镜头归为一组。\n'
        '每组给出一个简短名称（格式：地点-时段，如“书房-白天”）和一句背景描述提示词（中文，≤50字）。\n'
        '输出 JSON 数组，每项包含 group_name, shots(镜头编号数组), prompt_zh。不要输出任何其他内容。'
    )

    def suggest_scene_groups_llm(self, project_id: str,
                                  system_prompt: "str | None" = None,
                                  task_prompt: "str | None" = None) -> dict:
        """LLM-based scene group suggestion (PRD-007B §4.1)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("storyboard", {}).get("action") != "approve":
            raise ApplicationBlocked("storyboard approval required before scene planning")
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml") or {}
        all_shots = [s for s in (visual.get("shots", []) if isinstance(visual, dict) else []) if isinstance(s, dict)]
        if not all_shots:
            raise ApplicationBlocked("no shots found in visual score")
        shots_json = json.dumps(
            [{"id": s.get("id", ""), "purpose": s.get("purpose", ""), "section": s.get("section", "")} for s in all_shots],
            ensure_ascii=False,
        )
        sys_p = system_prompt or self._DEFAULT_SCENE_GROUP_SYSTEM_PROMPT
        task_p = task_prompt or (
            f"以下是分镜列表，请按场景组归类：\n\n{shots_json}\n\n"
            "要求：不遗漏任何镜头，每个镜头只能属于一个组。"
        )
        from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort
        from mvstudio.director.drafting import ModelBudget, ModelTask
        model = self.semantic_model or os.environ.get("LLM_MODEL", "")
        if not model:
            raise ApplicationBlocked("LLM not configured", error_stage="configuration")
        try:
            provider = self.semantic_port or OpenAICompatibleSemanticPort.from_env()
        except Exception as exc:
            raise ApplicationBlocked("LLM provider not configured", error_stage="configuration") from exc
        schema = {"groups": [{"group_name": "str", "shots": ["str"], "prompt_zh": "str"}]}
        payload = {"system_prompt": sys_p, "task_prompt": task_p, "shots": shots_json}
        task = ModelTask(
            event_type="scene_group.suggest_requested", model=model,
            budget=ModelBudget(max_input_bytes=65536, max_output_bytes=32000, max_tokens=4000),
            reason="Cluster storyboard shots into background scene groups.",
            input_contract_hash=canonical_hash(payload),
            output_schema_hash=canonical_hash(schema),
            output_schema=schema, payload=payload,
            instruction=sys_p + "\n\n" + task_p + "\n\nReturn a JSON object of the form {\"groups\": [{\"group_name\":\"...\",\"shots\":[\"S001\",...],\"prompt_zh\":\"...\"}]}",
        )
        try:
            result = provider.run(task)
        except Exception as exc:
            raise ApplicationBlocked(f"LLM call failed: {exc}", error_stage="translate_prompt") from exc
        output = getattr(result, "output", None) or {}
        groups_raw = output.get("groups") if isinstance(output, dict) else None
        if not isinstance(groups_raw, list):
            raise ApplicationBlocked("LLM returned no valid groups")
        all_shot_ids = {s.get("id", "") for s in all_shots}
        assigned: set = set()
        groups = []
        now = datetime.now(timezone.utc).isoformat()
        for i, g in enumerate(groups_raw):
            gid = f"SG{i+1:03d}"
            shot_ids = [s for s in (g.get("shots") or []) if s in all_shot_ids]
            assigned.update(shot_ids)
            groups.append({
                "group_id": gid, "name": g.get("group_name", f"场景组{i+1}"),
                "shots": shot_ids, "prompt_zh": g.get("prompt_zh", ""),
                "notes": "LLM 建议", "locked": False,
                "created_at": now, "updated_at": now,
            })
        uncategorized = list(all_shot_ids - assigned)
        if uncategorized:
            groups.append({
                "group_id": f"SG{len(groups)+1:03d}", "name": "未分组",
                "shots": sorted(uncategorized), "prompt_zh": "", "notes": "待分配",
                "locked": False, "created_at": now, "updated_at": now,
            })
        sp_data = {
            "version": 1, "status": "draft",
            "groups": groups,
            "llm_suggestion_used": True,
            "system_prompt": sys_p, "task_prompt": task_p,
            "generated_at": now,
        }
        self._write_scene_planning(root, sp_data)
        return {"groups": groups, "system_prompt": sys_p, "task_prompt": task_p}

    def get_scene_planning(self, project_id: str) -> dict:
        """Return current scene planning data (PRD-007B §4.0)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sp = self._scene_planning(root)
        if sp is None:
            return {"status": "not_started", "groups": []}
        return sp

    def update_scene_planning(self, project_id: str, payload: dict) -> dict:
        """Update scene group plan (PRD-007B §4.2)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sp = self._scene_planning(root) or {"version": 1, "status": "draft", "groups": [], "llm_suggestion_used": False}
        action = payload.get("action")
        now = datetime.now(timezone.utc).isoformat()
        if action == "regenerate_suggestion":
            return self.suggest_scene_groups_llm(
                project_id,
                system_prompt=payload.get("system_prompt"),
                task_prompt=payload.get("task_prompt"),
            )
        elif action == "update_groups":
            raw_groups = payload.get("groups", [])
            groups = []
            existing_ids = {g["group_id"] for g in sp.get("groups", []) if "group_id" in g}
            counter = len(existing_ids) + 1
            for g in raw_groups:
                gid = g.get("group_id")
                if not gid:
                    while f"SG{counter:03d}" in existing_ids:
                        counter += 1
                    gid = f"SG{counter:03d}"
                    existing_ids.add(gid)
                    counter += 1
                groups.append({
                    "group_id": gid,
                    "name": g.get("name") or g.get("group_name", "场景组"),
                    "shots": g.get("shots", []),
                    "prompt_zh": g.get("prompt_zh", ""),
                    "notes": g.get("notes", ""),
                    "locked": bool(g.get("locked", False)),
                    "created_at": g.get("created_at", now),
                    "updated_at": now,
                })
            sp["groups"] = groups
            sp["status"] = "draft"
            sp["updated_at"] = now
            self._write_scene_planning(root, sp)
            return {"groups": groups}
        else:
            raise ApplicationBlocked(f"unknown action: {action}")

    def approve_scene_planning(self, project_id: str) -> dict:
        """Approve scene planning and propagate to shots (PRD-007B §4.3)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sp = self._scene_planning(root)
        if sp is None:
            raise ApplicationBlocked("no scene planning data found; run suggest or update first")
        visual = self._read_structured_file(root / "creative" / "visual_score.yaml") or {}
        all_shot_ids = {s.get("id", "") for s in (visual.get("shots", []) if isinstance(visual, dict) else []) if isinstance(s, dict)}
        groups = sp.get("groups", [])
        assigned = {sid for g in groups for sid in g.get("shots", [])}
        uncategorized = all_shot_ids - assigned
        if uncategorized:
            raise ApplicationBlocked(
                f"uncategorized shots: {sorted(uncategorized)}",
                error_stage="precondition",
            )
        refs = self._shot_references(root)
        for g in groups:
            gid = g["group_id"]
            for sid in g.get("shots", []):
                record = refs["shots"].setdefault(sid, {})
                record["scene_group_id"] = gid
                if "background_override" not in record:
                    record["background_override"] = None
        self._write_shot_references(root, refs)
        now = datetime.now(timezone.utc).isoformat()
        sg_doc = {
            "version": 1, "generated_by": "scene_planning", "generated_at": now,
            "scene_groups": [
                {
                    "id": g["group_id"], "name": g["name"],
                    "source_section_id": "",
                    "shot_ids": g["shots"],
                    "location": "", "time_of_day": "", "weather": "",
                    "emotional_state": "", "narrative_world_state": "",
                    "created_by": "user", "created_at": g.get("created_at", now), "updated_at": now,
                }
                for g in groups
            ],
        }
        self._write_scene_groups(root, sg_doc)
        sp["status"] = "approved"
        sp["approved_at"] = now
        self._write_scene_planning(root, sp)
        return {"status": "approved", "groups": len(groups), "shots_assigned": len(assigned)}

    def submit_generate_group_background_job(self, project_id: str, group_id: str) -> dict:
        """Submit 2 candidate background generation jobs for a scene group (PRD-007B §4.5)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        sp = self._scene_planning(root)
        if sp is None or sp.get("status") != "approved":
            raise ApplicationBlocked("scene_planning must be approved before group background generation")
        sg_doc = self._scene_groups(root)
        if sg_doc is None:
            raise ApplicationBlocked("no scene groups found")
        target_sg = next((g for g in sg_doc.get("scene_groups", []) if g.get("id") == group_id), None)
        if target_sg is None:
            raise ApplicationNotFound(group_id)
        shot_ids = target_sg.get("shot_ids", [])
        if not shot_ids:
            raise ApplicationBlocked("scene group has no shots")
        representative_shot_id = shot_ids[0]
        job_ids = []
        for _ in range(2):
            result = self.submit_generate_background_job(project_id, representative_shot_id)
            job_ids.append(result["job_id"])
        return {"group_id": group_id, "job_ids": job_ids, "status": "queued"}

    def set_shot_background_override(self, project_id: str, shot_id: str, override_path: "str | None") -> dict:
        """Set or clear a per-shot background override (PRD-007B §4.7)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        refs = self._shot_references(root)
        record = refs["shots"].setdefault(shot_id, {})
        record["background_override"] = override_path
        self._write_shot_references(root, refs)
        return {
            "shot_id": shot_id,
            "background_master_id": record.get("background_master_id", ""),
            "background_override": override_path,
        }

    def generate_shot_background(self, project_id, shot_id, en_prompt: "str | None" = None):
        # DEPRECATED: use scene-group level generation
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        sg_doc = self._scene_groups(root)
        if sg_doc is not None:
            target_sg = next(
                (
                    g for g in sg_doc.get("scene_groups", [])
                    if shot_id in g.get("shot_ids", [])
                ),
                None,
            )
            if target_sg is None:
                raise ApplicationBlocked(
                    "请先在场景与背景阶段建立场景组",
                    error_stage="precondition",
                )
            return self.generate_scene_group_background(project_id, target_sg["id"])
        if decisions.get("story", {}).get("action") != "approve":
            raise ApplicationBlocked("story approval is required before background generation")
        return self._generate_shot_image(
            project_id, shot_id, "image.background.generate_requested", "backgrounds",
            en_prompt=en_prompt,
        )

    def generate_shot_keyframe(self, project_id, shot_id, en_prompt: "str | None" = None):
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("scenes", {}).get("action") != "approve":
            raise ApplicationBlocked(
                "scenes approval is required before keyframe generation",
                error_stage="precondition", error_category="precondition",
            )
        references = self._shot_references(root)
        shot_record = references["shots"].get(shot_id, {})
        if not shot_record.get("background_master_id"):
            raise ApplicationBlocked(
                "shot has no background master, please complete scenes stage first",
                error_stage="precondition", error_category="precondition",
            )
        return self._generate_shot_image(
            project_id, shot_id, "image.keyframe.generate_requested", "keyframes",
            include_background=True, en_prompt=en_prompt,
        )

    def generate_shot_video(self, project_id: str, shot_id: str, duration: int = 5):
        """Generate a video for a shot via the configured video provider (PRD-004)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("scenes", {}).get("action") != "approve":
            raise ApplicationBlocked(
                "scenes approval is required before video generation",
                error_stage="precondition", error_category="precondition",
            )
        references = self._shot_references(root)
        shot_ref = references["shots"].get(shot_id, {})
        selected_kf = shot_ref.get("selected_keyframe", "")
        if not selected_kf:
            raise ApplicationBlocked(
                "shot has no selected keyframe, please complete keyframes stage first",
                error_stage="precondition", error_category="precondition",
            )
        kf_path = root / selected_kf
        if not kf_path.exists():
            raise ApplicationBlocked(
                "selected keyframe file not found on disk",
                error_stage="precondition", error_category="precondition",
            )
        if not os.environ.get("SEEDANCE_BASE_URL"):
            raise ApplicationBlocked(
                "Seedance provider not configured",
                error_stage="configuration", error_category="configuration",
            )
        provider = getattr(self, "video_provider", None)
        if provider is None:
            try:
                from mvstudio.providers.seedance import SeedancePort
                provider = SeedancePort.from_env()
            except Exception as exc:
                raise ApplicationBlocked(f"video provider is not configured: {exc}") from exc
        task_id = "task-" + uuid.uuid4().hex[:12]
        try:
            from mvstudio.providers.seedance import SeedanceTask, SeedanceFrame
            kf_bytes = kf_path.read_bytes()
            import hashlib
            kf_sha256 = "sha256:" + hashlib.sha256(kf_bytes).hexdigest()
            brief = self._read_structured_file(root / "brief.json") or {}
            proj_canvas = str(brief.get("canvas", "9:16"))
            proj_resolution = str(brief.get("resolution", "720p"))
            visual = self._read_structured_file(root / "creative" / "visual_score.yaml") or {}
            shot_data = next(
                (s for s in (visual.get("shots", []) if isinstance(visual, dict) else []) if isinstance(s, dict) and s.get("id") == shot_id),
                {},
            )
            shot_prompt = (
                shot_data.get("primary_action")
                or shot_data.get("purpose")
                or shot_data.get("first_frame")
                or f"Shot {shot_id} motion"
            )
            seedance_task = SeedanceTask(
                shot_id=shot_id,
                model=os.environ.get("SEEDANCE_MODEL", "doubao-seedance-2-0-260128"),
                prompt=shot_prompt,
                duration_seconds=int(duration),
                first_frame=SeedanceFrame(content=kf_bytes, sha256=kf_sha256),
                aspect_ratio=proj_canvas,
                resolution=proj_resolution,
            )
            result = provider.generate(seedance_task)
            video_bytes = result.video_bytes
        except Exception as exc:
            raise ApplicationBlocked(f"video generation failed: {exc}") from exc
        qc_passed, qc_info = self._qc_video(video_bytes, duration)
        relative = Path("assets/generated/videos") / (
            shot_id + "-" + task_id[-10:] + ".mp4"
        )
        self._write_atomic_file(root / relative, video_bytes, ".generated-video-")
        relative_text = relative.as_posix()
        # Re-read under the lock: the snapshot read before provider.generate is
        # stale and would clobber concurrent keyframe/video registrations.
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].setdefault(shot_id, {})
            entry = {
                "path": relative_text,
                "source_keyframe": selected_kf,
                "duration_requested": duration,
                "duration_actual": qc_info["duration_actual"],
                "resolution": proj_resolution,
                "file_size_bytes": qc_info["file_size_bytes"],
                "model": os.environ.get("SEEDANCE_MODEL", ""),
                "task_id": task_id,
                "cost_yuan": round(duration * 0.8, 2),
                "qc_passed": qc_passed,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            record.setdefault("video_entries", []).append(entry)
            if not record.get("selected_video"):
                record["selected_video"] = relative_text
            self._write_shot_references(root, references)
        return self.get_project_workflow(project_id)

    def select_shot_video(self, project_id: str, shot_id: str, path: str):
        """Set selected_video for a shot (PRD-004)."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        with self._shot_references_lock:
            references = self._shot_references(root)
            record = references["shots"].get(shot_id, {})
            candidate_paths = [
                e["path"] for e in record.get("video_entries", [])
                if isinstance(e, dict) and e.get("path")
            ]
            if path not in candidate_paths:
                raise ApplicationConflict("video candidate is invalid")
            record["selected_video"] = path
            record["video_selected_at"] = datetime.now(timezone.utc).isoformat()
            references["shots"][shot_id] = record
            self._write_shot_references(root, references)
        return self.get_project_workflow(project_id)

    def ping_video_provider(self) -> dict:
        """Test Seedance provider connectivity (PRD-004)."""
        import time
        base_url = os.environ.get("SEEDANCE_BASE_URL", "")
        model = os.environ.get("SEEDANCE_MODEL", "seedance-2.0")
        if not base_url:
            return {"provider": "seedance", "reachable": False, "model": model,
                    "latency_ms": 0, "error": "SEEDANCE_BASE_URL not configured"}
        start = time.time()
        try:
            import urllib.request
            req = urllib.request.Request(
                base_url.rstrip("/") + "/health",
                method="GET",
            )
            req.add_header("User-Agent", "mvstudio-ping/1")
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            latency_ms = round((time.time() - start) * 1000)
            return {"provider": "seedance", "reachable": True, "model": model,
                    "latency_ms": latency_ms, "error": ""}
        except Exception as exc:
            latency_ms = round((time.time() - start) * 1000)
            return {"provider": "seedance", "reachable": False, "model": model,
                    "latency_ms": latency_ms, "error": str(exc)}

    # -----------------------------------------------------------------------
    # PRD-005: SSE streaming – mini-job infrastructure
    # -----------------------------------------------------------------------

    def _emit_mini_event(self, job_id: str, event_type: str, payload: dict):
        """Append a progress/done/error SSE event for a mini image-gen job."""
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT COALESCE(MAX(seq),0) FROM events WHERE job_id=?", (job_id,)
            ).fetchone()
            seq = row[0] + 1
            db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (job_id, seq, event_type, now, json.dumps(payload, ensure_ascii=False)),
            )
            db.commit()

    def _set_mini_job_state(self, job_id: str, state: str):
        """Update runtime_state for a mini image-gen job."""
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as db:
            db.execute(
                "UPDATE job_status SET runtime_state=?, updated_at=? WHERE job_id=?",
                (state, now, job_id),
            )
            db.commit()

    @staticmethod
    def _encode_en_prompt(en_prompt: str) -> str:
        import base64
        encoded = base64.urlsafe_b64encode(en_prompt.encode("utf-8")).decode("ascii").rstrip("=")
        return "b64prompt:" + encoded

    @staticmethod
    def _decode_en_prompt(refs) -> "str | None":
        import base64
        for ref in refs:
            if isinstance(ref, str) and ref.startswith("b64prompt:"):
                padded = ref[10:] + "=="
                try:
                    return base64.urlsafe_b64decode(padded).decode("utf-8")
                except Exception:
                    return None
        return None

    def _translate_prompt(self, project_id: str, shot_id: str, event_type: str) -> str:
        """Translate shot prompt to English (thin wrapper; monkeypatchable in tests)."""
        _project, root = self._project_directory(project_id)
        context = self._shot_generation_context(root, shot_id)
        request_id = "translate-" + uuid.uuid4().hex[:12]
        prompt, _translation = self._translate_image_prompt(
            project_id, event_type, context, request_id,
        )
        return prompt

    def submit_generate_background_job(self, project_id: str, shot_id: str, en_prompt: "str | None" = None) -> dict:
        """Create an async background-generation job, return immediately with job_id."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        sg_doc = self._scene_groups(root)
        if sg_doc is not None:
            target_sg = next(
                (g for g in sg_doc.get("scene_groups", []) if shot_id in g.get("shot_ids", [])),
                None,
            )
            if target_sg is None:
                raise ApplicationBlocked(
                    "请先在场景与背景阶段建立场景组",
                    error_stage="precondition",
                )
        elif decisions.get("story", {}).get("action") != "approve":
            raise ApplicationBlocked(
                "story approval is required before background generation",
                error_stage="precondition",
            )
        now_s = datetime.now(timezone.utc).isoformat()
        input_refs: tuple = (shot_id,)
        if en_prompt:
            input_refs = (shot_id, self._encode_en_prompt(en_prompt))
        input_digest = "sha256:" + hashlib.sha256(
            f"bg:{project_id}:{shot_id}:{now_s}".encode()
        ).hexdigest()
        result = self.submit_job(
            project_id, "generate_background", input_digest,
            input_refs=input_refs,
            idempotency_key="imgbg-" + uuid.uuid4().hex,
        )
        return {"job_id": result.job_id, "status": "queued"}

    def submit_generate_keyframe_job(self, project_id: str, shot_id: str, en_prompt: "str | None" = None) -> dict:
        """Create an async keyframe-generation job, return immediately with job_id."""
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        decisions = self._workflow_decisions(root)
        if decisions.get("scenes", {}).get("action") != "approve":
            raise ApplicationBlocked(
                "scenes approval is required before keyframe generation",
                error_stage="precondition", error_category="precondition",
            )
        references = self._shot_references(root)
        shot_record = references["shots"].get(shot_id, {})
        if not shot_record.get("background_master_id"):
            raise ApplicationBlocked(
                "shot has no background master, please complete scenes stage first",
                error_stage="precondition", error_category="precondition",
            )
        now_s = datetime.now(timezone.utc).isoformat()
        input_refs: tuple = (shot_id,)
        if en_prompt:
            input_refs = (shot_id, self._encode_en_prompt(en_prompt))
        input_digest = "sha256:" + hashlib.sha256(
            f"kf:{project_id}:{shot_id}:{now_s}".encode()
        ).hexdigest()
        result = self.submit_job(
            project_id, "generate_keyframe", input_digest,
            input_refs=input_refs,
            idempotency_key="imgkf-" + uuid.uuid4().hex,
        )
        return {"job_id": result.job_id, "status": "queued"}

    def run_generate_background_job(self, job_id: str):
        """Execute a queued background-generation job (called by API background task)."""
        try:
            spec = self.repository.get_job(job_id)
        except RepositoryNotFound:
            return
        shot_id = spec.input_refs[0] if spec.input_refs else ""
        en_prompt = self._decode_en_prompt(spec.input_refs)
        self._execute_background_job(job_id, spec.project_id, shot_id, en_prompt=en_prompt)

    def run_generate_keyframe_job(self, job_id: str):
        """Execute a queued keyframe-generation job (called by API background task)."""
        try:
            spec = self.repository.get_job(job_id)
        except RepositoryNotFound:
            return
        shot_id = spec.input_refs[0] if spec.input_refs else ""
        en_prompt = self._decode_en_prompt(spec.input_refs)
        self._execute_keyframe_job(job_id, spec.project_id, shot_id, en_prompt=en_prompt)

    def _execute_background_job(self, job_id: str, project_id: str, shot_id: str, en_prompt: "str | None" = None):
        self._set_mini_job_state(job_id, "running")
        try:
            if en_prompt:
                self._emit_mini_event(job_id, "progress", {
                    "stage": "generate_image", "pct": 40, "message": "正在调用图片模型...",
                })
            else:
                self._emit_mini_event(job_id, "progress", {
                    "stage": "translate_prompt", "pct": 10, "message": "正在翻译提示词...",
                })
                en_prompt = self._translate_prompt(
                    project_id, shot_id, "image.background.generate_requested",
                )
                self._emit_mini_event(job_id, "progress", {
                    "stage": "translate_prompt", "pct": 30,
                    "message": "提示词翻译完成", "en_prompt": en_prompt,
                })
                self._emit_mini_event(job_id, "progress", {
                    "stage": "generate_image", "pct": 40, "message": "正在调用图片模型...",
                })
            self.generate_shot_background(project_id, shot_id, en_prompt=en_prompt)
            self._emit_mini_event(job_id, "done", {
                "stage": "save_result", "pct": 100, "message": "已保存",
            })
            self._set_mini_job_state(job_id, "succeeded")
        except Exception as exc:
            err_stage = getattr(exc, "error_stage", "") or "generate_image"
            err_cat = getattr(exc, "error_category", "") or "generation_failed"
            self._emit_mini_event(job_id, "error", {
                "stage": err_stage,
                "error_category": err_cat,
                "message": str(exc),
            })
            self._set_mini_job_state(job_id, "failed")

    def _execute_keyframe_job(self, job_id: str, project_id: str, shot_id: str, en_prompt: "str | None" = None):
        self._set_mini_job_state(job_id, "running")
        try:
            if en_prompt:
                self._emit_mini_event(job_id, "progress", {
                    "stage": "generate_image", "pct": 40, "message": "正在调用图片模型...",
                })
            else:
                self._emit_mini_event(job_id, "progress", {
                    "stage": "translate_prompt", "pct": 10, "message": "正在翻译提示词...",
                })
                en_prompt = self._translate_prompt(
                    project_id, shot_id, "image.keyframe.generate_requested",
                )
                self._emit_mini_event(job_id, "progress", {
                    "stage": "translate_prompt", "pct": 30,
                    "message": "提示词翻译完成", "en_prompt": en_prompt,
                })
                self._emit_mini_event(job_id, "progress", {
                    "stage": "generate_image", "pct": 40, "message": "正在调用图片模型...",
                })
            self.generate_shot_keyframe(project_id, shot_id, en_prompt=en_prompt)
            self._emit_mini_event(job_id, "done", {
                "stage": "save_result", "pct": 100, "message": "已保存",
            })
            self._set_mini_job_state(job_id, "succeeded")
        except Exception as exc:
            err_stage = getattr(exc, "error_stage", "") or "generate_image"
            err_cat = getattr(exc, "error_category", "") or "generation_failed"
            self._emit_mini_event(job_id, "error", {
                "stage": err_stage,
                "error_category": err_cat,
                "message": str(exc),
            })
            self._set_mini_job_state(job_id, "failed")

    def _run_pending_jobs_sync(self):
        """Execute all queued image-gen jobs synchronously (test helper)."""
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT jobs.job_id, jobs.project_id, jobs.operation, jobs.input_refs "
                "FROM jobs JOIN job_status ON job_status.job_id=jobs.job_id "
                "WHERE job_status.runtime_state='queued' "
                "AND jobs.operation IN ('generate_background', 'generate_keyframe')"
            ).fetchall()
        for row in rows:
            job_id, project_id, operation, input_refs_str = row
            params = json.loads(input_refs_str)
            shot_id = params[0] if params else ""
            en_prompt = self._decode_en_prompt(params)
            if operation == "generate_background":
                self._execute_background_job(job_id, project_id, shot_id, en_prompt=en_prompt)
            else:
                self._execute_keyframe_job(job_id, project_id, shot_id, en_prompt=en_prompt)

    def _removed_project_assets(self, root):
        value = self._read_structured_file(root / "creative" / "removed-assets.json")
        if not isinstance(value, dict) or not isinstance(value.get("items"), list):
            return []
        return [item for item in value["items"] if isinstance(item, dict)]

    def remove_project_character_asset(self, project_id, relative, confirmation_name):
        """Move a character source into the project-local trash and invalidate creative work."""
        self._require_initialized()
        project, root = self._project_directory(project_id)
        if not isinstance(relative, str) or not relative.startswith("inputs/characters/"):
            raise ApplicationConflict("character asset path is invalid")
        path = Path(relative)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ApplicationConflict("character asset path is invalid")
        if confirmation_name != path.name:
            raise ApplicationConflict("character asset deletion confirmation does not match")
        source = root / path
        if source.is_symlink() or not source.is_file():
            raise ApplicationNotFound(relative)
        try:
            source.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise ApplicationBlocked("character asset escapes project") from exc
        removed_at = datetime.now(timezone.utc).isoformat()
        trash_name = hashlib.sha256(
            (project.project_id + relative + removed_at).encode("utf-8")
        ).hexdigest()[:12] + "-" + path.name
        trash_relative = Path(".mvstudio/trash/assets") / trash_name
        destination = root / trash_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise ApplicationConflict("character asset trash destination exists")
        try:
            os.replace(source, destination)
        except OSError as exc:
            raise ApplicationError("character asset removal failed") from exc
        items = self._removed_project_assets(root)
        items.append({
            "original_path": relative,
            "trash_path": trash_relative.as_posix(),
            "removed_at": removed_at,
            "name": path.name,
        })
        try:
            self._write_atomic_file(
                root / "creative" / "removed-assets.json",
                canonical_json({"version": 1, "items": items}), ".removed-assets-",
            )
        except Exception:
            try:
                os.replace(destination, source)
            except OSError:
                pass
            raise
        return self.get_project_workflow(project_id)

    def restore_project_character_asset(self, project_id, relative):
        self._require_initialized()
        _project, root = self._project_directory(project_id)
        items = self._removed_project_assets(root)
        match = next((item for item in items if item.get("original_path") == relative), None)
        if match is None:
            raise ApplicationNotFound(relative)
        original = Path(relative)
        trash = Path(str(match.get("trash_path", "")))
        if (original.is_absolute() or trash.is_absolute()
                or any(part in {"", ".", ".."} for part in original.parts + trash.parts)):
            raise ApplicationBlocked("removed asset record is invalid")
        source = root / trash
        destination = root / original
        if source.is_symlink() or not source.is_file() or destination.exists():
            raise ApplicationBlocked("removed asset cannot be restored")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(source, destination)
        except OSError as exc:
            raise ApplicationError("character asset restore failed") from exc
        items.remove(match)
        try:
            self._write_atomic_file(
                root / "creative" / "removed-assets.json",
                canonical_json({"version": 1, "items": items}), ".removed-assets-",
            )
        except Exception:
            try:
                os.replace(destination, source)
            except OSError:
                pass
            raise
        return self.get_project_workflow(project_id)

    def get_project_prompts(self, project_id):
        self._require_initialized()
        from mv_platform.application.prompt_catalog import all_prompt_defaults
        _project, root = self._project_directory(project_id)
        overrides = {}
        target = root / "creative" / "prompt-overrides.json"
        if target.is_symlink():
            raise ApplicationBlocked("prompt configuration path is unsafe")
        if target.is_file():
            try:
                overrides = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApplicationBlocked("project prompt configuration is invalid") from exc
        defaults = all_prompt_defaults()
        return {key: overrides.get(key, value) for key, value in defaults.items()}

    def update_project_prompts(self, project_id, prompts):
        self._require_initialized()
        from mv_platform.application.prompt_catalog import all_prompt_defaults
        defaults = all_prompt_defaults()
        if not isinstance(prompts, dict) or set(prompts) != set(defaults):
            raise ApplicationConflict("all known workflow prompts are required")
        cleaned = {}
        for key, value in prompts.items():
            if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > 16000:
                raise ApplicationConflict("workflow prompt is empty or too large")
            cleaned[key] = value.strip()
        _project, root = self._project_directory(project_id)
        self._write_atomic_file(
            root / "creative" / "prompt-overrides.json",
            canonical_json(cleaned), ".prompts-",
        )
        return cleaned

    @staticmethod
    def _money(value):
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

    def _record_cost(self, project_id, job_id, step_id, resource_type, quantity,
                     unit_price, amount, input_tokens=0, cache_read_tokens=0,
                     output_tokens=0, multiplier=1, metadata=None):
        entry_id = "cost-" + canonical_hash({"project_id": project_id, "job_id": job_id,
            "step_id": step_id, "resource_type": resource_type,
            "metadata": metadata or {}}).split(":", 1)[-1]
        with self.database.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO cost_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (entry_id, project_id, job_id, step_id, resource_type, float(quantity),
                 float(unit_price), input_tokens, cache_read_tokens, output_tokens,
                 float(multiplier), float(self._money(Decimal(amount))),
                 datetime.now(timezone.utc).isoformat(),
                 canonical_json(metadata or {}).decode("utf-8")),
            )
        return entry_id

    def record_llm_cost(self, project_id, job_id, step_id, input_tokens,
                        cache_read_tokens, output_tokens, metadata=None):
        amount = ((Decimal(input_tokens) * Decimal("5") +
                   Decimal(cache_read_tokens) * Decimal("0.5") +
                   Decimal(output_tokens) * Decimal("30")) / Decimal("1000000")) * Decimal("0.04")
        return self._record_cost(project_id, job_id, step_id, "llm", 1, 0, amount,
            input_tokens, cache_read_tokens, output_tokens, Decimal("0.04"), metadata)

    def record_image_cost(self, project_id, job_id, step_id, quantity=1, metadata=None):
        amount = Decimal(str(quantity)) * Decimal("0.5")
        return self._record_cost(project_id, job_id, step_id, "image", quantity,
                                 Decimal("0.5"), amount, metadata=metadata)

    def record_video_cost(self, project_id, job_id, step_id, seconds, metadata=None):
        amount = Decimal(str(seconds)) * Decimal("0.6")
        return self._record_cost(project_id, job_id, step_id, "video", seconds,
                                 Decimal("0.6"), amount, metadata=metadata)

    def get_project_costs(self, project_id):
        self._require_initialized()
        self._project_directory(project_id)
        with self.database.connect() as db:
            rows = db.execute("SELECT entry_id,job_id,step_id,resource_type,quantity,unit_price,input_tokens,cache_read_tokens,output_tokens,multiplier,amount_yuan,occurred_at,metadata FROM cost_entries WHERE project_id=? ORDER BY occurred_at,entry_id", (project_id,)).fetchall()
        entries = [{"entry_id": r[0], "job_id": r[1], "step_id": r[2],
            "resource_type": r[3], "quantity": r[4], "unit_price": r[5],
            "input_tokens": r[6], "cache_read_tokens": r[7], "output_tokens": r[8],
            "multiplier": r[9], "amount_yuan": r[10], "occurred_at": r[11],
            "metadata": json.loads(r[12])} for r in rows]
        by_type = {kind: round(sum(e["amount_yuan"] for e in entries if e["resource_type"] == kind), 8)
                   for kind in ("llm", "image", "video")}
        return {"currency": "CNY", "total_yuan": round(sum(by_type.values()), 8),
                "by_type": by_type, "entries": entries}

    def _require_initialized(self):
        if not self._initialized:
            raise ApplicationBlocked("service is not initialized")

    def list_projects(self):
        self._require_initialized()
        return tuple(self.repository.list_projects())

    def list_project_jobs(self, project_id):
        self._require_initialized()
        try:
            return tuple(JobResult(job, status) for job, status in self.repository.list_jobs(project_id))
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(project_id) from exc

    def delete_project(self, project_id, confirmation_slug):
        self._require_initialized()
        try:
            project = self.repository.get_project(project_id)
            jobs = self.repository.list_jobs(project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(project_id) from exc
        if confirmation_slug != project.slug:
            raise ApplicationConflict("project deletion confirmation does not match")
        if any(status.runtime_state is RuntimeState.RUNNING for _job, status in jobs):
            raise ApplicationBlocked("running projects cannot be deleted")

        project_directory = self._project_root() / project.slug
        job_directories = [self._job_root() / job.job_id for job, _status in jobs]
        targets = ((project_directory, self._project_root()),) + tuple(
            (directory, self._job_root()) for directory in job_directories
        )
        for path, root in targets:
            if path.is_symlink():
                raise ApplicationBlocked("project deletion target is a symlink")
            try:
                path.resolve().relative_to(root.resolve())
            except ValueError as exc:
                raise ApplicationBlocked("project deletion target escapes workspace") from exc

        try:
            with self.database.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                selector = "(SELECT job_id FROM jobs WHERE project_id=?)"
                db.execute("DELETE FROM cost_entries WHERE project_id=?", (project_id,))
                db.execute("DELETE FROM artifacts WHERE job_id IN " + selector, (project_id,))
                db.execute("DELETE FROM events WHERE job_id IN " + selector, (project_id,))
                db.execute("DELETE FROM job_status WHERE job_id IN " + selector, (project_id,))
                db.execute("DELETE FROM jobs WHERE project_id=?", (project_id,))
                deleted = db.execute("DELETE FROM projects WHERE project_id=?", (project_id,))
                if deleted.rowcount != 1:
                    raise ApplicationNotFound(project_id)
                db.commit()
        except ApplicationError:
            raise
        except sqlite3.Error as exc:
            raise ApplicationError("project deletion failed") from exc

        try:
            if project_directory.exists():
                shutil.rmtree(project_directory)
            for directory in job_directories:
                if directory.exists():
                    shutil.rmtree(directory)
        except OSError as exc:
            raise ApplicationError("project records were deleted but file cleanup failed") from exc
        return {"project_id": project_id, "slug": project.slug, "deleted": True}

    def _write_brief(self, directory, brief_bytes):
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "brief.json"
        if target.exists() or target.is_symlink():
            if target.is_symlink(): raise ApplicationBlocked("brief path is a symlink")
            if target.read_bytes() != brief_bytes:
                raise ApplicationConflict("project brief differs")
            return
        fd, temporary = tempfile.mkstemp(prefix=".brief-", dir=str(directory))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(brief_bytes)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def _initialize_project_directory(self, directory, brief_bytes):
        for relative in self._PROJECT_DIRECTORIES:
            (directory / relative).mkdir(parents=True, exist_ok=True)
        self._write_brief(directory, brief_bytes)

    def _atomic_copy(self, source, destination):
        if destination.is_symlink():
            raise ApplicationBlocked("staged input path is a symlink")
        source_digest = self._file_digest(source)
        if destination.exists():
            if not destination.is_file() or self._file_digest(destination) != source_digest:
                raise ApplicationConflict("staged input differs")
            return
        fd, temporary = tempfile.mkstemp(prefix=".input-", dir=str(destination.parent))
        try:
            with source.open("rb") as reader, os.fdopen(fd, "wb") as writer:
                shutil.copyfileobj(reader, writer, 1024 * 1024)
                writer.flush()
                os.fsync(writer.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _file_digest(self, path):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.digest()

    def _safe_project_input(self, project, relative):
        prefixes = ("inputs/audio/", "inputs/lyrics/", "inputs/characters/")
        if not isinstance(relative, str) or not relative.startswith(prefixes):
            raise ApplicationConflict("director intake refs must be project input paths")
        path = Path(relative)
        if path.is_absolute() or "\\" in relative or any(part in {"", ".", ".."} for part in path.parts):
            raise ApplicationConflict("invalid director intake path")
        root = self._project_root() / project.slug
        candidate = root / path
        current = root
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise ApplicationBlocked("director input path contains a symlink")
        try:
            candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise ApplicationBlocked("director input is missing or escapes project") from exc
        if not candidate.is_file():
            raise ApplicationBlocked("director input must be a regular file")
        return candidate

    def _safe_seedance_input(self, project, relative):
        prefixes = ("creative/approved_shots/", "assets/source/keyframes/")
        if not isinstance(relative, str) or not relative.startswith(prefixes):
            raise ApplicationConflict("Seedance refs must be approved-shot or keyframe paths")
        path = Path(relative)
        if path.is_absolute() or "\\" in relative or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ApplicationConflict("invalid Seedance input path")
        root = self._project_root() / project.slug
        candidate = root / path
        current = root
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise ApplicationBlocked("Seedance input path contains a symlink")
        try:
            candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise ApplicationBlocked("Seedance input is missing or escapes project") from exc
        if not candidate.is_file():
            raise ApplicationBlocked("Seedance input must be a regular file")
        return candidate

    def _claim_seedance_request(self, staging, contract_hash):
        claim = staging / ".seedance-request-claimed"
        try:
            descriptor = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ApplicationBlocked(
                "Seedance request was already attempted; automatic paid retry is disabled"
            ) from exc
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write((contract_hash + "\n").encode("ascii"))
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                claim.unlink()
            except OSError:
                pass
            raise

    def start_seedance_shot(self, job_id):
        self._require_initialized()
        if self.supervisor is None:
            raise ApplicationBlocked("job supervisor is not configured")
        try:
            job = self.repository.get_job(job_id)
            status = self.repository.get_status(job_id)
            project = self.repository.get_project(job.project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(job_id) from exc
        if job.operation != "generate" or status.runtime_state is not RuntimeState.QUEUED:
            raise ApplicationConflict("Seedance shot requires a queued generate job")
        contracts = [
            item for item in job.input_refs
            if item.startswith("creative/approved_shots/") and item.endswith(".json")
        ]
        frames = [
            item for item in job.input_refs
            if item.startswith("assets/source/keyframes/")
        ]
        if len(contracts) != 1 or len(frames) != 1 or len(job.input_refs) != 2:
            raise ApplicationConflict(
                "Seedance shot requires one approved-shot contract and one keyframe"
            )
        contract_source = self._safe_seedance_input(project, contracts[0])
        frame_source = self._safe_seedance_input(project, frames[0])
        if contract_source.stat().st_size > 256 * 1024:
            raise ApplicationBlocked("approved-shot contract exceeds byte budget")
        if frame_source.stat().st_size > 20 * 1024 * 1024:
            raise ApplicationBlocked("approved keyframe exceeds byte budget")
        try:
            contract_value = json.loads(contract_source.read_bytes())
            from mvstudio.generation.shot_contract import parse_approved_shot

            approved = parse_approved_shot(contract_value, project.project_id)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ApplicationBlocked("approved-shot contract is invalid") from exc
        if Path(contracts[0]).stem != approved.shot_id:
            raise ApplicationConflict("approved-shot filename must match shot_id")
        if frames[0] != approved.first_frame_path:
            raise ApplicationConflict("Job keyframe differs from approved-shot contract")
        if job.input_digest != approved.contract_sha256:
            raise ApplicationConflict("Job input digest differs from approved-shot contract")
        frame_bytes = frame_source.read_bytes()
        frame_hash = "sha256:" + hashlib.sha256(frame_bytes).hexdigest()
        if frame_hash != approved.first_frame_sha256:
            raise ApplicationBlocked("approved keyframe hash changed")
        staging = self._job_root() / job_id
        if staging.is_symlink():
            raise ApplicationBlocked("job staging path is a symlink")
        staging.mkdir(parents=True, exist_ok=True)
        for relative, source in ((contracts[0], contract_source), (frames[0], frame_source)):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_copy(source, destination)
        from mvstudio.providers.seedance import (
            SeedanceFrame, SeedancePort, SeedanceProviderError, SeedanceTask,
        )

        try:
            port = self.seedance_port or SeedancePort.from_env()
        except SeedanceProviderError as exc:
            raise ApplicationBlocked("Seedance provider configuration is invalid") from exc
        self._claim_seedance_request(staging, approved.contract_sha256)
        try:
            result = port.generate(
                SeedanceTask(
                    shot_id=approved.shot_id,
                    model=approved.model,
                    prompt=approved.prompt,
                    duration_seconds=approved.duration_seconds,
                    first_frame=SeedanceFrame(frame_bytes, frame_hash),
                    aspect_ratio=approved.aspect_ratio,
                    resolution=approved.resolution,
                )
            )
        except SeedanceProviderError as exc:
            raise ApplicationBlocked(
                "Seedance request failed; automatic paid retry is disabled"
            ) from exc
        if (
            not isinstance(result.video_bytes, bytes)
            or not result.video_bytes
            or result.video_sha256
            != "sha256:" + hashlib.sha256(result.video_bytes).hexdigest()
            or result.first_frame_sha256 != frame_hash
            or result.model != approved.model
        ):
            raise ApplicationBlocked("Seedance result identity or hash is invalid")
        self.record_video_cost(
            project.project_id, job_id, "video.shot.generate_requested",
            approved.duration_seconds,
            {"shot_id": approved.shot_id, "model": result.model, "task_id": result.task_id},
        )
        generated_relative = "generated/" + approved.shot_id + ".mp4"
        generated = staging / generated_relative
        self._write_atomic_file(generated, result.video_bytes, ".seedance-video-")
        audit = {
            "version": 1,
            "project_id": project.project_id,
            "job_id": job_id,
            "shot_id": approved.shot_id,
            "provider": result.provider,
            "model": result.model,
            "task_id": result.task_id,
            "approved_contract_sha256": approved.contract_sha256,
            "request_contract_sha256": result.request_contract_sha256,
            "first_frame_sha256": result.first_frame_sha256,
            "video_sha256": result.video_sha256,
            "status": "generated_pending_qc",
        }
        self._write_atomic_file(
            staging / "generated" / "provider_audit.json",
            canonical_json(audit),
            ".seedance-audit-",
        )
        self.supervisor.submit(
            job_id,
            "seedance_shot_qc",
            {
                "project_id": project.project_id,
                "shot_id": approved.shot_id,
                "video_path": generated_relative,
                "video_sha256": result.video_sha256,
                "duration_seconds": approved.duration_seconds,
                "width": 720,
                "height": 1280,
            },
        )
        try:
            completed = self.supervisor.wait(job_id, 60)
        except TimeoutError as exc:
            raise ApplicationBlocked("Seedance shot QC timed out") from exc
        if completed.runtime_state is not RuntimeState.SUCCEEDED:
            raise ApplicationBlocked("Seedance shot failed technical QC")
        preview_relative = (
            "assets/generated/shot-previews/" + approved.shot_id + "_"
            + job_id + "_pending-diagnosis.mp4"
        )
        store = ArtifactStore(self._project_root(), self._job_root())
        try:
            digest, _size = store.publish(
                generated, project.slug, preview_relative, overwrite=False
            )
        except (UnsafePathError, OSError) as exc:
            raise ApplicationBlocked("Seedance preview publication failed") from exc
        payload = {
            "version": 1,
            "project_id": project.project_id,
            "job_id": job_id,
            "shot_id": approved.shot_id,
            "status": "pending_diagnosis",
            "diagnosis_required": True,
            "user_approval_required": True,
            "preview": preview_relative,
            "content_hash": digest,
        }
        completed_status = self.repository.get_status(job_id)
        self._set_business_stage(
            completed_status,
            BusinessStage.GENERATION_PARTIAL,
            "seedance.shot_pending_diagnosis",
            payload,
        )
        return _immutable(payload)

    # ------------------------------------------------------------------
    # Audio-first auto-materialization (PRD-009 §4.4)
    # ------------------------------------------------------------------

    async def _run_lyrics_transcribe(self, project_id, job_id):
        """Transcribe audio to LRC using the configured transcription provider.

        Delegates to transcribe_audio_for_project which resolves provider
        priority: LLM_* gateway first, WHISPER_* fallback, local Whisper last.
        """
        self.transcribe_audio_for_project(project_id)

    async def _run_character_design(self, project_id, job_id, char_name):
        """Generate one character portrait via the configured image provider.

        char_name is the binding name (XLSX) or None (LRC/TXT auto-mode).
        Delegates to generate_characters_for_project which resolves GPT_IMAGE_*.
        The portrait is written to inputs/characters/<safe_name>.png.
        """
        import os as _os
        _project, root = self._project_directory(project_id)
        from mvstudio.providers.image_openai import OpenAICompatibleImageProvider, ImageProviderError
        try:
            provider = self.image_provider or OpenAICompatibleImageProvider.from_env(_os.environ)
        except ImageProviderError as exc:
            raise ApplicationBlocked(
                "image provider not configured: set GPT_IMAGE_API_KEY and GPT_IMAGE_BASE_URL"
            ) from exc
        display = char_name if char_name else "角色"
        prompt = (
            f"简洁人物肖像，{display}，中国风写实风格，"
            "干净白色背景，正面半身像，高质量插画，适合MV故事板"
        )
        try:
            image_bytes = provider.generate(prompt, size="1024x1024")
        except ImageProviderError as exc:
            raise ApplicationConflict(f"portrait generation failed for {display}: {exc}") from exc
        chars_dir = root / "inputs" / "characters"
        chars_dir.mkdir(exist_ok=True)
        safe_name = (char_name or "character").replace(" ", "_").replace("/", "_")
        (chars_dir / f"{safe_name}.png").write_bytes(image_bytes)

    def _extract_character_names_from_lyrics(self, project_root):
        """Derive the set of character names to generate portraits for.

        For XLSX director contracts, returns the binding name list with chorus
        markers (``_CHORUS_MARKERS``) excluded, sorted for determinism.
        For LRC / TXT lyrics, returns ``[None]`` so the executor auto-selects
        1-3 names (PRD-009 §4.3.1 LRC path).
        """
        from mvstudio.director.intake import _CHORUS_MARKERS, parse_xlsx_director_sheet
        lyrics_dir = project_root / "inputs" / "lyrics"
        lyrics_files = [f for f in lyrics_dir.iterdir() if f.is_file()]
        if not lyrics_files:
            return [None]
        lyrics_path = lyrics_files[0]
        if lyrics_path.suffix.lower() != ".xlsx":
            # LRC / TXT — no binding character names; executor decides.
            return [None]
        sheet = parse_xlsx_director_sheet(lyrics_path)
        all_names: set = set()
        for entry in sheet.get("timed_entries", []):
            for name in entry.get("character_names", []):
                all_names.add(name)
        char_names = sorted(all_names - _CHORUS_MARKERS)
        return char_names if char_names else [None]

    def transcribe_audio_for_project(self, project_id):
        """Transcribe the project audio to LRC using local Whisper (Faster Whisper).

        Reads inputs/audio/<file>, transcribes with word timestamps, groups word
        segments into LRC lines at natural pauses (>0.5 s silence) or every 12 words,
        and writes the result to inputs/lyrics/transcript.lrc.

        Provider resolution honours user configuration first: an injected
        alignment_port wins, otherwise the already-configured OpenAI-compatible
        gateway (WHISPER_* or shared LLM_*) is used for remote transcription, and
        a local Whisper model (MVSTUDIO_WHISPER_MODEL) is only the last-resort
        fallback when no gateway is configured.

        Returns {"lrc_file": "inputs/lyrics/transcript.lrc", "line_count": int}.
        Raises ApplicationConflict if != 1 audio file or hallucination risk detected.
        Raises ApplicationBlocked if no transcription provider is configured.
        """
        self._require_initialized()
        import os as _os
        _project, root = self._project_directory(project_id)
        audio_files = [f for f in (root / "inputs" / "audio").iterdir() if f.is_file()]
        if len(audio_files) != 1:
            raise ApplicationConflict(
                "transcription requires exactly one audio file in inputs/audio/"
            )
        audio_path = audio_files[0]
        from mvstudio.providers.alignment_faster_whisper import FasterWhisperAlignmentPort
        from mvstudio.providers.transcription_openai import (
            OpenAICompatibleTranscriptionPort,
            TranscriptionProviderError,
        )
        from mvstudio.director.alignment import LyricAlignmentError
        # Provider chain: injected port (test/override) wins outright.  Otherwise
        # a locally-configured FasterWhisper model takes priority — it is offline,
        # free, and not subject to remote outages — and the remote gateway is only
        # a fallback for when no local model is installed (or the local model
        # itself fails to load).  Transient failures (network 5xx, model load
        # errors) are caught per-provider and fall through to the next candidate;
        # ApplicationBlocked is raised only when every provider is exhausted.
        # LyricAlignmentError from a successful provider's transcribe() (data
        # problem) aborts immediately — a different provider will not fix it.
        providers = []
        if self.alignment_port is not None:
            providers.append(self.alignment_port)
        else:
            # 1. Local model first, when configured (MVSTUDIO_WHISPER_MODEL).
            try:
                providers.append(FasterWhisperAlignmentPort.from_env())
            except LyricAlignmentError:
                pass  # local model not configured — fall back to remote gateway
            # 2. Remote gateway as fallback.
            gateway = _os.environ.get("LLM_BASE_URL") or _os.environ.get("WHISPER_BASE_URL", "")
            if gateway:
                try:
                    providers.append(OpenAICompatibleTranscriptionPort.from_env(_os.environ))
                except TranscriptionProviderError:
                    pass  # gateway URL/key invalid — skip
        if not providers:
            raise ApplicationBlocked(
                "transcription not configured: configure the LLM gateway "
                "(LLM_BASE_URL/LLM_API_KEY) or a dedicated WHISPER_* gateway, "
                "or set MVSTUDIO_WHISPER_MODEL to a local model path"
            )
        result = None
        last_exc: Exception | None = None
        for port in providers:
            try:
                result = port.transcribe(audio_path)
                last_exc = None
                break
            except (TranscriptionProviderError, LyricAlignmentError) as exc:
                # Provider failed to produce a transcript: remote transport error
                # (5xx, network timeout) or a local model-load/inference failure.
                # Neither is a data problem the next provider would share, so fall
                # through and try the next candidate in the chain.
                last_exc = exc
        if last_exc is not None:
            raise ApplicationBlocked(
                "转录服务暂时不可用：" + str(last_exc)
                + "。请稍后重试；若持续失败，请在系统设置中检查转录网关"
                "（LLM_ 或 WHISPER_）的地址与密钥。"
            ) from last_exc
        if result.hallucination_risk:
            raise ApplicationConflict(
                "transcription quality gate failed: word density too high — "
                "check that MVSTUDIO_WHISPER_LANGUAGE matches the audio language"
            )
        # Group word-level segments into LRC lines at pauses (>0.5 s) or 12-word cap.
        lrc_lines, current_words, current_start = [], [], None
        segs = result.segments
        for i, word in enumerate(segs):
            if current_start is None:
                current_start = word["start"]
            current_words.append(word["text"])
            is_last = i == len(segs) - 1
            next_pause = ((segs[i + 1]["start"] - word["end"]) > 0.5) if not is_last else True
            if next_pause or len(current_words) >= 12 or is_last:
                text = "".join(current_words).strip()
                if text:
                    mm, ss = int(current_start // 60), current_start % 60
                    lrc_lines.append(f"[{mm:02d}:{ss:05.2f}]{text}")
                current_words, current_start = [], None
        if not lrc_lines:
            raise ApplicationConflict("transcription returned no speech segments")
        lyrics_dir = root / "inputs" / "lyrics"
        lyrics_dir.mkdir(exist_ok=True)
        (lyrics_dir / "transcript.lrc").write_text("\n".join(lrc_lines), encoding="utf-8")
        return {"lrc_file": "inputs/lyrics/transcript.lrc", "line_count": len(lrc_lines)}

    def generate_characters_for_project(self, project_id):
        """Generate character portraits via GPT-image-2, writing PNGs to inputs/characters/.

        Derives character names from an XLSX director sheet in inputs/lyrics/ (if present);
        falls back to a single generic portrait for LRC/TXT lyrics or when no lyrics exist.

        Returns {"generated": [display_name, ...], "portrait_count": int}.
        Raises ApplicationBlocked if the image provider is not configured.
        Raises ApplicationConflict if a generation call fails.
        """
        self._require_initialized()
        import os as _os
        _project, root = self._project_directory(project_id)
        from mvstudio.providers.image_openai import OpenAICompatibleImageProvider, ImageProviderError
        try:
            provider = self.image_provider or OpenAICompatibleImageProvider.from_env(_os.environ)
        except ImageProviderError as exc:
            raise ApplicationBlocked(
                "image provider not configured: set GPT_IMAGE_API_KEY and GPT_IMAGE_BASE_URL"
            ) from exc
        char_names = self._extract_character_names_from_lyrics(root)
        chars_dir = root / "inputs" / "characters"
        chars_dir.mkdir(exist_ok=True)
        generated = []
        for name in char_names:
            display = name if name else "角色"
            prompt = (
                f"简洁人物肖像，{display}，中国风写实风格，"
                "干净白色背景，正面半身像，高质量插画，适合MV故事板"
            )
            try:
                image_bytes = provider.generate(prompt, size="1024x1024")
            except ImageProviderError as exc:
                raise ApplicationConflict(
                    f"portrait generation failed for {display}: {exc}"
                ) from exc
            safe_name = (name or "character").replace(" ", "_").replace("/", "_")
            (chars_dir / f"{safe_name}.png").write_bytes(image_bytes)
            generated.append(display)
        return {"generated": generated, "portrait_count": len(generated)}

    def get_material_status(self, project_id):
        """Return per-bucket status for the intake material inspector.

        Returns a dict with keys audio, lyrics, characters, ready_for_intake.
        No side effects; purely reads disk state.
        """
        self._require_initialized()
        _project, root = self._project_directory(project_id)

        def _files(kind):
            bucket = root / "inputs" / kind
            return [f for f in bucket.iterdir() if f.is_file()] if bucket.is_dir() else []

        audio = _files("audio")
        lyrics = _files("lyrics")
        chars = _files("characters")
        has_audio = len(audio) == 1
        return {
            "audio": {
                "status": "ok" if has_audio else "missing",
                "file": audio[0].name if has_audio else None,
            },
            "lyrics": {
                "status": "ok" if lyrics else "missing",
                "can_fill": has_audio,
                "files": [f.name for f in lyrics],
            },
            "characters": {
                "status": "ok" if chars else "missing",
                "can_fill": bool(lyrics) or has_audio,
                "count": len(chars),
            },
            "ready_for_intake": has_audio,
        }

    def analyze_characters_from_lyrics(self, project_id, messages):
        """Multi-turn LLM character analysis from lyrics.

        ``messages`` is a list of {"role": "user"|"assistant", "content": "..."}
        representing the conversation so far (NOT including the system message).

        Returns {"reply": str, "characters": [{"name": str, "description": str}, ...]}.
        Raises ApplicationBlocked if the LLM gateway is not configured.
        """
        import json as _json
        import os as _os
        import urllib.request as _req

        self._require_initialized()
        _project, root = self._project_directory(project_id)

        # Read lyrics content for the system prompt
        lyrics_text = ""
        lyrics_dir = root / "inputs" / "lyrics"
        if lyrics_dir.is_dir():
            for lf in sorted(lyrics_dir.iterdir()):
                if lf.is_file():
                    try:
                        lyrics_text = lf.read_text(encoding="utf-8", errors="replace")[:8000]
                    except Exception:
                        pass
                    break

        system_prompt = (
            "你是一位音乐MV导演助手，专门分析歌词中的人物角色。\n"
            "根据歌词内容，识别出需要在MV中出现的人物角色。\n"
            "请在回答末尾输出一个JSON代码块，格式如下：\n"
            "```json\n"
            "{\"characters\": [{\"name\": \"人物名称\", \"description\": \"外貌特征和性格气质描述\"}]}\n"
            "```\n\n"
            "歌词内容如下：\n"
            + (lyrics_text or "（暂无歌词，请根据歌曲标题或用户描述来分析）")
        )

        base_url = _os.environ.get("LLM_BASE_URL", "")
        api_key = _os.environ.get("LLM_API_KEY", "")
        model = _os.environ.get("LLM_MODEL", _os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))

        if not base_url or not api_key:
            raise ApplicationBlocked(
                "LLM gateway not configured: set LLM_BASE_URL and LLM_API_KEY"
            )

        base = base_url.rstrip("/")
        endpoint = base + ("/chat/completions" if base.endswith("/v1") else "/v1/chat/completions")

        all_messages = [{"role": "system", "content": system_prompt}] + (messages or [])

        body = {
            "model": model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        request = _req.Request(
            endpoint,
            data=_json.dumps(body, separators=(",", ":")).encode("utf-8"),
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with _req.urlopen(request, timeout=60) as resp:
                raw = resp.read(500_000)
        except Exception as exc:
            raise ApplicationBlocked(f"LLM character analysis request failed: {exc}") from exc

        data = _json.loads(raw)
        reply_text = data["choices"][0]["message"]["content"]

        # Extract JSON characters block from reply
        characters = []
        try:
            content = reply_text.strip()
            # Find ```json ... ``` block
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                json_str = content[start:end].strip()
            else:
                # Try to find raw JSON object
                start = content.rfind("{")
                end = content.rfind("}") + 1
                json_str = content[start:end] if start >= 0 else ""
            if json_str:
                parsed = _json.loads(json_str)
                characters = parsed.get("characters", [])
        except Exception:
            pass  # characters stays empty; reply_text still returned

        return {"reply": reply_text, "characters": characters}

    def generate_character_portraits_from_list(self, project_id, characters):
        """Generate portraits for an explicit character list.

        ``characters`` is a list of {"name": str, "description": str}.
        Generates one portrait PNG per character via the configured image provider.

        Returns {"portrait_count": int, "portraits": [{"name": str, "path": str}]}.
        Raises ApplicationBlocked if the image provider is not configured.
        Raises ApplicationConflict if a generation call fails.
        """
        import os as _os

        self._require_initialized()
        _project, root = self._project_directory(project_id)
        from mvstudio.providers.image_openai import OpenAICompatibleImageProvider, ImageProviderError

        try:
            provider = self.image_provider or OpenAICompatibleImageProvider.from_env(_os.environ)
        except ImageProviderError as exc:
            raise ApplicationBlocked(
                "image provider not configured: set GPT_IMAGE_API_KEY and GPT_IMAGE_BASE_URL"
            ) from exc

        chars_dir = root / "inputs" / "characters"
        chars_dir.mkdir(exist_ok=True)

        portraits = []
        for char in characters:
            name = (char.get("name") or "角色").strip()
            description = (char.get("description") or "").strip()
            prompt = (
                f"简洁人物肖像，{name}，"
                + (f"{description}，" if description else "")
                + "中国风写实风格，干净白色背景，正面半身像，高质量插画，适合MV故事板"
            )
            try:
                image_bytes = provider.generate(prompt, size="1024x1024")
            except ImageProviderError as exc:
                raise ApplicationConflict(
                    f"portrait generation failed for {name}: {exc}"
                ) from exc
            safe_name = name.replace(" ", "_").replace("/", "_")
            dest = chars_dir / f"{safe_name}.png"
            dest.write_bytes(image_bytes)
            portraits.append({"name": name, "path": f"inputs/characters/{safe_name}.png"})

        return {"portrait_count": len(portraits), "portraits": portraits}

    async def _materialize_job(self, project_id, job_id, confirm_billing):
        """Orchestrate the four-step auto-materialization (PRD-009 §4.4).

        Steps (strict order):
            a. Assert inputs/audio/ contains exactly one file; raise
               MaterializeError("no_audio") otherwise.
            b. If inputs/lyrics/ is empty, transcribe audio → LRC and record
               cost with a deterministic step_id tied to the audio content hash.
            c. If inputs/characters/ is empty, derive character names from the
               lyrics file and design one portrait per non-chorus character,
               recording cost per character with a deterministic step_id.
            d. Call start_director_intake so the disk buckets (now populated)
               are staged and submitted to the supervisor.

        ``confirm_billing`` must be ``True``; any provider call is gated on this
        flag per §4.5.  The method never calls add_job / update_job.
        """
        self._require_initialized()
        if not confirm_billing:
            raise MaterializeError("billing_confirmation_required")

        _project, root = self._project_directory(project_id)
        audio_dir = root / "inputs" / "audio"
        lyrics_dir = root / "inputs" / "lyrics"
        chars_dir = root / "inputs" / "characters"

        # ---- step a: audio hard gate ----------------------------------------
        audio_files = [f for f in audio_dir.iterdir() if f.is_file()]
        if len(audio_files) != 1:
            raise MaterializeError("no_audio")
        audio_file = audio_files[0]
        # Deterministic 10-char hex tied to audio content (§4.4.4 幂等键)
        audio_hash10 = hashlib.sha256(audio_file.read_bytes()).hexdigest()[:10]

        # ---- step b: transcribe lyrics if bucket is empty -------------------
        lyrics_files = [f for f in lyrics_dir.iterdir() if f.is_file()]
        if not lyrics_files:
            step_id = "materialize:lyrics:" + audio_hash10
            await self._run_lyrics_transcribe(project_id, job_id)
            # Record after product is written; metadata must be deterministic.
            self._record_cost(
                project_id, job_id, step_id, "asr",
                1, Decimal("0"), Decimal("0"),
                metadata={},
            )

        # ---- step c: design characters if bucket is empty -------------------
        char_files = [f for f in chars_dir.iterdir() if f.is_file()]
        if not char_files:
            char_names = self._extract_character_names_from_lyrics(root)
            for char_name in char_names:
                step_id = "materialize:character:" + (char_name if char_name else "auto")
                await self._run_character_design(project_id, job_id, char_name)
                # Record after product is written; metadata must be deterministic.
                self._record_cost(
                    project_id, job_id, step_id, "image",
                    1, Decimal("0.5"), Decimal("0.5"),
                    metadata={},
                )

        # ---- step d: intake (disk buckets are now complete) -----------------
        self.start_director_intake(job_id)

    def pending_materialization(self, project_id):
        """Return the list of input kinds that are still absent from disk buckets.

        Reads inputs/audio/, inputs/lyrics/, and inputs/characters/ and
        returns each kind whose bucket does not yet satisfy the §2.1.1 gate:
        - "audio"      — bucket does not contain exactly one file
        - "lyrics"     — bucket is empty (zero files)
        - "characters" — bucket is empty (zero files)

        The frontend reads this field (§5.3) to render the soft-gate prompt and
        the "Confirm billing and auto-complete" button.  The result is derived
        purely from disk state; input_refs is never consulted.
        """
        self._require_initialized()
        _project, root = self._project_directory(project_id)

        def _bucket_files(name):
            bucket = root / "inputs" / name
            if not bucket.is_dir():
                return []
            return [f for f in bucket.iterdir() if f.is_file()]

        audio_files = _bucket_files("audio")
        lyrics_files = _bucket_files("lyrics")
        char_files = _bucket_files("characters")
        missing = []
        if len(audio_files) != 1:
            missing.append("audio")
        if not lyrics_files:
            missing.append("lyrics")
        if not char_files:
            missing.append("characters")
        return missing

    def start_director_intake(self, job_id):
        self._require_initialized()
        if self.supervisor is None:
            raise ApplicationBlocked("job supervisor is not configured")
        try:
            job = self.repository.get_job(job_id)
            status = self.repository.get_status(job_id)
            project = self.repository.get_project(job.project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(job_id) from exc
        if job.operation != "analyze" or status.runtime_state is not RuntimeState.QUEUED:
            raise ApplicationConflict("director intake requires a queued analyze job")
        project_dir = self._project_root() / project.slug
        audio_files = list((project_dir / "inputs" / "audio").glob("*"))
        lyrics_files = list((project_dir / "inputs" / "lyrics").glob("*"))
        char_files = list((project_dir / "inputs" / "characters").glob("*"))
        if len(audio_files) != 1:
            raise ApplicationConflict("director intake requires exactly one audio file in inputs/audio/")
        # lyrics and characters are soft gates; orchestration layer handles completion
        staging = self._job_root() / job_id
        if staging.is_symlink():
            raise ApplicationBlocked("job staging path is a symlink")
        staging.mkdir(parents=True, exist_ok=True)
        for disk_file in audio_files + lyrics_files + char_files:
            relative = str(disk_file.relative_to(project_dir))
            source = self._safe_project_input(project, relative)
            current = staging
            for part in Path(relative).parts[:-1]:
                current = current / part
                if current.is_symlink():
                    raise ApplicationBlocked("staged input path contains a symlink")
                current.mkdir(exist_ok=True)
                if current.is_symlink():
                    raise ApplicationBlocked("staged input path contains a symlink")
            self._atomic_copy(source, current / Path(relative).name)
        audio_refs = [str(f.relative_to(project_dir)) for f in audio_files]
        lyrics_refs = [str(f.relative_to(project_dir)) for f in lyrics_files]
        chars_refs = [str(f.relative_to(project_dir)) for f in char_files]
        payload = {
            "project_id": project.project_id,
            "audio": audio_refs[0],
            "lyrics": lyrics_refs[0] if lyrics_refs else None,
            "characters": chars_refs,
        }
        return self.supervisor.submit(job_id, "director_intake", payload)

    def start_director_animatic_test(self, job_id):
        """Use the configured semantic provider for a creative Animatic draft."""
        return self._start_director_animatic_test(job_id, offline=False)

    def start_director_animatic_offline_test(self, job_id):
        """Use explicit non-semantic placeholders for an offline structural test."""
        return self._start_director_animatic_test(job_id, offline=True)

    def _start_director_animatic_test(self, job_id, offline, creative_model=True):
        self._require_initialized()
        if self.supervisor is None:
            raise ApplicationBlocked("job supervisor is not configured")
        try:
            job = self.repository.get_job(job_id)
            status = self.repository.get_status(job_id)
            project = self.repository.get_project(job.project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(job_id) from exc
        if job.operation != "animatic" or status.runtime_state is not RuntimeState.QUEUED:
            raise ApplicationConflict("director animatic test requires a queued animatic job")
        project_dir = self._project_root() / project.slug
        audio_files = list((project_dir / "inputs" / "audio").glob("*"))
        lyrics_files = list((project_dir / "inputs" / "lyrics").glob("*"))
        char_files = list((project_dir / "inputs" / "characters").glob("*"))
        if len(audio_files) != 1:
            raise ApplicationConflict("director animatic test requires exactly one audio file in inputs/audio/")
        # lyrics and characters are soft gates; orchestration layer handles completion
        staging = self._job_root() / job_id
        if staging.is_symlink():
            raise ApplicationBlocked("job staging path is a symlink")
        staging.mkdir(parents=True, exist_ok=True)
        for disk_file in audio_files + lyrics_files + char_files:
            relative = str(disk_file.relative_to(project_dir))
            source = self._safe_project_input(project, relative)
            current = staging
            for part in Path(relative).parts[:-1]:
                current = current / part
                if current.is_symlink():
                    raise ApplicationBlocked("staged input path contains a symlink")
                current.mkdir(exist_ok=True)
                if current.is_symlink():
                    raise ApplicationBlocked("staged input path contains a symlink")
            self._atomic_copy(source, current / Path(relative).name)
        audio_refs = [str(f.relative_to(project_dir)) for f in audio_files]
        lyrics_refs = [str(f.relative_to(project_dir)) for f in lyrics_files]
        chars_refs = [str(f.relative_to(project_dir)) for f in char_files]

        from mvstudio.director.drafting import draft_maps
        from mvstudio.director.intake import inspect_intake
        from mvstudio.director.structural_planner import plan_structural_score
        intake = inspect_intake(
            {
                "project_id": project.project_id,
                "audio": audio_refs[0],
                "lyrics": lyrics_refs[0] if lyrics_refs else None,
                "characters": chars_refs,
            },
            staging,
        )
        timed_path = staging / "intake" / "lyrics_timed.json"
        alignment_mode = "timed_lrc"
        if intake["lyrics"]["alignment_state"] == "alignment_required":
            from mvstudio.director.alignment import LyricAlignmentError, align_plain_lyrics
            from mvstudio.providers.alignment_faster_whisper import FasterWhisperAlignmentPort

            try:
                alignment_port = self.alignment_port or FasterWhisperAlignmentPort.from_env()
                intake, timed = align_plain_lyrics(intake, staging, alignment_port)
            except LyricAlignmentError as exc:
                raise ApplicationBlocked(str(exc)) from exc
            alignment_mode = "provider_word_timestamps"
        elif intake["lyrics"]["alignment_state"] not in {
            "aligned", "aligned_director_contract"
        } or not timed_path.is_file():
            raise ApplicationBlocked("director animatic test lyrics alignment is invalid")
        brief_path = self._project_root() / project.slug / "brief.json"
        try:
            brief = json.loads(brief_path.read_bytes())
            if alignment_mode == "timed_lrc":
                timed = json.loads(timed_path.read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise ApplicationBlocked("director animatic test input contract is invalid") from exc
        if offline:
            from mvstudio.providers.semantic_offline import OfflineStructuralPort

            port = OfflineStructuralPort()
            model = port.model
        else:
            from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort

            port = self.semantic_port or OpenAICompatibleSemanticPort.from_env()
            model = self.semantic_model or os.environ.get("LLM_MODEL", "")
            service = self
            provider = port
            invocation_counts = {}

            class CostRecordingPort:
                translate_chinese_prompts = getattr(
                    provider, "translate_chinese_prompts", False
                )

                def run(self, task):
                    invocation_counts[task.event_type] = invocation_counts.get(task.event_type, 0) + 1
                    source_event = (
                        task.payload.get("source_event", "")
                        if isinstance(task.payload, Mapping) else ""
                    )
                    metadata = {
                        "model": task.model, "event_type": task.event_type,
                        "invocation": invocation_counts[task.event_type],
                    }
                    if source_event:
                        metadata["source_event"] = source_event
                    try:
                        result = provider.run(task)
                    except Exception as exc:
                        usage = (
                            getattr(exc, "input_tokens", 0),
                            getattr(exc, "cache_read_tokens", 0),
                            getattr(exc, "output_tokens", 0),
                        )
                        if any(usage):
                            failure_metadata = dict(metadata)
                            failure_metadata["outcome"] = "invalid_response"
                            finish_reason = getattr(exc, "finish_reason", "")
                            if finish_reason:
                                failure_metadata["finish_reason"] = finish_reason
                            service.record_llm_cost(
                                project.project_id, job_id, task.event_type,
                                usage[0], usage[1], usage[2], failure_metadata,
                            )
                        raise
                    service.record_llm_cost(
                        project.project_id, job_id, task.event_type,
                        result.input_tokens, result.cache_read_tokens, result.output_tokens,
                        metadata,
                    )
                    return result

            port = CostRecordingPort()
        prompt_overrides = self.get_project_prompts(project.project_id)

        def emit_progress(stage, pct, message):
            if offline:
                return
            try:
                self._emit_mini_event(job_id, "progress", {
                    "stage": stage, "pct": pct, "message": message,
                })
            except Exception:
                pass

        drafted = draft_maps(
            intake, timed, brief, port, staging, model,
            prompt_overrides=prompt_overrides,
            progress=emit_progress,
        )
        score = plan_structural_score(
            drafted["music_map"],
            drafted["character_map"],
            drafted["lyrics_semantic"],
            brief,
            staging,
        )
        if offline:
            score["purpose"] = "structural_animatic_test_only"
            self._write_atomic_file(
                staging / "creative" / "visual_score.yaml",
                yaml.safe_dump(score, allow_unicode=True, sort_keys=False).encode("utf-8"),
                ".offline-score-",
            )
        visual_score_mode = "structural_offline"
        if not offline and creative_model:
            from mvstudio.director.creative_planner import draft_creative_score

            creative = draft_creative_score(
                score,
                drafted["music_map"],
                drafted["character_map"],
                drafted["lyrics_semantic"],
                brief,
                port,
                model,
                staging,
                drafted["model_audit"],
                prompt_overrides=prompt_overrides,
                progress=emit_progress,
            )
            score = creative["visual_score"]
            visual_score_mode = "creative_model_draft"
        elif not offline:
            visual_score_mode = "structural_score_from_model_maps"
        package = {
            "project_id": project.project_id,
            "brief": brief,
            "music_map": drafted["music_map"],
            "character_map": drafted["character_map"],
            "visual_score": score,
            "animatic": {"enabled": True, "fps": 6},
        }
        self.supervisor.submit(job_id, "director_structural", package)
        try:
            completed = self.supervisor.wait(job_id, 300)
        except TimeoutError as exc:
            raise ApplicationBlocked("director animatic test timed out") from exc
        if completed.runtime_state is not RuntimeState.SUCCEEDED:
            raise ApplicationBlocked("director animatic test failed")
        _job, completed_status, manifest, _manifest_path, staging = self._director_manifest(
            job_id, "draft_self_generated"
        )
        artifact = next(
            (item for item in manifest["artifacts"] if item["path"] == "outputs/animatic.mp4"),
            None,
        )
        if artifact is None:
            raise ApplicationBlocked("director animatic output is missing")
        destination_relative = (
            "outputs/structural_animatic_" if offline else "outputs/creative_animatic_"
        ) + job_id + ".mp4"
        store = ArtifactStore(self._project_root(), self._job_root())
        destination = store.validate_project_path(project.slug, destination_relative)
        if destination.exists():
            if not destination.is_file():
                raise ApplicationConflict("structural animatic destination is not a file")
            if "sha256:" + self._file_digest(destination).hex() != artifact["content_hash"]:
                raise ApplicationConflict("structural animatic destination differs")
        else:
            try:
                store.publish(
                    staging / artifact["path"],
                    project.slug,
                    destination_relative,
                    overwrite=False,
                )
            except (UnsafePathError, OSError) as exc:
                raise ApplicationBlocked("structural animatic publication failed") from exc
        payload = {
            "project_id": project.project_id,
            "job_id": job_id,
            "status": "draft_self_generated",
            "approval_required": True,
            "semantic_mode": "offline_unclassified" if offline else "configured_model",
            "lyrics_alignment_mode": alignment_mode,
            "visual_score_mode": visual_score_mode,
            "output": destination_relative,
            "content_hash": artifact["content_hash"],
        }
        self._set_business_stage(
            completed_status,
            BusinessStage.VISUAL_SCORE_PENDING_USER,
            "director.structural_animatic_published",
            payload,
        )
        return _immutable(payload)

    def _director_manifest(self, job_id, required_status):
        try:
            job = self.repository.get_job(job_id)
            status = self.repository.get_status(job_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(job_id) from exc
        if job.operation not in {"compile", "animatic"} or status.runtime_state is not RuntimeState.SUCCEEDED:
            raise ApplicationConflict("director artifacts require a successful compile or animatic job")
        staging = self._job_root() / job_id
        manifest_path = staging / "artifact-manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise ApplicationBlocked("director artifact manifest is missing or unsafe")
        try:
            manifest = json.loads(manifest_path.read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise ApplicationBlocked("director artifact manifest is invalid") from exc
        if manifest.get("project_id") != job.project_id or manifest.get("job_id") != job_id:
            raise ApplicationBlocked("director artifact manifest identity mismatch")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ApplicationBlocked("director artifact manifest has no artifacts")
        declared = set()
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise ApplicationBlocked("director artifact entry is invalid")
            relative = artifact.get("path")
            path = Path(relative) if isinstance(relative, str) else Path()
            if (
                not isinstance(relative, str)
                or not relative.startswith(("creative/", "outputs/"))
                or path.is_absolute()
                or "\\" in relative
                or any(part in {"", ".", ".."} for part in path.parts)
                or relative in declared
            ):
                raise ApplicationBlocked("director artifact path is invalid")
            if artifact.get("project_id") != job.project_id or artifact.get("job_id") != job_id:
                raise ApplicationBlocked("director artifact identity mismatch")
            if artifact.get("status") != required_status:
                raise ApplicationBlocked("director artifact is not " + required_status)
            source = staging / path
            if source.is_symlink() or not source.is_file():
                raise ApplicationBlocked("director artifact file is missing or unsafe")
            try:
                source.resolve(strict=True).relative_to(staging.resolve(strict=True))
            except (FileNotFoundError, ValueError) as exc:
                raise ApplicationBlocked("director artifact escapes staging") from exc
            digest = "sha256:" + self._file_digest(source).hex()
            if digest != artifact.get("content_hash"):
                raise ApplicationBlocked("director artifact hash mismatch")
            declared.add(relative)
        all_files = {
            path.relative_to(staging).as_posix()
            for path in staging.rglob("*")
            if path.is_file()
        }
        actual = {
            relative for relative in all_files
            if relative.startswith(("creative/", "outputs/"))
        }
        operational = {
            relative for relative in all_files
            if relative.startswith(("inputs/audio/", "inputs/lyrics/", "inputs/characters/"))
            or relative in {
                "intake/intake_manifest.json",
                "intake/lyrics_plain.json",
                "intake/lyrics_timed.json",
                "intake/lyrics_alignment_audit.json",
                "intake/lyrics_alignment_evidence.json",
            }
        }
        unexpected = all_files - actual - operational - {
            "artifact-manifest.json", "approval-record.json"
        }
        if any(path.is_symlink() for path in staging.rglob("*")):
            raise ApplicationBlocked("director staging contains a symlink")
        if unexpected:
            raise ApplicationBlocked("staging contains unexpected operational files")
        if actual != declared:
            raise ApplicationBlocked("staging contains undeclared director artifacts")
        return job, status, manifest, manifest_path, staging

    def _set_business_stage(self, status, stage, event_type, payload):
        now = datetime.now(timezone.utc)
        with self.database.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT COALESCE(MAX(seq),0) FROM events WHERE job_id=?", (status.job_id,)).fetchone()
            db.execute(
                "UPDATE job_status SET business_stage=?,updated_at=? WHERE job_id=?",
                (stage.value, now.isoformat(), status.job_id),
            )
            db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (status.job_id, row[0] + 1, event_type, now.isoformat(), canonical_json(payload).decode("utf-8")),
            )
            db.commit()

    def approve_director_artifacts(self, job_id):
        self._require_initialized()
        job, status, manifest, manifest_path, _staging = self._director_manifest(
            job_id, "draft_self_generated"
        )
        approved_at = datetime.now(timezone.utc).isoformat()
        for artifact in manifest["artifacts"]:
            artifact["status"] = "approved"
            artifact["approved_at"] = approved_at
        manifest["approval"] = {"status": "approved", "approved_at": approved_at}
        manifest_bytes = canonical_json(manifest)
        self._write_atomic_file(manifest_path, manifest_bytes, ".manifest-")
        approval = {
            "version": 1,
            "project_id": job.project_id,
            "job_id": job_id,
            "manifest_hash": "sha256:" + hashlib.sha256(manifest_bytes).hexdigest(),
            "status": "approved",
            "approved_at": approved_at,
        }
        self._write_atomic_file(
            manifest_path.parent / "approval-record.json", canonical_json(approval), ".approval-"
        )
        self._set_business_stage(status, BusinessStage.QC_PASSED, "director.artifacts_approved", approval)
        return _immutable(approval)

    def _write_atomic_file(self, target, content, prefix):
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise ApplicationBlocked("atomic target is a symlink")
        fd, temporary = tempfile.mkstemp(prefix=prefix, dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _verified_published_artifact(self, project, relative_path, content_hash):
        """Return the immutable source for a canonical artifact we previously published."""
        receipts_root = self._project_root() / project.slug / ".mvstudio" / "jobs"
        if receipts_root.is_symlink() or not receipts_root.is_dir():
            return None
        store = ArtifactStore(self._project_root(), self._job_root())
        for receipt_directory in receipts_root.iterdir():
            if receipt_directory.is_symlink() or not receipt_directory.is_dir():
                continue
            receipt_path = receipt_directory / "publication.json"
            if receipt_path.is_symlink() or not receipt_path.is_file():
                continue
            try:
                receipt = json.loads(receipt_path.read_bytes())
                owner_job_id = receipt["job_id"]
                if (
                    receipt.get("status") != "published"
                    or receipt.get("project_id") != project.project_id
                    or owner_job_id != receipt_directory.name
                    or relative_path not in receipt.get("paths", [])
                ):
                    continue
                manifest_path = store.validate_job_path(owner_job_id, "artifact-manifest.json")
                if manifest_path.is_symlink() or not manifest_path.is_file():
                    continue
                manifest = json.loads(manifest_path.read_bytes())
                manifest_hash = "sha256:" + hashlib.sha256(canonical_json(manifest)).hexdigest()
                if receipt.get("manifest_hash") != manifest_hash:
                    continue
                artifact = next(
                    item for item in manifest.get("artifacts", ())
                    if item.get("path") == relative_path
                    and item.get("content_hash") == content_hash
                )
                source = store.validate_job_path(owner_job_id, artifact["path"])
                if (
                    source.is_symlink()
                    or not source.is_file()
                    or "sha256:" + self._file_digest(source).hex() != content_hash
                ):
                    continue
                return owner_job_id, source
            except (KeyError, StopIteration, TypeError, ValueError, OSError, json.JSONDecodeError,
                    UnsafePathError):
                continue
        return None

    def publish_director_artifacts(self, job_id, supersede=False, preserve_user_edits=False):
        self._require_initialized()
        job, status, manifest, _manifest_path, staging = self._director_manifest(job_id, "approved")
        project = self.repository.get_project(job.project_id)
        approval_path = staging / "approval-record.json"
        if approval_path.is_symlink() or not approval_path.is_file():
            raise ApplicationBlocked("director approval record is missing or unsafe")
        try:
            approval = json.loads(approval_path.read_bytes())
        except (OSError, json.JSONDecodeError) as exc:
            raise ApplicationBlocked("director approval record is invalid") from exc
        manifest_hash = "sha256:" + hashlib.sha256(canonical_json(manifest)).hexdigest()
        if (
            approval.get("status") != "approved"
            or approval.get("project_id") != job.project_id
            or approval.get("job_id") != job_id
            or approval.get("manifest_hash") != manifest_hash
        ):
            raise ApplicationBlocked("director approval does not match the manifest")
        store = ArtifactStore(self._project_root(), self._job_root())
        pending = []
        replacements = []
        superseded_job_ids = set()
        # Paths skipped because they contain user edits that cannot be traced back to
        # any previously verified publication.  Only populated when preserve_user_edits=True.
        user_preserved_paths = []
        for artifact in manifest["artifacts"]:
            destination = store.validate_project_path(project.slug, artifact["path"])
            project_root = self._project_root() / project.slug
            current = project_root
            for part in Path(artifact["path"]).parts:
                current = current / part
                if current.is_symlink():
                    raise ApplicationBlocked("director publication destination contains a symlink")
            if destination.exists():
                if not destination.is_file():
                    raise ApplicationConflict("director publication destination is not a file")
                digest = "sha256:" + self._file_digest(destination).hex()
                if digest != artifact["content_hash"]:
                    if not supersede:
                        raise ApplicationConflict("director publication would overwrite existing content")
                    previous = self._verified_published_artifact(
                        project, artifact["path"], digest
                    )
                    if previous is None:
                        if preserve_user_edits:
                            # The file was edited by the user after the last known publish.
                            # Keep the user's version intact instead of overwriting it.
                            user_preserved_paths.append(artifact["path"])
                            continue
                        raise ApplicationConflict(
                            "director publication would overwrite unverified existing content"
                        )
                    superseded_job_ids.add(previous[0])
                    replacements.append(
                        (staging / artifact["path"], artifact["path"], previous[1])
                    )
            else:
                pending.append((staging / artifact["path"], artifact["path"]))
        created = []
        replaced = []
        try:
            for source, relative in pending:
                store.publish(source, project.slug, relative, overwrite=False)
                created.append(store.validate_project_path(project.slug, relative))
            for source, relative, previous_source in replacements:
                store.publish(source, project.slug, relative, overwrite=True)
                replaced.append((relative, previous_source))
        except (UnsafePathError, OSError) as exc:
            for path in reversed(created):
                try:
                    path.unlink()
                except OSError:
                    pass
            rollback_failed = False
            for relative, previous_source in reversed(replaced):
                try:
                    store.publish(previous_source, project.slug, relative, overwrite=True)
                except (UnsafePathError, OSError):
                    rollback_failed = True
            if rollback_failed:
                raise ApplicationBlocked("director publication rollback failed") from exc
            raise ApplicationConflict("director publication failed without overwriting content") from exc
        published_paths = [
            artifact["path"] for artifact in manifest["artifacts"]
            if artifact["path"] not in user_preserved_paths
        ]
        receipt = {
            "version": 1,
            "project_id": job.project_id,
            "job_id": job_id,
            "manifest_hash": manifest_hash,
            "status": "published",
            "paths": published_paths,
            "supersedes_job_ids": sorted(superseded_job_ids),
            "published_at": datetime.now(timezone.utc).isoformat(),
            **({"user_preserved_paths": user_preserved_paths} if user_preserved_paths else {}),
        }
        receipt_path = self._project_root() / project.slug / ".mvstudio/jobs" / job_id / "publication.json"
        self._write_atomic_file(receipt_path, canonical_json(receipt), ".publication-")
        self._set_business_stage(status, BusinessStage.EXPORTED, "director.artifacts_published", receipt)
        return _immutable(receipt)

    def run_director_mvp_test(self, job_id):
        """Run the configured Director flow and leave every failure in a terminal state."""
        try:
            return self._run_director_mvp_test(job_id)
        except Exception as exc:
            try:
                job = self.repository.get_job(job_id)
                project = self.repository.get_project(job.project_id)
                self._recover_model_audit_costs(project.project_id, job_id)
                status = self.repository.get_status(job_id)
                if status.runtime_state in {RuntimeState.QUEUED, RuntimeState.RUNNING}:
                    now = datetime.now(timezone.utc)
                    self.repository.set_status(status.transition(RuntimeState.FAILED, now, "mvp_workflow_error"))
                    events = self.repository.list_events(job_id)
                    self.repository.append_event(Event(
                        job_id, (events[-1].seq if events else 0) + 1,
                        "mvp.workflow_failed", now,
                        {"error_code": "mvp_workflow_error", "exception_type": type(exc).__name__},
                    ))
            except Exception:
                pass
            raise

    def _recover_model_audit_costs(self, project_id, job_id):
        audit_path = self._job_root() / job_id / "creative" / "model_audit.json"
        if audit_path.is_symlink() or not audit_path.is_file():
            return
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        existing = {}
        for entry in self.get_project_costs(project_id)["entries"]:
            if entry.get("job_id") != job_id or entry.get("resource_type") != "llm":
                continue
            metadata = entry.get("metadata", {})
            if metadata.get("outcome") == "invalid_response":
                continue
            key = (entry.get("step_id", ""), metadata.get("source_event", ""))
            existing[key] = existing.get(key, 0) + 1
        occurrences = {}
        for call in audit.get("calls", []):
            if not isinstance(call, dict):
                continue
            recoverable = [call]
            if isinstance(call.get("prompt_translation"), dict):
                recoverable.append(call["prompt_translation"])
            for item in recoverable:
                usage = item.get("usage", {})
                try:
                    source_event = item.get("source_event", "")
                    key = (item["event_type"], source_event)
                    occurrences[key] = occurrences.get(key, 0) + 1
                    if occurrences[key] <= existing.get(key, 0):
                        continue
                    metadata = {
                        "model": item.get("model", ""), "event_type": item["event_type"],
                        "invocation": occurrences[key], "recovered_from_audit": True,
                    }
                    if source_event:
                        metadata["source_event"] = source_event
                    self.record_llm_cost(
                        project_id, job_id, item["event_type"],
                        int(usage.get("input_tokens", 0)),
                        int(usage.get("cache_read_tokens", 0)),
                        int(usage.get("output_tokens", 0)),
                        metadata,
                    )
                except (KeyError, TypeError, ValueError):
                    continue

    def run_director_plan(self, job_id):
        """Create and publish the editable planning draft without rendering a test film."""
        def emit(event_type, payload):
            try:
                self._emit_mini_event(job_id, event_type, payload)
            except Exception:
                pass

        try:
            job = self.repository.get_job(job_id)
            draft = self.start_director_animatic_test(job_id)
            validation = self.approve_director_artifacts(job_id)
            emit("progress", {"stage": "publish", "pct": 85, "message": "正在发布草稿…"})
            publication = self.publish_director_artifacts(job_id, supersede=True, preserve_user_edits=True)
            self.localize_project_content(job.project_id)
            emit("done", {"stage": "done", "pct": 100, "message": "分析完成"})
            return _immutable({
                "status": "planning_draft_published",
                "job_id": job_id,
                "draft": draft,
                "validation": validation,
                "publication": publication,
                "user_facing_language": "zh-CN",
            })
        except Exception as exc:
            emit("error", {"message": str(exc), "exception_type": type(exc).__name__})
            try:
                job = self.repository.get_job(job_id)
                project = self.repository.get_project(job.project_id)
                self._recover_model_audit_costs(project.project_id, job_id)
                status = self.repository.get_status(job_id)
                if status.runtime_state in {RuntimeState.QUEUED, RuntimeState.RUNNING}:
                    now = datetime.now(timezone.utc)
                    self.repository.set_status(
                        status.transition(RuntimeState.FAILED, now, "planning_workflow_error")
                    )
                    events = self.repository.list_events(job_id)
                    self.repository.append_event(Event(
                        job_id, (events[-1].seq if events else 0) + 1,
                        "planning.workflow_failed", now,
                        {"error_code": "planning_workflow_error",
                         "exception_type": type(exc).__name__},
                    ))
            except Exception:
                pass
            raise

    def resume_director_plan(self, source_job_id):
        """Continue a failed planning job from its persisted creative checkpoint."""
        self._require_initialized()
        if self.supervisor is None:
            raise ApplicationBlocked("job supervisor is not configured")
        try:
            source_job = self.repository.get_job(source_job_id)
            source_status = self.repository.get_status(source_job_id)
            project = self.repository.get_project(source_job.project_id)
        except RepositoryNotFound as exc:
            raise ApplicationNotFound(source_job_id) from exc
        if (
            source_job.operation != "animatic"
            or source_status.runtime_state is not RuntimeState.FAILED
        ):
            raise ApplicationConflict("only a failed planning task can continue")
        source = self._job_root() / source_job_id
        checkpoint_paths = (
            "creative/beats.json",
            "creative/lyrics_semantic.json",
            "creative/music_map.yaml",
            "creative/character_map.yaml",
            "creative/model_audit.json",
            "creative/visual_score.yaml",
        )
        if source.is_symlink() or any(
            (source / relative).is_symlink() or not (source / relative).is_file()
            for relative in checkpoint_paths
        ):
            raise ApplicationBlocked("failed task has no safe continuation checkpoint")
        prompt_overrides = self.get_project_prompts(project.project_id)
        resume_digest = canonical_hash({
            "resume_from": source_job_id,
            "prompts": prompt_overrides,
            "checkpoint": {
                relative: "sha256:" + self._file_digest(source / relative).hex()
                for relative in checkpoint_paths
            },
        })
        resumed = self.submit_job(
            project.project_id,
            "animatic",
            resume_digest,
            source_job.input_refs,
            source_job.requested_outputs,
            model_policy_ref=source_job.model_policy_ref,
            privacy_consent_ref=source_job.privacy_consent_ref,
        )
        if resumed.status.runtime_state is RuntimeState.SUCCEEDED:
            publication = self.publish_director_artifacts(resumed.job_id, supersede=True, preserve_user_edits=True)
            self.localize_project_content(project.project_id)
            return _immutable({
                "status": "planning_draft_published",
                "job_id": resumed.job_id,
                "resumed_from": source_job_id,
                "validation": {"status": "already_approved"},
                "publication": publication,
                "user_facing_language": "zh-CN",
            })
        if resumed.status.runtime_state is not RuntimeState.QUEUED:
            raise ApplicationConflict("continuation task already exists")
        job_id = resumed.job_id
        staging = self._job_root() / job_id
        staging.mkdir(parents=True, exist_ok=True)
        try:
            for relative in source_job.input_refs:
                (staging / relative).parent.mkdir(parents=True, exist_ok=True)
                self._atomic_copy(
                    self._safe_project_input(project, relative), staging / relative,
                )
            for relative in checkpoint_paths:
                (staging / relative).parent.mkdir(parents=True, exist_ok=True)
                self._atomic_copy(source / relative, staging / relative)

            music_map = self._read_structured_file(staging / "creative/music_map.yaml")
            character_map = self._read_structured_file(staging / "creative/character_map.yaml")
            lyrics_semantic = self._read_structured_file(staging / "creative/lyrics_semantic.json")
            structural_score = self._read_structured_file(staging / "creative/visual_score.yaml")
            upstream_audit = self._read_structured_file(staging / "creative/model_audit.json")
            brief = self._read_structured_file(
                self._project_root() / project.slug / "brief.json"
            )
            if not all(isinstance(value, dict) for value in (
                music_map, character_map, lyrics_semantic, structural_score,
                upstream_audit, brief,
            )):
                raise ApplicationBlocked("continuation checkpoint is invalid")

            from mvstudio.director.creative_planner import draft_creative_score
            from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort

            provider = self.semantic_port or OpenAICompatibleSemanticPort.from_env()
            model = self.semantic_model or os.environ.get("LLM_MODEL", "")
            service = self
            invocation_counts = {}

            class CostRecordingPort:
                translate_chinese_prompts = getattr(
                    provider, "translate_chinese_prompts", False
                )

                def run(self, task):
                    invocation_counts[task.event_type] = invocation_counts.get(task.event_type, 0) + 1
                    source_event = (
                        task.payload.get("source_event", "")
                        if isinstance(task.payload, Mapping) else ""
                    )
                    metadata = {
                        "model": task.model, "event_type": task.event_type,
                        "invocation": invocation_counts[task.event_type],
                    }
                    if source_event:
                        metadata["source_event"] = source_event
                    try:
                        result = provider.run(task)
                    except Exception as exc:
                        usage = (
                            getattr(exc, "input_tokens", 0),
                            getattr(exc, "cache_read_tokens", 0),
                            getattr(exc, "output_tokens", 0),
                        )
                        if any(usage):
                            metadata["outcome"] = "invalid_response"
                            finish_reason = getattr(exc, "finish_reason", "")
                            if finish_reason:
                                metadata["finish_reason"] = finish_reason
                            service.record_llm_cost(
                                project.project_id, job_id, task.event_type,
                                usage[0], usage[1], usage[2], metadata,
                            )
                        raise
                    service.record_llm_cost(
                        project.project_id, job_id, task.event_type,
                        result.input_tokens, result.cache_read_tokens,
                        result.output_tokens, metadata,
                    )
                    return result

            creative = draft_creative_score(
                structural_score, music_map, character_map, lyrics_semantic, brief,
                CostRecordingPort(), model, staging, upstream_audit,
                prompt_overrides=prompt_overrides,
            )
            package = {
                "project_id": project.project_id,
                "brief": brief,
                "music_map": music_map,
                "character_map": character_map,
                "visual_score": creative["visual_score"],
                "animatic": {"enabled": True, "fps": 6},
            }
            self.supervisor.submit(job_id, "director_structural", package)
            completed = self.supervisor.wait(job_id, 300)
            if completed.runtime_state is not RuntimeState.SUCCEEDED:
                raise ApplicationBlocked("continued planning task failed")
            self._set_business_stage(
                completed,
                BusinessStage.VISUAL_SCORE_PENDING_USER,
                "planning.checkpoint_resumed",
                {"source_job_id": source_job_id, "checkpoint": "visual_score"},
            )
            validation = self.approve_director_artifacts(job_id)
            publication = self.publish_director_artifacts(job_id, supersede=True, preserve_user_edits=True)
            return _immutable({
                "status": "planning_draft_published",
                "job_id": job_id,
                "resumed_from": source_job_id,
                "validation": validation,
                "publication": publication,
                "user_facing_language": "zh-CN",
            })
        except Exception as exc:
            try:
                status = self.repository.get_status(job_id)
                if status.runtime_state in {RuntimeState.QUEUED, RuntimeState.RUNNING}:
                    now = datetime.now(timezone.utc)
                    self.repository.set_status(
                        status.transition(RuntimeState.FAILED, now, "planning_resume_error")
                    )
                    events = self.repository.list_events(job_id)
                    self.repository.append_event(Event(
                        job_id, (events[-1].seq if events else 0) + 1,
                        "planning.resume_failed", now,
                        {"error_code": "planning_resume_error",
                         "exception_type": type(exc).__name__,
                         "source_job_id": source_job_id},
                    ))
            except Exception:
                pass
            raise

    def _run_director_mvp_test(self, job_id):
        job = self.repository.get_job(job_id)
        project = self.repository.get_project(job.project_id)
        status = self.repository.get_status(job_id)
        if status.runtime_state is RuntimeState.SUCCEEDED:
            draft = {"status": "resumed_after_director_publication"}
            approval = {"status": "already_approved"}
            receipt_path = (
                self._project_root() / project.slug / ".mvstudio" / "jobs" / job_id / "publication.json"
            )
            try:
                publication = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApplicationBlocked("director publication receipt is missing") from exc
        else:
            draft = self._start_director_animatic_test(job_id, offline=False, creative_model=False)
            approval = self.approve_director_artifacts(job_id)
            publication = self.publish_director_artifacts(job_id)
        project_root = self._project_root() / project.slug
        audio = [path for path in job.input_refs if path.startswith("inputs/audio/")]
        lyrics = [path for path in job.input_refs if path.startswith("inputs/lyrics/")]
        characters = [path for path in job.input_refs if path.startswith("inputs/characters/")]
        if len(audio) != 1 or len(lyrics) != 1 or len(characters) < 2:
            raise ApplicationConflict("two-shot MVP requires audio, timed lyrics and two characters")
        relative = "outputs/final_mvp_" + job_id + ".mp4"
        destination = project_root / relative
        work = self._job_root() / job_id / "mvp-render"
        work.mkdir(parents=True, exist_ok=True)
        temporary = work / "final.mp4"
        from mvstudio.director.mvp_renderer import MvpRenderError, render_two_shot_mvp

        try:
            qc = render_two_shot_mvp(
                project_root / audio[0], project_root / lyrics[0],
                [project_root / path for path in characters], temporary,
            )
        except (OSError, MvpRenderError) as exc:
            raise ApplicationBlocked(str(exc)) from exc
        digest = "sha256:" + self._file_digest(temporary).hex()
        if destination.exists():
            if not destination.is_file() or "sha256:" + self._file_digest(destination).hex() != digest:
                raise ApplicationConflict("two-shot MVP destination differs")
        else:
            try:
                ArtifactStore(self._project_root(), self._job_root()).publish(
                    temporary, project.slug, relative, overwrite=False
                )
            except (UnsafePathError, OSError) as exc:
                raise ApplicationBlocked("two-shot MVP publication failed") from exc
        artifact_id = "artifact-" + hashlib.sha256((job_id + relative + digest).encode()).hexdigest()[:24]
        with self.database.connect() as db:
            exists = db.execute("SELECT 1 FROM artifacts WHERE artifact_id=?", (artifact_id,)).fetchone()
        if not exists:
            self.repository.add_artifact(Artifact(
                artifact_id, project.project_id, job_id, "1", relative,
                (job.input_digest,), digest, datetime.now(timezone.utc),
                "mvstudio.director.mvp_renderer", "published",
            ))
        payload = {
            "project_id": project.project_id, "job_id": job_id,
            "status": "published", "output": relative, "content_hash": digest,
            "shot_count": 2, "local_render": True, "provider_cost_yuan": 0,
            "qc": qc, "draft": dict(draft), "approval": dict(approval),
            "published_artifact_count": len(publication["paths"]) + 1,
        }
        self._set_business_stage(
            self.repository.get_status(job_id), BusinessStage.EXPORTED,
            "mvp.two_shot_published", payload,
        )
        return _immutable(payload)

    def create_project(self, slug, brief, project_id=None):
        self._require_initialized()
        if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
            raise ApplicationConflict("invalid slug")
        if not isinstance(brief, Mapping):
            raise ApplicationConflict("brief must be a mapping")
        try:
            frozen = freeze_json(brief)
            brief_bytes = canonical_json(frozen)
            digest = canonical_hash(frozen)
        except Exception as exc:
            raise ApplicationConflict("brief is not JSON-compatible") from exc
        identity_digest = canonical_hash({"slug": slug, "brief_sha256": digest})
        project_id = project_id or "project-" + identity_digest.split(":", 1)[1][:32]
        root = self._project_root() / slug
        resolved = root.resolve()
        try: resolved.relative_to(self._project_root().resolve())
        except ValueError as exc: raise ApplicationBlocked("project path escapes workspace") from exc
        if root.exists() and root.is_symlink():
            raise ApplicationBlocked("project path is a symlink")
        try:
            project = self.repository.get_project(project_id)
            if project.slug != slug or project.brief_sha256 != digest:
                raise ApplicationConflict("project id already has different content")
            self._initialize_project_directory(root, brief_bytes)
            return ProjectResult(project, _immutable(frozen))
        except RepositoryNotFound:
            pass
        with self.database.connect() as db:
            row = db.execute("SELECT project_id,brief_sha256 FROM projects WHERE slug=?", (slug,)).fetchone()
        if row:
            if row[1] == digest:
                project = self.repository.get_project(row[0])
                self._initialize_project_directory(root, brief_bytes)
                return ProjectResult(project, _immutable(frozen))
            raise ApplicationConflict("slug already has different content")
        self._initialize_project_directory(root, brief_bytes)
        project = Project(project_id, slug, "projects/" + slug, digest, datetime.now(timezone.utc))
        try:
            self.repository.add_project(project)
        except RepositoryConflict as exc:
            raise ApplicationConflict(str(exc)) from exc
        return ProjectResult(project, _immutable(frozen))

    def submit_job(self, project_id, operation, input_digest, input_refs=(), requested_outputs=(),
                   idempotency_key=None, model_policy_ref="default", privacy_consent_ref="local-only",
                   auto_start=False, executor="fake", executor_input=None):
        self._require_initialized()
        try: self.repository.get_project(project_id)
        except RepositoryNotFound as exc: raise ApplicationNotFound(project_id) from exc
        try:
            if isinstance(input_refs, (str, bytes)) or isinstance(requested_outputs, (str, bytes)):
                raise TypeError("refs and outputs must be sequences")
            input_refs = tuple(input_refs)
            requested_outputs = tuple(requested_outputs)
            request = {"project_id": project_id, "operation": operation, "input_digest": input_digest,
                       "input_refs": input_refs, "requested_outputs": requested_outputs,
                       "model_policy_ref": model_policy_ref, "privacy_consent_ref": privacy_consent_ref}
            canonical_json(request)
            request_hash = canonical_hash(request).split(":", 1)[1]
            idem = idempotency_key or "idem-" + request_hash
            job_id = "job-" + request_hash[:32]
            spec = JobSpec(job_id, project_id, operation, input_refs, input_digest, "v1", "v1",
                           model_policy_ref, privacy_consent_ref, requested_outputs, idem)
        except (DomainValidationError, TypeError, ValueError) as exc:
            raise ApplicationConflict("invalid job request") from exc
        status = JobStatus(job_id, RuntimeState.QUEUED, BusinessStage.INTAKE_PENDING, 1, datetime.now(timezone.utc))
        try:
            with self.database.connect() as db:
                db.execute("BEGIN")
                row = db.execute("SELECT * FROM jobs WHERE idempotency_key=?", (idem,)).fetchone()
                if row:
                    if row[-1] != spec.canonical_digest(): raise ApplicationConflict("idempotency key conflict")
                    db.commit(); result = JobResult(self.repository._job(row), self.repository.get_status(job_id))
                else:
                    db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (spec.job_id, spec.project_id, spec.operation, canonical_json(spec.input_refs).decode(), spec.input_digest, spec.pipeline_version, spec.contract_version, spec.model_policy_ref, spec.privacy_consent_ref, canonical_json(spec.requested_outputs).decode(), spec.idempotency_key, spec.canonical_digest()))
                    db.execute("INSERT INTO job_status VALUES (?,?,?,?,?,?)", (job_id, status.runtime_state.value, status.business_stage.value, status.attempt, status.updated_at.isoformat(), status.error_code))
                    db.commit(); result = JobResult(spec, status)
        except ApplicationError: raise
        except (sqlite3.IntegrityError, RepositoryNotFound) as exc: raise ApplicationConflict(str(exc)) from exc
        if auto_start:
            self.start_job(result.job_id, executor, executor_input)
            return JobResult(result.job_spec, self.repository.get_status(result.job_id))
        return result

    def start_job(self, job_id, executor="fake", executor_input=None):
        if self.supervisor is None: raise ApplicationBlocked("job supervisor is not configured")
        from mv_platform.supervisor import JobAlreadyActive
        try: return self.supervisor.submit(job_id, executor, executor_input)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc
        except JobAlreadyActive as exc:
            raise ApplicationConflict("another task is already running") from exc

    def inspect_job(self, job_id):
        try:
            spec = self.repository.get_job(job_id); status = self.repository.get_status(job_id)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc
        return JobInspection(spec, status, tuple(self.repository.list_events(job_id)), tuple(self.repository.list_artifacts(job_id)), spec.canonical_digest())

    def list_events(self, job_id, after_seq=0):
        if isinstance(after_seq, bool) or not isinstance(after_seq, int) or after_seq < 0: raise ApplicationConflict("invalid event cursor")
        try: self.repository.get_job(job_id)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc
        return tuple(self.repository.list_events(job_id, after_seq))

    def list_artifacts(self, job_id):
        try: self.repository.get_job(job_id)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc
        return tuple(self.repository.list_artifacts(job_id))

    def cancel_job(self, job_id, grace_seconds=1.0):
        try: status = self.repository.get_status(job_id)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc
        if status.runtime_state == RuntimeState.CANCELLED: return JobResult(self.repository.get_job(job_id), status)
        if status.runtime_state in {RuntimeState.SUCCEEDED, RuntimeState.FAILED, RuntimeState.BLOCKED}: return JobResult(self.repository.get_job(job_id), status)
        if self.supervisor is not None:
            try: self.supervisor.cancel(job_id, grace_seconds); return JobResult(self.repository.get_job(job_id), self.repository.get_status(job_id))
            except Exception as exc:
                if status.runtime_state != RuntimeState.QUEUED: raise ApplicationError(str(exc)) from exc
        if status.runtime_state == RuntimeState.QUEUED:
            updated = status.transition(RuntimeState.CANCELLED, datetime.now(timezone.utc), "cancelled")
            event_payload = canonical_json({"error_code": "cancelled"}).decode("utf-8")
            try:
                with self.database.connect() as db:
                    db.execute("BEGIN IMMEDIATE")
                    result = db.execute(
                        "UPDATE job_status SET runtime_state=?, updated_at=?, error_code=? "
                        "WHERE job_id=? AND runtime_state=?",
                        (RuntimeState.CANCELLED.value, updated.updated_at.isoformat(), "cancelled",
                         job_id, RuntimeState.QUEUED.value),
                    )
                    if result.rowcount != 1:
                        raise ApplicationConflict("job is no longer queued")
                    row = db.execute(
                        "SELECT COALESCE(MAX(seq),0) FROM events WHERE job_id=?", (job_id,)
                    ).fetchone()
                    db.execute(
                        "INSERT INTO events VALUES (?,?,?,?,?)",
                        (job_id, row[0] + 1, "job.cancelled", updated.updated_at.isoformat(), event_payload),
                    )
                    db.commit()
            except ApplicationError:
                raise
            except sqlite3.Error as exc:
                raise ApplicationError("queued cancellation was rolled back") from exc
            return JobResult(self.repository.get_job(job_id), updated)
        raise ApplicationBlocked("job supervisor is not configured")

    def recover(self):
        if self.supervisor is None: raise ApplicationBlocked("job supervisor is not configured")
        return self.supervisor.recover()

    def shutdown(self):
        if self.supervisor is None: raise ApplicationBlocked("job supervisor is not configured")
        return self.supervisor.shutdown()
