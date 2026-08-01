import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from mv_platform.domain import Artifact, Event, JobSpec, JobStatus, Project
from mv_platform.domain.states import BusinessStage, RuntimeState
from mv_platform.domain.hashing import canonical_json


class RepositoryConflict(Exception):
    pass


class RepositoryNotFound(Exception):
    pass


def _json(value):
    return canonical_json(value).decode("utf-8")


def _dt(value):
    return value.isoformat()


class Repository:
    def __init__(self, database):
        self.database = database

    def _write(self, fn):
        db = self.database.connect()
        try:
            db.execute("BEGIN")
            result = fn(db)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def add_project(self, project):
        def run(db):
            try:
                db.execute("INSERT INTO projects VALUES (?,?,?,?,?)", (project.project_id, project.slug, project.root, project.brief_sha256, _dt(project.created_at)))
            except sqlite3.IntegrityError as exc:
                raise RepositoryConflict("project already exists") from exc
            return project
        return self._write(run)

    def get_project(self, project_id):
        with self.database.connect() as db:
            row = db.execute("SELECT project_id,slug,root,brief_sha256,created_at FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if not row: raise RepositoryNotFound(project_id)
        return Project(row[0], row[1], row[2], row[3], datetime.fromisoformat(row[4]))

    def list_projects(self):
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT project_id,slug,root,brief_sha256,created_at "
                "FROM projects ORDER BY created_at DESC, project_id DESC"
            ).fetchall()
        return [Project(row[0], row[1], row[2], row[3], datetime.fromisoformat(row[4])) for row in rows]

    def add_job(self, job):
        def run(db):
            try:
                db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (job.job_id, job.project_id, job.operation, _json(job.input_refs), job.input_digest, job.pipeline_version, job.contract_version, job.model_policy_ref, job.privacy_consent_ref, _json(job.requested_outputs), job.idempotency_key, job.canonical_digest()))
            except sqlite3.IntegrityError:
                row = db.execute("SELECT * FROM jobs WHERE idempotency_key=?", (job.idempotency_key,)).fetchone()
                if row and row[-1] == job.canonical_digest(): return self._job(row)
                raise RepositoryConflict("idempotency key conflict")
            return job
        return self._write(run)

    def _job(self, row):
        return JobSpec(row[0], row[1], row[2], tuple(json.loads(row[3])), row[4], row[5], row[6], row[7], row[8], tuple(json.loads(row[9])), row[10])

    def get_job(self, job_id):
        with self.database.connect() as db: row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if not row: raise RepositoryNotFound(job_id)
        return self._job(row)

    def list_jobs(self, project_id):
        with self.database.connect() as db:
            if not db.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone():
                raise RepositoryNotFound(project_id)
            rows = db.execute(
                "SELECT jobs.*, job_status.runtime_state, job_status.business_stage, "
                "job_status.attempt, job_status.updated_at, job_status.error_code "
                "FROM jobs JOIN job_status ON job_status.job_id=jobs.job_id "
                "WHERE jobs.project_id=? ORDER BY job_status.updated_at DESC, jobs.job_id DESC",
                (project_id,),
            ).fetchall()
        return [
            (self._job(row[:12]), JobStatus(row[0], RuntimeState(row[12]), BusinessStage(row[13]), row[14], datetime.fromisoformat(row[15]), row[16]))
            for row in rows
        ]

    def set_status(self, status):
        def run(db):
            if not db.execute("SELECT 1 FROM jobs WHERE job_id=?", (status.job_id,)).fetchone(): raise RepositoryNotFound(status.job_id)
            db.execute("INSERT OR REPLACE INTO job_status VALUES (?,?,?,?,?,?)", (status.job_id, status.runtime_state.value, status.business_stage.value, status.attempt, _dt(status.updated_at), status.error_code))
            return status
        return self._write(run)

    def get_status(self, job_id):
        with self.database.connect() as db: row = db.execute("SELECT * FROM job_status WHERE job_id=?", (job_id,)).fetchone()
        if not row: raise RepositoryNotFound(job_id)
        return JobStatus(row[0], RuntimeState(row[1]), BusinessStage(row[2]), row[3], datetime.fromisoformat(row[4]), row[5])

    def append_event(self, event):
        def run(db):
            if not db.execute("SELECT 1 FROM jobs WHERE job_id=?", (event.job_id,)).fetchone(): raise RepositoryNotFound(event.job_id)
            row = db.execute("SELECT COALESCE(MAX(seq),0) FROM events WHERE job_id=?", (event.job_id,)).fetchone()
            if event.seq != row[0] + 1: raise RepositoryConflict("event sequence must be strictly monotonic")
            db.execute("INSERT INTO events VALUES (?,?,?,?,?)", (event.job_id, event.seq, event.event_type, _dt(event.occurred_at), _json(event.payload)))
            return event
        return self._write(run)

    def list_events(self, job_id, after_seq=0):
        with self.database.connect() as db: rows = db.execute("SELECT * FROM events WHERE job_id=? AND seq>? ORDER BY seq", (job_id, after_seq)).fetchall()
        return [Event(r[0], r[1], r[2], datetime.fromisoformat(r[3]), json.loads(r[4])) for r in rows]

    def add_artifact(self, artifact):
        def run(db):
            job = db.execute("SELECT project_id FROM jobs WHERE job_id=?", (artifact.job_id,)).fetchone()
            if not job:
                raise RepositoryNotFound(artifact.job_id)
            if job[0] != artifact.project_id:
                raise RepositoryConflict("artifact project does not match job project")
            try: db.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?,?,?,?)", (artifact.artifact_id, artifact.project_id, artifact.job_id, artifact.schema_version, artifact.relative_path, _json(artifact.input_hashes), artifact.content_hash, _dt(artifact.created_at), artifact.producer, artifact.status))
            except sqlite3.IntegrityError as exc: raise RepositoryConflict("artifact already exists") from exc
            return artifact
        return self._write(run)

    def list_artifacts(self, job_id):
        with self.database.connect() as db: rows = db.execute("SELECT * FROM artifacts WHERE job_id=? ORDER BY created_at, artifact_id", (job_id,)).fetchall()
        return [Artifact(r[0], r[1], r[2], r[3], r[4], tuple(json.loads(r[5])), r[6], datetime.fromisoformat(r[7]), r[8], r[9]) for r in rows]
