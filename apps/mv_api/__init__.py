import asyncio
import json
import logging
import os
import sys
import threading
import time
import tempfile
import traceback
from pathlib import Path
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from contextvars import ContextVar

from mv_platform.application.service import (
    ApplicationBlocked, ApplicationConflict, ApplicationError, ApplicationNotFound,
)
from mv_platform.application.error_logs import ErrorLogStore
from apps.runtime import build_service, load_runtime_environment, default_workspace_root
from apps.mv_api.auth import AuthStore, RegistrationError, LoginError
from apps.mv_api.registry import UserServiceRegistry


logger = logging.getLogger(__name__)

# Per-request user context, set by the auth middleware in multi-user mode.
# require_service()/tick_service()/record_error() resolve from these so the
# ~66 existing call sites need no change.
_current_service: ContextVar = ContextVar("current_service", default=None)
_current_error_logs: ContextVar = ContextVar("current_error_logs", default=None)
_current_user_id: ContextVar = ContextVar("current_user_id", default=None)

# Session cookie name + attributes. httponly + samesite=lax; not "secure" so it
# works over plain-HTTP IP access (nginx terminates on port 80, no TLS yet).
_SESSION_COOKIE = "mv_session"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectRequest(StrictModel):
    slug: str
    brief: Mapping[str, Any]
    project_id: Optional[str] = None


class RegisterRequest(StrictModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)
    invite_code: str = Field(default="", max_length=128)


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


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


class MaterializeRequest(StrictModel):
    confirm_billing: bool = False


class CharacterAnalyzeRequest(StrictModel):
    messages: list = []


class CharacterGenerateRequest(StrictModel):
    characters: list = []


class DeleteProjectRequest(StrictModel):
    confirmation_slug: str


class ProviderSettingsRequest(StrictModel):
    base_url: str = ""
    api_key: str = ""
    model: str = ""


class PathSettingsRequest(StrictModel):
    workspace_root: str
    media_binary_path: str = Field(default="", alias="ff" + "mpeg_path")
    probe_binary_path: str = Field(default="", alias="ff" + "probe_path")
    whisper_model_path: str = ""


class RuntimeSettingsRequest(StrictModel):
    paths: PathSettingsRequest
    llm: ProviderSettingsRequest
    image: ProviderSettingsRequest
    video: ProviderSettingsRequest


class PromptSettingsRequest(StrictModel):
    prompts: dict[str, str]


class WorkflowDecisionRequest(StrictModel):
    action: str
    note: str = Field(default="", max_length=8000)


class DisplayContentRequest(StrictModel):
    fields: dict[str, str]


class CharacterAssetRemoveRequest(StrictModel):
    relative_path: str = Field(min_length=1, max_length=1000)
    confirmation_name: str = Field(min_length=1, max_length=500)


class CharacterAssetRestoreRequest(StrictModel):
    relative_path: str = Field(min_length=1, max_length=1000)


class ShotBackgroundRequest(StrictModel):
    relative_path: str = Field(min_length=1, max_length=1000)


class GenerateShotBackgroundRequest(StrictModel):
    en_prompt: Optional[str] = Field(default=None, max_length=10000)


class GenerateShotKeyframeRequest(StrictModel):
    en_prompt: Optional[str] = Field(default=None, max_length=10000)


class ShotKeyframeSelectionRequest(StrictModel):
    relative_path: str = Field(min_length=1, max_length=1000)


class ShotVideoGenerateRequest(StrictModel):
    duration: int = Field(default=5, ge=1, le=60)


class ShotVideoSelectionRequest(StrictModel):
    path: str = Field(min_length=1, max_length=1000)


class SceneGroupUpdateRequest(StrictModel):
    name: Optional[str] = Field(default=None, max_length=40)
    shot_ids: Optional[list[str]] = None


class SceneGroupMergeRequest(StrictModel):
    source_ids: list[str]
    target_name: str = Field(default="", max_length=40)


class ScenePlanningSuggestRequest(StrictModel):
    system_prompt: Optional[str] = None
    task_prompt: Optional[str] = None


class ScenePlanningUpdateRequest(StrictModel):
    action: str
    groups: Optional[list[dict]] = None
    system_prompt: Optional[str] = None
    task_prompt: Optional[str] = None


class SelectMasterRequest(StrictModel):
    candidate_id: str


class BackgroundOverrideRequest(StrictModel):
    override_path: Optional[str] = None


class FrontendErrorRequest(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    path: str = Field(default="", max_length=500)
    method: str = Field(default="", max_length=12)
    status: int = Field(default=0, ge=0, le=599)
    project_id: str = Field(default="", max_length=100)
    job_id: str = Field(default="", max_length=100)
    user_agent: str = Field(default="", max_length=500)


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
    public_details = {
        "invalid job request": "任务参数无效，请检查输入引用",
        "another task is already running": "已有任务正在运行，请等待完成后重试",
        "idempotency key conflict": "检测到重复任务，请刷新任务列表",
        "project deletion confirmation does not match": "项目删除确认不匹配",
        "running jobs must finish before restart": "有任务正在运行，完成后才能重启",
        "asset upload is empty": "所选文件为空，请重新选择素材文件夹",
        "asset upload is too large": "单个素材超过 1GB，暂时无法导入",
        "keyframe upload is too large": "组合首帧超过 40MB，请压缩后重新上传",
        "keyframe upload is empty": "组合首帧文件为空，请重新选择",
        "reference image is too large": "参考图片超过 40MB，请压缩后重新上传",
        "reference image is invalid": "参考图片无法读取，请选择有效的 PNG、JPG 或 WebP 图片",
        "reference image extension does not match content": "参考图片的扩展名与实际格式不一致",
        "reference image dimensions are unsupported": "参考图片尺寸无效或过大",
        "keyframe candidate is invalid": "所选组合首帧不属于当前镜头，请重新选择",
        "shot background path is invalid": "背景参考不属于当前项目，请重新选择",
        "image provider is not configured": "图片服务尚未配置，请先在系统设置中填写地址、密钥和模型",
        "image generation failed": "GPT-image-2 生成失败，请查看错误日志后重试",
        "image provider returned an invalid image": "图片服务返回的内容不是有效图片，本次结果未保存",
        "image prompt translation failed": "生图提示词翻译失败，请查看错误日志后重试",
        "image prompt translation returned an invalid result": "生图提示词翻译结果无效，请重试",
        "shot background is required before keyframe generation": "请先为本镜选择或生成背景，再生成组合首帧",
        "story approval is required before background generation": "请先确认故事框架，再生成分镜背景",
        "storyboard approval is required before keyframe generation": "请先确认分镜方案，再生成组合首帧",
        "lyrics spreadsheet is invalid": "歌词表格无法读取，请检查 xlsx 文件",
        "spreadsheet is too large": "歌词表格过大，暂时无法导入",
        "lyrics spreadsheet is empty": "歌词表格中没有内容",
        "lyrics spreadsheet needs a lyrics column": "歌词表格需要包含“歌词”列",
        "lyrics spreadsheet start time is invalid": "歌词表格的起始时间格式无效",
        "lyrics spreadsheet has no lyrics": "歌词表格中没有识别到歌词",
    }
    if isinstance(exc, ApplicationNotFound):
        status = 404
        detail = "未找到请求的内容"
    elif isinstance(exc, ApplicationConflict):
        status = 409
        detail = public_details.get(str(exc), "当前状态与本次操作冲突")
    elif isinstance(exc, ApplicationBlocked):
        status = 423
        detail = public_details.get(str(exc)) or str(exc)
        payload = {"detail": detail}
        if getattr(exc, "error_stage", ""):
            payload["error_stage"] = exc.error_stage
        if getattr(exc, "error_category", ""):
            payload["error_category"] = exc.error_category
        return JSONResponse(payload, status_code=status)
    else:
        status = 400
        detail = "应用处理失败，请查看错误日志"
    return JSONResponse({"detail": detail}, status_code=status)


def _start_supervisor_driver(app, interval=0.5):
    """Background asyncio task that advances every resident user's supervisor.

    A JobSupervisor only progresses when polled (``tick``). In single-user mode
    the SSE/workflow endpoints tick on demand, but with many independent users a
    job must keep advancing even when its owner is not actively streaming. This
    driver ticks all resident supervisors on a fixed cadence; ticks run in a
    threadpool so blocking work never stalls the event loop.
    """
    async def _run():
        while True:
            await asyncio.sleep(interval)
            registry = app.state.registry
            if registry is None:
                continue
            try:
                await run_in_threadpool(registry.tick_all)
            except Exception:  # pragma: no cover - driver must never die
                logger.exception("supervisor driver tick failed")

    task = asyncio.ensure_future(_run())
    app.state.supervisor_driver = task
    return task


def create_app(service=None, workspace_root=None):
    owned = service is None
    # Multi-user mode is enabled only on a bare server launch: no injected
    # service AND no explicit workspace_root. Tests either pass service=...
    # (single-user) or workspace_root=... (legacy "build one shared service"
    # path) — both stay in single-user mode with auth disabled and behave
    # exactly as before.
    multi_user = service is None and workspace_root is None
    app = FastAPI()
    app.state.service = service
    app.state.error_logs = None
    app.state.auth = None
    app.state.registry = None
    app.state.multi_user = multi_user
    web_root = Path(__file__).with_name("static")
    app.mount("/assets", StaticFiles(directory=web_root), name="web-assets")

    @app.on_event("startup")
    async def startup():
        if multi_user:
            # Server mode: no shared service. Each user gets an isolated service
            # built on demand by the registry; credentials come only from that
            # user's own saved settings (never a shared .env).
            base = default_workspace_root() if workspace_root is None else Path(workspace_root)
            app.state.auth = AuthStore(Path(base) / "auth.sqlite3")
            app.state.registry = UserServiceRegistry(base, build=build_service)
            _start_supervisor_driver(app)
            return
        # Single-user / test mode: one shared service (legacy behaviour).
        if app.state.service is None:
            load_runtime_environment()
            app.state.service = build_service(workspace_root)
        current = app.state.service
        if hasattr(current, "workspace_root") and hasattr(current, "settings"):
            app.state.error_logs = ErrorLogStore(
                current.workspace_root, current.settings.data_root
            )

    @app.on_event("shutdown")
    async def shutdown():
        driver = getattr(app.state, "supervisor_driver", None)
        if driver is not None:
            driver.cancel()
        if app.state.registry is not None:
            app.state.registry.shutdown_all()
        if owned and app.state.service is not None:
            app.state.service.shutdown()

    def record_error(source, event):
        # In multi-user mode use the current user's error log; else the shared one.
        store = _current_error_logs.get() if multi_user else app.state.error_logs
        if store is None:
            return
        try:
            store.append(source, event)
        except OSError:
            logger.exception("Could not write local error log")

    def backend_event(request, exc, response, include_traceback=False):
        event = {
            "event": "api_error",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
        if include_traceback:
            event["traceback"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        record_error("backend", event)

    @app.exception_handler(ApplicationError)
    async def application_error(request: Request, exc: ApplicationError):
        response = _error_response(exc)
        backend_event(request, exc, response, include_traceback=isinstance(exc, ApplicationBlocked))
        return response

    @app.exception_handler(ValueError)
    async def value_error(request: Request, exc: ValueError):
        response = _error_response(exc)
        backend_event(request, exc, response, include_traceback=True)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        response = JSONResponse({"detail": "request validation failed"}, status_code=422)
        backend_event(request, exc, response)
        return response

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled API error: %s", type(exc).__name__, exc_info=exc)
        response = _error_response(exc)
        backend_event(request, exc, response, include_traceback=True)
        return response

    def require_service():
        if multi_user:
            current = _current_service.get()
            if current is None:
                # Middleware only sets this for authenticated requests, so an
                # unset service here means the request was not authenticated.
                raise HTTPException(status_code=401, detail="authentication required")
            return current
        if app.state.service is None:
            raise HTTPException(status_code=503, detail="service unavailable")
        return app.state.service

    def tick_service():
        current = require_service()
        supervisor = getattr(current, "supervisor", None)
        if supervisor is not None and hasattr(supervisor, "tick"):
            supervisor.tick()
        return current

    def restart_process(current):
        time.sleep(0.6)
        current.shutdown()
        os.execv(
            sys.executable,
            [sys.executable, "-m", "uvicorn", *sys.argv[1:]],
        )

    # Paths reachable without a session: health probes, the SPA shell + its
    # static assets (so the login screen can load), and the auth endpoints
    # themselves. Everything else requires a valid session in multi-user mode.
    _PUBLIC_EXACT = {"/", "/healthz", "/readyz", "/favicon.ico",
                     "/api/v1/auth/register", "/api/v1/auth/login",
                     "/api/v1/auth/logout", "/api/v1/auth/me"}

    def _is_public_path(path: str) -> bool:
        if path in _PUBLIC_EXACT:
            return True
        return path.startswith("/assets/")

    if multi_user:
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            path = request.url.path
            auth = app.state.auth
            registry = app.state.registry
            if auth is None or registry is None:
                return JSONResponse({"detail": "service starting"}, status_code=503)

            token = request.cookies.get(_SESSION_COOKIE)
            user_id = auth.verify_session(token) if token else None

            if user_id is None:
                # No valid session. Public paths (login screen, auth API) pass
                # through unauthenticated; everything else is rejected.
                if _is_public_path(path):
                    return await call_next(request)
                return JSONResponse({"detail": "authentication required"}, status_code=401)

            # Authenticated: resolve this user's isolated service and expose it
            # to the handlers via contextvars, then always reset afterwards.
            try:
                entry = await run_in_threadpool(registry.get, user_id)
            except Exception:
                logger.exception("failed to resolve service for user %s", user_id)
                return JSONResponse({"detail": "service unavailable"}, status_code=503)
            tok_s = _current_service.set(entry.service)
            tok_e = _current_error_logs.set(entry.error_logs)
            tok_u = _current_user_id.set(user_id)
            try:
                return await call_next(request)
            finally:
                _current_service.reset(tok_s)
                _current_error_logs.reset(tok_e)
                _current_user_id.reset(tok_u)

    def _set_session_cookie(response, token):
        response.set_cookie(
            _SESSION_COOKIE, token, httponly=True, samesite="lax",
            max_age=30 * 24 * 3600, path="/",
        )

    @app.post("/api/v1/auth/register")
    async def auth_register(body: RegisterRequest):
        if not multi_user or app.state.auth is None:
            raise HTTPException(status_code=404, detail="registration is not enabled")
        try:
            user_id = await run_in_threadpool(
                app.state.auth.register, body.username, body.password, body.invite_code,
            )
        except RegistrationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        token = await run_in_threadpool(app.state.auth.create_session, user_id)
        response = JSONResponse({"username": body.username})
        _set_session_cookie(response, token)
        return response

    @app.post("/api/v1/auth/login")
    async def auth_login(body: LoginRequest):
        if not multi_user or app.state.auth is None:
            raise HTTPException(status_code=404, detail="login is not enabled")
        try:
            user_id = await run_in_threadpool(
                app.state.auth.authenticate, body.username, body.password,
            )
        except LoginError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        token = await run_in_threadpool(app.state.auth.create_session, user_id)
        response = JSONResponse({"username": body.username})
        _set_session_cookie(response, token)
        return response

    @app.post("/api/v1/auth/logout", status_code=204)
    async def auth_logout(request: Request):
        if multi_user and app.state.auth is not None:
            token = request.cookies.get(_SESSION_COOKIE)
            if token:
                await run_in_threadpool(app.state.auth.revoke_session, token)
        response = Response(status_code=204)
        response.delete_cookie(_SESSION_COOKIE, path="/")
        return response

    @app.get("/api/v1/auth/me")
    async def auth_me(request: Request):
        if not multi_user or app.state.auth is None:
            return {"authenticated": False, "multi_user": False}
        token = request.cookies.get(_SESSION_COOKIE)
        user_id = app.state.auth.verify_session(token) if token else None
        if user_id is None:
            return {"authenticated": False, "multi_user": True}
        username = await run_in_threadpool(app.state.auth.get_username, user_id)
        return {"authenticated": True, "multi_user": True, "username": username}

    @app.get("/healthz")
    async def healthz():
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz():
        if multi_user:
            if app.state.auth is None or app.state.registry is None:
                return JSONResponse({"status": "unready"}, status_code=503)
            return {"status": "ready"}
        if app.state.service is None:
            return JSONResponse({"status": "unready"}, status_code=503)
        return {"status": "ready"}

    @app.get("/", include_in_schema=False)
    async def web_app():
        return FileResponse(web_root / "index.html")

    @app.get("/api/v1/projects")
    async def list_projects():
        projects = await run_in_threadpool(require_service().list_projects)
        return [
            {
                "project_id": project.project_id,
                "slug": project.slug,
                "brief_sha256": project.brief_sha256,
                "created_at": project.created_at.isoformat(),
            }
            for project in projects
        ]

    @app.get("/api/v1/settings")
    async def get_settings():
        return _result(await run_in_threadpool(require_service().get_runtime_configuration))

    @app.get("/api/v1/logs")
    async def get_error_log_paths():
        store = _current_error_logs.get() if multi_user else app.state.error_logs
        if store is None:
            raise HTTPException(status_code=503, detail="error logs unavailable")
        return store.paths()

    @app.post("/api/v1/logs/frontend", status_code=204)
    async def record_frontend_error(body: FrontendErrorRequest):
        record_error("frontend", {"event": "frontend_error", **body.model_dump()})
        return Response(status_code=204)

    @app.post("/api/v1/system/restart")
    async def restart_system():
        require_service()

        def _check():
            current = tick_service()
            for project in current.list_projects():
                if any(
                    job.status.runtime_state.value in {"queued", "running"}
                    for job in current.list_project_jobs(project.project_id)
                ):
                    raise ApplicationBlocked("running jobs must finish before restart")
            return current

        current = await run_in_threadpool(_check)
        threading.Thread(target=restart_process, args=(current,), daemon=True).start()
        return {"status": "restarting"}

    @app.put("/api/v1/settings")
    async def update_settings(body: RuntimeSettingsRequest):
        return _result(await run_in_threadpool(
            require_service().update_runtime_configuration, body.model_dump(by_alias=True),
        ))

    @app.post("/api/v1/projects")
    async def create_project(body: ProjectRequest):
        return _result(await run_in_threadpool(
            require_service().create_project, body.slug, body.brief, body.project_id,
        ))

    @app.delete("/api/v1/projects/{project_id}")
    async def delete_project(project_id: str, body: DeleteProjectRequest):
        require_service()  # resolve on the loop so 401/503 map correctly
        return _result(await run_in_threadpool(
            lambda: tick_service().delete_project(project_id, body.confirmation_slug),
        ))

    @app.get("/api/v1/projects/{project_id}/prompts")
    async def get_project_prompts(project_id: str):
        return {"prompts": _result(await run_in_threadpool(
            require_service().get_project_prompts, project_id,
        ))}

    @app.put("/api/v1/projects/{project_id}/prompts")
    async def update_project_prompts(project_id: str, body: PromptSettingsRequest):
        return {"prompts": _result(await run_in_threadpool(
            require_service().update_project_prompts, project_id, body.prompts,
        ))}

    @app.post("/api/v1/projects/{project_id}/display-content/localize")
    async def localize_project_content(project_id: str):
        return _result(await run_in_threadpool(
            require_service().localize_project_content, project_id,
        ))

    @app.put("/api/v1/projects/{project_id}/display-content")
    async def update_project_display_content(project_id: str, body: DisplayContentRequest):
        return _result(await run_in_threadpool(
            require_service().update_project_display_content, project_id, body.fields,
        ))

    @app.get("/api/v1/projects/{project_id}/costs")
    async def get_project_costs(project_id: str):
        return _result(await run_in_threadpool(
            require_service().get_project_costs, project_id,
        ))

    @app.get("/api/v1/projects/{project_id}/workflow")
    async def get_project_workflow(project_id: str):
        require_service()
        return _result(await run_in_threadpool(
            lambda: tick_service().get_project_workflow(project_id),
        ))

    @app.post("/api/v1/projects/{project_id}/workflow/{stage_id}/decision")
    async def record_workflow_decision(
        project_id: str, stage_id: str, body: WorkflowDecisionRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().record_workflow_decision,
            project_id, stage_id, body.action, body.note,
        ))

    @app.post("/api/v1/projects/{project_id}/assets/characters/remove")
    async def remove_project_character_asset(
        project_id: str, body: CharacterAssetRemoveRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().remove_project_character_asset,
            project_id, body.relative_path, body.confirmation_name,
        ))

    @app.post("/api/v1/projects/{project_id}/assets/characters/restore")
    async def restore_project_character_asset(
        project_id: str, body: CharacterAssetRestoreRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().restore_project_character_asset,
            project_id, body.relative_path,
        ))

    @app.put("/api/v1/projects/{project_id}/shots/{shot_id}/background")
    async def bind_shot_background(
        project_id: str, shot_id: str, body: ShotBackgroundRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().bind_shot_background,
            project_id, shot_id, body.relative_path,
        ))

    @app.post("/api/v1/projects/{project_id}/shots/{shot_id}/background/generate", status_code=202)
    async def generate_shot_background(
        project_id: str, shot_id: str,
        body: GenerateShotBackgroundRequest = Body(default_factory=GenerateShotBackgroundRequest),
    ):
        deprecated = (
            f"use /api/v1/projects/{project_id}/scene-groups/{{sg_id}}/backgrounds/generate"
        )
        svc = require_service()
        try:
            result = await run_in_threadpool(
                svc.submit_generate_background_job,
                project_id, shot_id, en_prompt=body.en_prompt or None,
            )
        except ApplicationError as exc:
            err = _error_response(exc)
            err.headers["X-Deprecated"] = deprecated
            return err
        asyncio.ensure_future(run_in_threadpool(svc.run_generate_background_job, result["job_id"]))
        resp = JSONResponse(content=result, status_code=202)
        resp.headers["X-Async"] = "true"
        resp.headers["X-Deprecated"] = deprecated
        return resp

    @app.post("/api/v1/projects/{project_id}/scene-groups/suggest")
    async def suggest_scene_groups(project_id: str):
        return _result(await run_in_threadpool(
            require_service().suggest_and_save_scene_groups, project_id,
        ))

    @app.get("/api/v1/projects/{project_id}/scene-groups")
    async def get_scene_groups(project_id: str):
        return _result(await run_in_threadpool(
            require_service().get_scene_groups, project_id,
        ))

    @app.put("/api/v1/projects/{project_id}/scene-groups/{sg_id}")
    async def update_scene_group(
        project_id: str, sg_id: str, body: SceneGroupUpdateRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().update_scene_group,
            project_id, sg_id, name=body.name, shot_ids=body.shot_ids,
        ))

    @app.post("/api/v1/projects/{project_id}/scene-groups/merge")
    async def merge_scene_groups(project_id: str, body: SceneGroupMergeRequest):
        return _result(await run_in_threadpool(
            require_service().merge_scene_groups,
            project_id, body.source_ids, body.target_name,
        ))

    @app.post("/api/v1/projects/{project_id}/scene-groups/{sg_id}/backgrounds/generate")
    async def generate_scene_group_background(project_id: str, sg_id: str):
        return _result(await run_in_threadpool(
            require_service().generate_scene_group_background, project_id, sg_id,
        ))

    @app.put("/api/v1/projects/{project_id}/scene-groups/{sg_id}/backgrounds/{bg_id}/select")
    async def select_background_master(project_id: str, sg_id: str, bg_id: str):
        return _result(await run_in_threadpool(
            require_service().select_background_master,
            project_id, sg_id, bg_id,
        ))

    # PRD-007B: scene planning routes
    @app.get("/api/v1/projects/{project_id}/scene-planning")
    async def get_scene_planning(project_id: str):
        return _result(await run_in_threadpool(
            require_service().get_scene_planning, project_id,
        ))

    @app.post("/api/v1/projects/{project_id}/scene-planning/suggest")
    async def suggest_scene_planning(
        project_id: str,
        body: "ScenePlanningSuggestRequest" = Body(default_factory=lambda: ScenePlanningSuggestRequest()),
    ):
        return _result(await run_in_threadpool(
            require_service().suggest_scene_groups_llm,
            project_id, body.system_prompt, body.task_prompt,
        ))

    @app.put("/api/v1/projects/{project_id}/scene-planning")
    async def update_scene_planning(project_id: str, body: "ScenePlanningUpdateRequest"):
        return _result(await run_in_threadpool(
            require_service().update_scene_planning,
            project_id, body.model_dump(exclude_none=False),
        ))

    @app.post("/api/v1/projects/{project_id}/scene-planning/approve")
    async def approve_scene_planning(project_id: str):
        return _result(await run_in_threadpool(
            require_service().approve_scene_planning, project_id,
        ))

    @app.post("/api/v1/projects/{project_id}/groups/{group_id}/background/generate")
    async def generate_group_background(project_id: str, group_id: str):
        return _result(await run_in_threadpool(
            require_service().submit_generate_group_background_job, project_id, group_id,
        ))

    @app.post("/api/v1/projects/{project_id}/groups/{group_id}/background/select")
    async def select_group_background_master(
        project_id: str, group_id: str, body: "SelectMasterRequest",
    ):
        return _result(await run_in_threadpool(
            require_service().select_background_master,
            project_id, group_id, body.candidate_id,
        ))

    @app.put("/api/v1/projects/{project_id}/shots/{shot_id}/background-override")
    async def set_shot_background_override(
        project_id: str, shot_id: str, body: "BackgroundOverrideRequest",
    ):
        return _result(await run_in_threadpool(
            require_service().set_shot_background_override,
            project_id, shot_id, body.override_path,
        ))

    @app.post("/api/v1/projects/{project_id}/shots/{shot_id}/keyframes")
    async def import_shot_keyframe(
        project_id: str, shot_id: str, request: Request, filename: str,
    ):
        size = 0
        temporary = tempfile.NamedTemporaryFile(prefix="mvstudio-keyframe-", delete=False)
        temporary_path = Path(temporary.name)
        try:
            with temporary:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 40 * 1024 * 1024:
                        raise ApplicationConflict("keyframe upload is too large")
                    temporary.write(chunk)
            if size == 0:
                raise ApplicationConflict("keyframe upload is empty")
            return _result(await run_in_threadpool(
                require_service().import_shot_keyframe,
                project_id, shot_id, temporary_path, filename,
            ))
        finally:
            try:
                temporary_path.unlink()
            except OSError:
                pass

    @app.post("/api/v1/projects/{project_id}/shots/{shot_id}/keyframes/generate", status_code=202)
    async def generate_shot_keyframe(
        project_id: str, shot_id: str,
        body: GenerateShotKeyframeRequest = Body(default_factory=GenerateShotKeyframeRequest),
    ):
        svc = require_service()
        try:
            result = await run_in_threadpool(
                svc.submit_generate_keyframe_job,
                project_id, shot_id, en_prompt=body.en_prompt or None,
            )
        except ApplicationError as exc:
            return _error_response(exc)
        asyncio.ensure_future(run_in_threadpool(svc.run_generate_keyframe_job, result["job_id"]))
        return JSONResponse(content=result, status_code=202)

    @app.put("/api/v1/projects/{project_id}/shots/{shot_id}/keyframes/selection")
    async def select_shot_keyframe(
        project_id: str, shot_id: str, body: ShotKeyframeSelectionRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().select_shot_keyframe,
            project_id, shot_id, body.relative_path,
        ))

    @app.delete("/api/v1/projects/{project_id}/shots/{shot_id}/keyframes")
    async def delete_shot_keyframe(project_id: str, shot_id: str, path: str):
        return _result(await run_in_threadpool(
            require_service().delete_shot_keyframe, project_id, shot_id, path,
        ))

    class ShotSkippedRequest(StrictModel):
        skipped: bool

    @app.put("/api/v1/projects/{project_id}/shots/{shot_id}/skipped")
    async def set_shot_skipped(project_id: str, shot_id: str, body: ShotSkippedRequest):
        return _result(await run_in_threadpool(
            require_service().set_shot_skipped, project_id, shot_id, body.skipped,
        ))

    @app.post("/api/v1/projects/{project_id}/shots/{shot_id}/video/generate", status_code=202)
    async def generate_shot_video(
        project_id: str, shot_id: str, body: ShotVideoGenerateRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().generate_shot_video, project_id, shot_id, body.duration,
        ))

    @app.put("/api/v1/projects/{project_id}/shots/{shot_id}/videos/selection")
    async def select_shot_video(
        project_id: str, shot_id: str, body: ShotVideoSelectionRequest,
    ):
        return _result(await run_in_threadpool(
            require_service().select_shot_video,
            project_id, shot_id, body.path,
        ))

    @app.post("/api/v1/settings/video-provider/ping")
    async def ping_video_provider():
        return await run_in_threadpool(require_service().ping_video_provider)

    @app.get("/api/v1/projects/{project_id}/files")
    async def get_project_file(project_id: str, path: str):
        resolved = await run_in_threadpool(require_service().get_project_file, project_id, path)
        return FileResponse(resolved)

    @app.post("/api/v1/projects/{project_id}/jobs")
    async def submit_job(project_id: str, body: JobRequest):
        values = body.model_dump()
        return _result(await run_in_threadpool(
            require_service().submit_job, project_id, **values,
        ))

    @app.post("/api/v1/projects/{project_id}/assets")
    async def import_project_asset(
        project_id: str, request: Request, filename: str, kind: str = "",
    ):
        size = 0
        temporary = tempfile.NamedTemporaryFile(prefix="mvstudio-upload-", delete=False)
        temporary_path = Path(temporary.name)
        try:
            with temporary:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 1024 * 1024 * 1024:
                        raise ApplicationConflict("asset upload is too large")
                    temporary.write(chunk)
            if size == 0:
                raise ApplicationConflict("asset upload is empty")
            current = require_service()
            if kind:
                return _result(await run_in_threadpool(
                    current.import_project_asset,
                    project_id, temporary_path, filename, kind_hint=kind,
                ))
            return _result(await run_in_threadpool(
                current.import_project_asset,
                project_id, temporary_path, filename,
            ))
        finally:
            try:
                temporary_path.unlink()
            except OSError:
                pass

    @app.get("/api/v1/projects/{project_id}/jobs")
    async def list_project_jobs(project_id: str):
        require_service()
        jobs = await run_in_threadpool(lambda: tick_service().list_project_jobs(project_id))
        return [_result(job) for job in jobs]

    @app.post("/api/v1/jobs/{job_id}/start")
    async def start_job(job_id: str, body: StartRequest):
        return _result(await run_in_threadpool(
            require_service().start_job, job_id, body.executor, body.executor_input,
        ))

    @app.post("/api/v1/jobs/{job_id}/director/intake")
    async def start_director_intake(job_id: str):
        return _result(await run_in_threadpool(
            require_service().start_director_intake, job_id,
        ))

    @app.post("/api/v1/jobs/{job_id}/director/animatic-test")
    async def start_director_animatic_test(job_id: str):
        return _result(await run_in_threadpool(
            require_service().start_director_animatic_test, job_id,
        ))

    @app.post("/api/v1/jobs/{job_id}/director/animatic-offline-test")
    async def start_director_animatic_offline_test(job_id: str):
        return _result(await run_in_threadpool(
            require_service().start_director_animatic_offline_test, job_id,
        ))

    @app.post("/api/v1/jobs/{job_id}/director/mvp-test")
    async def run_director_mvp_test(job_id: str):
        service = require_service()
        return _result(await run_in_threadpool(service.run_director_mvp_test, job_id))

    @app.post("/api/v1/jobs/{job_id}/director/plan")
    async def run_director_plan(job_id: str):
        service = require_service()
        return _result(await run_in_threadpool(service.run_director_plan, job_id))

    @app.post("/api/v1/jobs/{job_id}/director/plan/resume")
    async def resume_director_plan(job_id: str):
        service = require_service()
        return _result(await run_in_threadpool(service.resume_director_plan, job_id))

    @app.post("/api/v1/jobs/{job_id}/director/approve")
    async def approve_director_artifacts(job_id: str):
        return _result(await run_in_threadpool(
            require_service().approve_director_artifacts, job_id,
        ))

    @app.post("/api/v1/jobs/{job_id}/director/publish")
    async def publish_director_artifacts(job_id: str, preserve_edits: bool = False):
        return _result(await run_in_threadpool(
            require_service().publish_director_artifacts,
            job_id, supersede=preserve_edits, preserve_user_edits=preserve_edits,
        ))

    @app.post("/api/v1/jobs/{job_id}/seedance/shot")
    async def start_seedance_shot(job_id: str):
        return _result(await run_in_threadpool(
            require_service().start_seedance_shot, job_id,
        ))

    @app.get("/api/v1/jobs/{job_id}")
    async def inspect_job(job_id: str):
        require_service()
        return _result(await run_in_threadpool(lambda: tick_service().inspect_job(job_id)))

    @app.get("/api/v1/jobs/{job_id}/inspect")
    async def inspect_job_alias(job_id: str):
        require_service()
        return _result(await run_in_threadpool(lambda: tick_service().inspect_job(job_id)))

    @app.post("/api/v1/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str, body: CancelRequest):
        return _result(await run_in_threadpool(
            require_service().cancel_job, job_id, body.grace_seconds,
        ))

    @app.post("/api/v1/jobs/{job_id}/materialize")
    async def materialize_job(job_id: str, body: MaterializeRequest):
        if not body.confirm_billing:
            return JSONResponse({"error": "billing_confirmation_required"}, status_code=422)
        svc = require_service()
        job = await run_in_threadpool(svc.inspect_job, job_id)
        project_id = job.job_spec.project_id
        await svc._materialize_job(project_id, job_id, body.confirm_billing)
        pending = await run_in_threadpool(svc.pending_materialization, project_id)
        return {"status": "ok", "pending_materialization": _jsonable(pending)}

    @app.post("/api/v1/projects/{project_id}/transcribe")
    async def transcribe_project(project_id: str):
        return _result(await run_in_threadpool(
            require_service().transcribe_audio_for_project, project_id,
        ))

    @app.post("/api/v1/projects/{project_id}/generate-characters")
    async def generate_project_characters(project_id: str):
        return _result(await run_in_threadpool(
            require_service().generate_characters_for_project, project_id,
        ))

    @app.get("/api/v1/projects/{project_id}/material-status")
    async def get_material_status(project_id: str):
        return _result(await run_in_threadpool(
            require_service().get_material_status, project_id,
        ))

    @app.post("/api/v1/projects/{project_id}/fill/characters/analyze")
    async def analyze_characters(project_id: str, body: CharacterAnalyzeRequest):
        return _result(await run_in_threadpool(
            require_service().analyze_characters_from_lyrics, project_id, body.messages,
        ))

    @app.post("/api/v1/projects/{project_id}/fill/characters/generate")
    async def generate_character_portraits(project_id: str, body: CharacterGenerateRequest):
        return _result(await run_in_threadpool(
            require_service().generate_character_portraits_from_list,
            project_id,
            body.characters,
        ))

    @app.get("/api/v1/jobs/{job_id}/artifacts")
    async def artifacts(job_id: str):
        return _result(await run_in_threadpool(require_service().list_artifacts, job_id))

    @app.get("/api/v1/jobs/{job_id}/events")
    async def events(job_id: str, request: Request, follow: bool = False):
        service_for_events = require_service()
        try:
            after = int(request.headers.get("last-event-id", "0"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID") from exc
        if after < 0:
            raise HTTPException(status_code=400, detail="invalid Last-Event-ID")
        await run_in_threadpool(service_for_events.list_events, job_id, after)

        async def stream():
            cursor = after
            last_heartbeat = time.monotonic()
            while True:
                if service_for_events.supervisor is not None:
                    await run_in_threadpool(service_for_events.supervisor.tick)
                batch = await run_in_threadpool(service_for_events.list_events, job_id, cursor)
                for event in batch:
                    payload = {"id": event.seq, "event": event.event_type,
                               "data": json.dumps(_jsonable(event.payload), sort_keys=True, separators=(",", ":"))}
                    yield "id: {id}\nevent: {event}\ndata: {data}\n\n".format(**payload)
                    cursor = event.seq
                if not follow:
                    return
                inspection = await run_in_threadpool(service_for_events.inspect_job, job_id)
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
