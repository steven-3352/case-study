import asyncio
import json
import time
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from mv_platform.application.service import (
    ApplicationBlocked, ApplicationConflict, ApplicationError, ApplicationNotFound,
)
from apps.runtime import build_service


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectRequest(StrictModel):
    slug: str
    brief: Mapping[str, Any]
    project_id: Optional[str] = None


class JobRequest(StrictModel):
    operation: str
    input_digest: str
    input_refs: list[str] = Field(default_factory=list)
    requested_outputs: list[str] = Field(default_factory=list)
    idempotency_key: Optional[str] = None
    model_policy_ref: str = "default"
    privacy_consent_ref: str = "local-only"
    auto_start: bool = False
    executor: str = "fake"
    executor_input: Optional[Mapping[str, Any]] = None


class StartRequest(StrictModel):
    executor: str = "fake"
    executor_input: Optional[Mapping[str, Any]] = None


class CancelRequest(StrictModel):
    grace_seconds: float = 1.0


def _jsonable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, MappingProxyType) or isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, set):
        return sorted(_jsonable(item) for item in value)
    return value


def _result(value):
    if hasattr(value, "job_spec") and hasattr(value, "status"):
        result = {"job_spec": _jsonable(value.job_spec), "status": _jsonable(value.status)}
        result["canonical_job_digest"] = value.canonical_job_digest
        if hasattr(value, "events"):
            result["events"] = _jsonable(value.events)
            result["artifacts"] = _jsonable(value.artifacts)
        return result
    if hasattr(value, "project") and hasattr(value, "brief"):
        result = {"project": _jsonable(value.project), "brief": _jsonable(value.brief)}
        result["project_id"] = value.project_id
        result["slug"] = value.slug
        result["brief_sha256"] = value.brief_sha256
        return result
    return _jsonable(value)


def _error_response(exc):
    if isinstance(exc, ApplicationNotFound):
        status = 404
        detail = "not found"
    elif isinstance(exc, ApplicationConflict):
        status = 409
        detail = "conflict"
    elif isinstance(exc, ApplicationBlocked):
        status = 423
        detail = "blocked"
    else:
        status = 400
        detail = "application error"
    return JSONResponse({"detail": detail}, status_code=status)


def create_app(service=None, workspace_root=None):
    owned = service is None
    app = FastAPI()
    app.state.service = service

    @app.on_event("startup")
    async def startup():
        if app.state.service is None:
            app.state.service = build_service(workspace_root)

    @app.on_event("shutdown")
    async def shutdown():
        if owned and app.state.service is not None:
            app.state.service.shutdown()

    @app.exception_handler(ApplicationError)
    async def application_error(_: Request, exc: ApplicationError):
        return _error_response(exc)

    @app.exception_handler(ValueError)
    async def value_error(_: Request, exc: ValueError):
        return _error_response(exc)

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        return _error_response(exc)

    def require_service():
        if app.state.service is None:
            raise HTTPException(status_code=503, detail="service unavailable")
        return app.state.service

    @app.get("/healthz")
    async def healthz():
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz():
        if app.state.service is None:
            return JSONResponse({"status": "unready"}, status_code=503)
        return {"status": "ready"}

    @app.post("/api/v1/projects")
    async def create_project(body: ProjectRequest):
        return _result(require_service().create_project(body.slug, body.brief, body.project_id))

    @app.post("/api/v1/projects/{project_id}/jobs")
    async def submit_job(project_id: str, body: JobRequest):
        values = body.model_dump()
        return _result(require_service().submit_job(project_id, **values))

    @app.post("/api/v1/jobs/{job_id}/start")
    async def start_job(job_id: str, body: StartRequest):
        return _result(require_service().start_job(job_id, body.executor, body.executor_input))

    @app.post("/api/v1/jobs/{job_id}/director/intake")
    async def start_director_intake(job_id: str):
        return _result(require_service().start_director_intake(job_id))

    @app.post("/api/v1/jobs/{job_id}/director/animatic-test")
    async def start_director_animatic_test(job_id: str):
        return _result(require_service().start_director_animatic_test(job_id))

    @app.post("/api/v1/jobs/{job_id}/director/approve")
    async def approve_director_artifacts(job_id: str):
        return _result(require_service().approve_director_artifacts(job_id))

    @app.post("/api/v1/jobs/{job_id}/director/publish")
    async def publish_director_artifacts(job_id: str):
        return _result(require_service().publish_director_artifacts(job_id))

    @app.get("/api/v1/jobs/{job_id}")
    async def inspect_job(job_id: str):
        return _result(require_service().inspect_job(job_id))

    @app.post("/api/v1/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str, body: CancelRequest):
        return _result(require_service().cancel_job(job_id, body.grace_seconds))

    @app.get("/api/v1/jobs/{job_id}/artifacts")
    async def artifacts(job_id: str):
        return _result(require_service().list_artifacts(job_id))

    @app.get("/api/v1/jobs/{job_id}/events")
    async def events(job_id: str, request: Request, follow: bool = False):
        service_for_events = require_service()
        try:
            after = int(request.headers.get("last-event-id", "0"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID") from exc
        if after < 0:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID")
        service_for_events.list_events(job_id, after)

        async def stream():
            cursor = after
            last_heartbeat = time.monotonic()
            while True:
                if service_for_events.supervisor is not None:
                    service_for_events.supervisor.tick()
                batch = service_for_events.list_events(job_id, cursor)
                for event in batch:
                    payload = {"id": event.seq, "event": event.event_type,
                               "data": json.dumps(_jsonable(event.payload), sort_keys=True, separators=(",", ":"))}
                    yield "id: {id}\nevent: {event}\ndata: {data}\n\n".format(**payload)
                    cursor = event.seq
                if not follow:
                    return
                inspection = service_for_events.inspect_job(job_id)
                terminal = inspection.status.runtime_state.value in {"succeeded", "failed", "blocked", "cancelled"}
                if terminal:
                    return
                if await request.is_disconnected():
                    return
                if time.monotonic() - last_heartbeat >= 10:
                    yield ": heartbeat\n\n"
                    last_heartbeat = time.monotonic()
                await asyncio.sleep(0.25)

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


__all__ = ["create_app"]
