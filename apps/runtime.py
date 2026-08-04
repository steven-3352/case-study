import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from mv_platform.application.service import ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure.database import Database


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE_ROOT = SOURCE_ROOT / "src"

# Source checkouts must load the packaged executors without requiring users to
# understand or run an editable Python installation first.
if str(SOURCE_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_PACKAGE_ROOT))


def load_runtime_environment(path=None):
    env_path = Path(path) if path is not None else SOURCE_ROOT / ".env"
    return load_dotenv(env_path, override=False)


def default_workspace_root(environ=None):
    env = os.environ if environ is None else environ
    configured = env.get("MV_WORKSPACE_ROOT")
    if configured:
        return Path(configured).expanduser().absolute()
    pointer = workspace_pointer_path(env)
    if pointer.is_file() and not pointer.is_symlink():
        try:
            saved = json.loads(pointer.read_text(encoding="utf-8")).get("workspace_root", "")
            if saved and Path(saved).expanduser().is_absolute():
                return Path(saved).expanduser().absolute()
        except (OSError, ValueError, json.JSONDecodeError, AttributeError):
            pass
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MVStudio"
    if os.name == "nt":
        base = Path(env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "MVStudio"
    base = Path(env.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "mvstudio"


def workspace_pointer_path(environ=None):
    env = os.environ if environ is None else environ
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "MVStudio"
    elif os.name == "nt":
        base = Path(env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MVStudio"
    else:
        base = Path(env.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "mvstudio"
    return base / "workspace.json"


def build_service(workspace_root=None, settings=None, with_supervisor=True,
                  pointer_path=None, read_process_env=True):
    root = Path(workspace_root).expanduser().absolute() if workspace_root else default_workspace_root()
    configured = settings if isinstance(settings, Settings) else Settings.from_mapping(settings or {})
    database = Database(root / configured.db_path)
    supervisor = None
    if with_supervisor:
        from mv_platform.supervisor import JobSupervisor
        supervisor = JobSupervisor(database, root / configured.data_root / "jobs", configured.max_active_jobs)
    # In multi-user mode the registry passes a per-user pointer path so a user
    # cannot repoint a shared workspace; default keeps single-user behaviour.
    pointer = pointer_path if pointer_path is not None else workspace_pointer_path()
    service = ApplicationService(
        configured,
        database,
        supervisor=supervisor,
        workspace_root=root,
        source_root=SOURCE_ROOT,
        workspace_pointer_path=pointer,
        read_process_env=read_process_env,
    )
    service.initialize()
    return service
