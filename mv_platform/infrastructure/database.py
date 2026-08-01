import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path):
        self.path = Path(path)

    def connect(self):
        connection = sqlite3.connect(str(self.path), isolation_level=None)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def migrate(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
              project_id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, root TEXT NOT NULL,
              brief_sha256 TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
              operation TEXT NOT NULL, input_refs TEXT NOT NULL, input_digest TEXT NOT NULL,
              pipeline_version TEXT NOT NULL, contract_version TEXT NOT NULL, model_policy_ref TEXT NOT NULL,
              privacy_consent_ref TEXT NOT NULL, requested_outputs TEXT NOT NULL,
              idempotency_key TEXT NOT NULL UNIQUE, canonical_digest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_status (
              job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), runtime_state TEXT NOT NULL,
              business_stage TEXT NOT NULL, attempt INTEGER NOT NULL, updated_at TEXT NOT NULL, error_code TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
              job_id TEXT NOT NULL REFERENCES jobs(job_id), seq INTEGER NOT NULL,
              event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL,
              PRIMARY KEY(job_id, seq)
            );
            CREATE TABLE IF NOT EXISTS artifacts (
              artifact_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
              job_id TEXT NOT NULL REFERENCES jobs(job_id), schema_version TEXT NOT NULL,
              relative_path TEXT NOT NULL, input_hashes TEXT NOT NULL, content_hash TEXT NOT NULL,
              created_at TEXT NOT NULL, producer TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cost_entries (
              entry_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
              job_id TEXT REFERENCES jobs(job_id), step_id TEXT NOT NULL, resource_type TEXT NOT NULL,
              quantity REAL NOT NULL, unit_price REAL NOT NULL, input_tokens INTEGER NOT NULL,
              cache_read_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
              multiplier REAL NOT NULL, amount_yuan REAL NOT NULL, occurred_at TEXT NOT NULL,
              metadata TEXT NOT NULL
            );
            """)
