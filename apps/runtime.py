import os
import sys
from pathlib import Path

from mv_platform.application.service import ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure.database import Database


SOURCE_ROOT = Path(__file__).resolve().parents[1]


def default_workspace_root(environ=None):
    env = os.environ if environ is None else environ
    configured = env.get("MV_WORKSPACE_ROOT")
    if configured:
        return Path(configured).expanduser().absolute()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MVStudio"
    if os.name == "nt":
        base = Path(env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "MVStudio"
    base = Path(env.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "mvstudio"


def build_service(workspace_root=None, settings=None, with_supervisor=True):
    root = Path(workspace_root).expanduser().absolute() if workspace_root else default_workspace_root()
    configured = settings if isinstance(settings, Settings) else Settings.from_mapping(settings or {})
    database = Database(root / configured.db_path)
    supervisor = None
    if with_supervisor:
        from mv_platform.supervisor import JobSupervisor
        supervisor = JobSupervisor(database, root / configured.data_root / "jobs", configured.max_active_jobs)
    service = ApplicationService(
        configured,
        database,
        supervisor=supervisor,
        workspace_root=root,
        source_root=SOURCE_ROOT,
    )
    service.initialize()
    return service
