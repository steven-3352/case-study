import multiprocessing
import os
import queue
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mv_platform.domain import Event, JobStatus
from mv_platform.domain.states import RuntimeState
from mv_platform.infrastructure.repositories import Repository, RepositoryNotFound
from mv_platform.executors.fake import run_fake, validate_input


class SupervisorError(Exception):
    pass


class JobAlreadyActive(SupervisorError):
    pass


class UnknownExecutor(SupervisorError):
    pass


class InvalidExecutorInput(SupervisorError, ValueError):
    pass


_CHILD_ENV_ALLOWLIST = frozenset({
    "LANG", "LC_ALL", "LC_CTYPE", "PATH", "SYSTEMROOT", "TZ", "WINDIR",
})


@dataclass(frozen=True)
class SupervisorSnapshot:
    job_id: str
    runtime_state: RuntimeState
    status: JobStatus
    pid: object = None
    alive: bool = False
    staging_dir: str = ""

    @property
    def terminal(self):
        return self.runtime_state in {RuntimeState.SUCCEEDED, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.BLOCKED}


def _worker(executor_input, staging, cancelled, messages):
    child_environment = {
        key: value for key, value in os.environ.items() if key in _CHILD_ENV_ALLOWLIST
    }
    os.environ.clear()
    os.environ.update(child_environment)

    def send(message):
        messages.put(message)
    try:
        run_fake(executor_input, staging, cancelled, send)
    except Exception as exc:
        messages.put({"kind": "failed", "error_code": "worker_error", "detail": type(exc).__name__})


class JobSupervisor:
    def __init__(self, database, staging_root, max_active_jobs):
        if isinstance(max_active_jobs, bool) or not isinstance(max_active_jobs, int) or max_active_jobs < 1:
            raise ValueError("max_active_jobs must be positive")
        self.database = database
        self.repository = Repository(database)
        self.staging_root = Path(staging_root).resolve()
        self.max_active_jobs = max_active_jobs
        self._context = multiprocessing.get_context("spawn")
        self._workers = {}
        self._terminal = set()
        self.staging_root.mkdir(parents=True, exist_ok=True)

    def _staging_path(self, job_id):
        if not isinstance(job_id, str) or not job_id or job_id in {".", ".."}:
            raise SupervisorError("invalid job identifier")
        identifier = Path(job_id)
        if identifier.is_absolute() or len(identifier.parts) != 1 or "\\" in job_id:
            raise SupervisorError("invalid job identifier")
        staging = self.staging_root / job_id
        resolved = staging.resolve()
        try:
            resolved.relative_to(self.staging_root)
        except ValueError as exc:
            raise SupervisorError("job staging path escapes root") from exc
        if staging.is_symlink():
            raise SupervisorError("job staging path cannot be a symlink")
        return staging

    @property
    def model_call_count(self):
        return 0

    @property
    def token_count(self):
        return 0

    def _now(self):
        return datetime.now(timezone.utc)

    def _status(self, job_id):
        return self.repository.get_status(job_id)

    def _event(self, job_id, event_type, payload=None):
        events = self.repository.list_events(job_id)
        event = Event(job_id, (events[-1].seq if events else 0) + 1, event_type, self._now(), payload or {})
        self.repository.append_event(event)

    def _snapshot(self, job_id):
        status = self._status(job_id)
        worker = self._workers.get(job_id)
        return SupervisorSnapshot(job_id, status.runtime_state, status, worker["process"].pid if worker else None,
                                  bool(worker and worker["process"].is_alive()), str(worker["staging"]) if worker else str(self.staging_root / job_id))

    def submit(self, job_id, executor="fake", executor_input=None):
        staging = self._staging_path(job_id)
        if executor != "fake":
            raise UnknownExecutor(executor)
        try:
            status = self._status(job_id)
            self.repository.get_job(job_id)
        except RepositoryNotFound as exc:
            raise SupervisorError("unknown job") from exc
        if job_id in self._workers or status.runtime_state == RuntimeState.RUNNING:
            raise JobAlreadyActive(job_id)
        if status.runtime_state != RuntimeState.QUEUED:
            raise SupervisorError("terminal or non-queued job")
        try:
            executor_input = validate_input(executor_input)
        except ValueError as exc:
            raise InvalidExecutorInput(str(exc)) from exc
        if len(self._workers) >= self.max_active_jobs:
            raise SupervisorError("maximum active jobs reached")
        staging.mkdir(parents=True, exist_ok=True)
        messages = self._context.Queue()
        cancelled = self._context.Event()
        process = self._context.Process(target=_worker, args=(executor_input, str(staging), cancelled, messages))
        process.start()
        self._workers[job_id] = {"process": process, "messages": messages, "cancelled": cancelled, "staging": staging}
        try:
            self.repository.set_status(status.transition(RuntimeState.RUNNING, self._now()))
            self._event(job_id, "job.started", {"pid": process.pid})
        except Exception:
            cancelled.set()
            if process.is_alive():
                process.terminate()
            process.join(timeout=1)
            del self._workers[job_id]
            raise
        return self._snapshot(job_id)

    def _finish(self, job_id, state, error_code=None, event_type=None):
        if job_id in self._terminal:
            return
        status = self._status(job_id)
        if status.runtime_state in {RuntimeState.SUCCEEDED, RuntimeState.FAILED, RuntimeState.CANCELLED, RuntimeState.BLOCKED}:
            self._terminal.add(job_id)
            return
        self.repository.set_status(status.transition(state, self._now(), error_code))
        self._event(job_id, event_type or "job." + state.value, {"error_code": error_code} if error_code else {})
        self._terminal.add(job_id)

    def tick(self):
        for job_id, worker in list(self._workers.items()):
            terminal = False
            while True:
                try:
                    message = worker["messages"].get_nowait()
                except queue.Empty:
                    break
                if not isinstance(message, dict) or message.get("kind") not in {"progress", "succeeded", "failed", "cancelled"}:
                    self._finish(job_id, RuntimeState.FAILED, "malformed_message")
                    terminal = True
                    continue
                kind = message["kind"]
                if kind == "progress":
                    if not terminal and job_id not in self._terminal:
                        self._event(job_id, "job.progress", {"step": message.get("step"), "steps": message.get("steps")})
                elif not terminal and job_id not in self._terminal:
                    state = {"succeeded": RuntimeState.SUCCEEDED, "failed": RuntimeState.FAILED, "cancelled": RuntimeState.CANCELLED}[kind]
                    self._finish(job_id, state, message.get("error_code"), "job." + kind)
                    terminal = True
            if not worker["process"].is_alive():
                if job_id not in self._terminal:
                    if worker.get("cancel_requested"):
                        self._finish(job_id, RuntimeState.CANCELLED, "cancelled", "job.cancelled")
                    else:
                        self._finish(job_id, RuntimeState.FAILED, "worker_exit")
                worker["process"].join()
                del self._workers[job_id]
        return None

    def wait(self, job_id, timeout):
        deadline = time.monotonic() + timeout
        while True:
            self.tick()
            snapshot = self._snapshot(job_id)
            if snapshot.terminal:
                worker = self._workers.get(job_id)
                if worker:
                    worker["process"].join(timeout=0.2)
                    self.tick()
                return self._snapshot(job_id)
            if time.monotonic() >= deadline:
                raise TimeoutError(job_id)
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))

    def cancel(self, job_id, grace_seconds):
        worker = self._workers.get(job_id)
        if not worker:
            status = self._status(job_id)
            if status.runtime_state == RuntimeState.CANCELLED:
                return self._snapshot(job_id)
            raise SupervisorError("job is not active")
        worker["cancel_requested"] = True
        worker["cancelled"].set()
        deadline = time.monotonic() + max(0.0, grace_seconds)
        while time.monotonic() < deadline and worker["process"].is_alive():
            self.tick()
            time.sleep(0.005)
        if worker["process"].is_alive():
            worker["process"].terminate()
            worker["process"].join(timeout=1)
            if worker["process"].is_alive():
                worker["process"].kill()
                worker["process"].join(timeout=1)
        self.tick()
        if job_id not in self._terminal:
            self._finish(job_id, RuntimeState.CANCELLED, "cancelled", "job.cancelled")
        self.tick()
        return self._snapshot(job_id)

    def snapshot(self, job_id):
        return self._snapshot(job_id)

    def recover(self):
        with self.database.connect() as db:
            ids = [row[0] for row in db.execute("SELECT job_id FROM job_status WHERE runtime_state=?", (RuntimeState.RUNNING.value,))]
        for job_id in ids:
            if job_id not in self._workers:
                status = self._status(job_id)
                self.repository.set_status(JobStatus(job_id, RuntimeState.QUEUED, status.business_stage,
                                                     status.attempt, self._now()))
                self._event(job_id, "job.recovered")

    def shutdown(self):
        for job_id in list(self._workers):
            self.cancel(job_id, 0.05)


__all__ = ["JobSupervisor", "SupervisorError", "JobAlreadyActive", "UnknownExecutor", "SupervisorSnapshot"]
