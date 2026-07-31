import os
from dataclasses import dataclass
from pathlib import Path


class InfrastructureError(Exception):
    pass


def _relative(value, name):
    if not isinstance(value, str) or not value:
        raise InfrastructureError(name + " must be a relative non-parent-traversing path")
    path = Path(value)
    if "\\" in value or path.is_absolute() or any(p == ".." for p in path.parts):
        raise InfrastructureError(name + " must be a relative non-parent-traversing path")
    return value


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8787
    project_root: str = "projects"
    data_root: str = ".mvstudio"
    db_path: str = ".mvstudio/app.sqlite3"
    max_active_jobs: int = 1

    def __post_init__(self):
        if self.host not in ("127.0.0.1", "localhost", "::1"):
            raise InfrastructureError("host must be loopback")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise InfrastructureError("invalid port")
        if isinstance(self.max_active_jobs, bool) or not isinstance(self.max_active_jobs, int) or self.max_active_jobs <= 0:
            raise InfrastructureError("max_active_jobs must be positive")
        for name in ("project_root", "data_root", "db_path"):
            _relative(getattr(self, name), name)

    @classmethod
    def from_mapping(cls, values):
        values = dict(values)
        defaults = cls()
        result = {field: values.get(field, getattr(defaults, field)) for field in cls.__dataclass_fields__}
        for field in ("port", "max_active_jobs"):
            if isinstance(result[field], str):
                try:
                    result[field] = int(result[field])
                except ValueError as exc:
                    raise InfrastructureError("invalid " + field) from exc
        return cls(**result)

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        names = {"host": "MV_HOST", "port": "MV_PORT", "project_root": "MV_PROJECT_ROOT",
                 "data_root": "MV_DATA_ROOT", "db_path": "MV_DB_PATH", "max_active_jobs": "MV_MAX_ACTIVE_JOBS"}
        return cls.from_mapping({field: env[name] for field, name in names.items() if name in env})

    load = from_env
