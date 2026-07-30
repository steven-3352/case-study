from pathlib import Path

from mv_platform.application.service import ApplicationService
from mv_platform.config import Settings
from mv_platform.infrastructure.database import Database


def build_service(workspace_root, settings=None, with_supervisor=True):
    root = Path(workspace_root).absolute()
    configured = settings if isinstance(settings, Settings) else Settings.from_mapping(settings or {})
    database = Database(root / configured.db_path)
    supervisor = None
    if with_supervisor:
        from mv_platform.supervisor import JobSupervisor
        supervisor = JobSupervisor(database, root / configured.data_root / "jobs", configured.max_active_jobs)
    service = ApplicationService(configured, database, supervisor=supervisor, workspace_root=root)
    service.initialize()
    return service
