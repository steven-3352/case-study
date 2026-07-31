import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from mv_platform.domain import DomainValidationError, Event, JobSpec, JobStatus, Project
from mv_platform.domain.hashing import canonical_hash, canonical_json, freeze_json
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.infrastructure.repositories import Repository, RepositoryConflict, RepositoryNotFound
from mv_platform.infrastructure.artifacts import ArtifactStore, UnsafePathError


class ApplicationError(Exception):
    pass


class ApplicationConflict(ApplicationError):
    pass


class ApplicationNotFound(ApplicationError):
    pass


class ApplicationBlocked(ApplicationError):
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


class ApplicationService:
    _PROJECT_DIRECTORIES = (
        "inputs/audio", "inputs/lyrics", "inputs/characters",
        "creative", "assets/source", "assets/generated", "outputs",
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
        self._initialized = False

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
        self._initialized = True
        return None

    def _require_initialized(self):
        if not self._initialized:
            raise ApplicationBlocked("service is not initialized")

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
        audio = [path for path in job.input_refs if path.startswith("inputs/audio/")]
        lyrics = [path for path in job.input_refs if path.startswith("inputs/lyrics/")]
        characters = [path for path in job.input_refs if path.startswith("inputs/characters/")]
        if len(audio) != 1 or len(lyrics) != 1 or not characters:
            raise ApplicationConflict("director intake requires one audio, one lyrics file and character images")
        if len(audio) + len(lyrics) + len(characters) != len(job.input_refs):
            raise ApplicationConflict("director intake contains unsupported input refs")
        staging = self._job_root() / job_id
        if staging.is_symlink():
            raise ApplicationBlocked("job staging path is a symlink")
        staging.mkdir(parents=True, exist_ok=True)
        for relative in job.input_refs:
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
        payload = {
            "project_id": project.project_id,
            "audio": audio[0],
            "lyrics": lyrics[0],
            "characters": characters,
        }
        return self.supervisor.submit(job_id, "director_intake", payload)

    def start_director_animatic_test(self, job_id):
        """Use the configured semantic provider for a structural Animatic test."""
        return self._start_director_animatic_test(job_id, offline=False)

    def start_director_animatic_offline_test(self, job_id):
        """Use explicit non-semantic placeholders for an offline structural test."""
        return self._start_director_animatic_test(job_id, offline=True)

    def _start_director_animatic_test(self, job_id, offline):
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
        audio = [path for path in job.input_refs if path.startswith("inputs/audio/")]
        lyrics = [path for path in job.input_refs if path.startswith("inputs/lyrics/")]
        characters = [path for path in job.input_refs if path.startswith("inputs/characters/")]
        if len(audio) != 1 or len(lyrics) != 1 or not characters:
            raise ApplicationConflict(
                "director animatic test requires one audio, one timed lyrics file and character images"
            )
        if len(audio) + len(lyrics) + len(characters) != len(job.input_refs):
            raise ApplicationConflict("director animatic test contains unsupported input refs")
        staging = self._job_root() / job_id
        if staging.is_symlink():
            raise ApplicationBlocked("job staging path is a symlink")
        staging.mkdir(parents=True, exist_ok=True)
        for relative in job.input_refs:
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

        from mvstudio.director.drafting import draft_maps
        from mvstudio.director.intake import inspect_intake
        from mvstudio.director.structural_planner import plan_structural_score
        intake = inspect_intake(
            {
                "project_id": project.project_id,
                "audio": audio[0],
                "lyrics": lyrics[0],
                "characters": characters,
            },
            staging,
        )
        timed_path = staging / "intake" / "lyrics_timed.json"
        if not timed_path.is_file() or intake["lyrics"]["alignment_state"] != "aligned":
            raise ApplicationBlocked("director animatic test requires timed LRC lyrics")
        brief_path = self._project_root() / project.slug / "brief.json"
        try:
            brief = json.loads(brief_path.read_bytes())
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
        drafted = draft_maps(intake, timed, brief, port, staging, model)
        score = plan_structural_score(
            drafted["music_map"],
            drafted["character_map"],
            drafted["lyrics_semantic"],
            brief,
            staging,
        )
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
        destination_relative = "outputs/structural_animatic_" + job_id + ".mp4"
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
            or relative in {"intake/intake_manifest.json", "intake/lyrics_timed.json"}
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

    def publish_director_artifacts(self, job_id):
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
                    raise ApplicationConflict("director publication would overwrite existing content")
            else:
                pending.append((staging / artifact["path"], artifact["path"]))
        created = []
        try:
            for source, relative in pending:
                store.publish(source, project.slug, relative, overwrite=False)
                created.append(store.validate_project_path(project.slug, relative))
        except (UnsafePathError, OSError) as exc:
            for path in reversed(created):
                try:
                    path.unlink()
                except OSError:
                    pass
            raise ApplicationConflict("director publication failed without overwriting content") from exc
        receipt = {
            "version": 1,
            "project_id": job.project_id,
            "job_id": job_id,
            "manifest_hash": manifest_hash,
            "status": "published",
            "paths": [artifact["path"] for artifact in manifest["artifacts"]],
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        receipt_path = self._project_root() / project.slug / ".mvstudio/jobs" / job_id / "publication.json"
        self._write_atomic_file(receipt_path, canonical_json(receipt), ".publication-")
        self._set_business_stage(status, BusinessStage.EXPORTED, "director.artifacts_published", receipt)
        return _immutable(receipt)

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
        if auto_start: return self.start_job(result.job_id, executor, executor_input)
        return result

    def start_job(self, job_id, executor="fake", executor_input=None):
        if self.supervisor is None: raise ApplicationBlocked("job supervisor is not configured")
        try: return self.supervisor.submit(job_id, executor, executor_input)
        except RepositoryNotFound as exc: raise ApplicationNotFound(job_id) from exc

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
