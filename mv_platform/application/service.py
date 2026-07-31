import os
import re
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

    def __init__(self, settings, database, supervisor=None, workspace_root=None, source_root=None):
        self.settings = settings
        self.database = database
        self.supervisor = supervisor
        if workspace_root is None:
            raise ApplicationBlocked("workspace_root is required")
        self.workspace_root = Path(workspace_root).resolve()
        self.repository = Repository(database)
        self.source_root = Path(source_root).resolve() if source_root is not None else None
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
