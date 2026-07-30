import hashlib
import os
import shutil
import tempfile
from pathlib import Path


class UnsafePathError(Exception):
    pass


class ArtifactStore:
    def __init__(self, project_root, job_root):
        self.project_root = Path(project_root).resolve()
        self.job_root = Path(job_root).resolve()

    def _validate(self, root, relative):
        if not isinstance(relative, str) or not relative:
            raise UnsafePathError(relative)
        p = Path(relative)
        if p.is_absolute() or ".." in p.parts:
            raise UnsafePathError(relative)
        candidate = (root / p).resolve()
        try: candidate.relative_to(root)
        except ValueError: raise UnsafePathError(relative)
        return candidate

    def _validate_identifier(self, identifier):
        if not isinstance(identifier, str) or not identifier:
            raise UnsafePathError(identifier)
        path = Path(identifier)
        if path.is_absolute() or identifier in (".", "..") or len(path.parts) != 1 or "\\" in identifier:
            raise UnsafePathError(identifier)
        return identifier

    def validate_project_path(self, project_slug, relative_path):
        project_slug = self._validate_identifier(project_slug)
        return self._validate(self.project_root / project_slug, relative_path)

    def validate_job_path(self, job_id, relative_path):
        job_id = self._validate_identifier(job_id)
        return self._validate(self.job_root / job_id, relative_path)

    def publish(self, staged_file, project_slug, relative_path):
        staged = Path(staged_file)
        try: staged.resolve().relative_to(self.job_root)
        except ValueError: raise UnsafePathError("staged file outside job root")
        if not staged.is_file() or staged.is_symlink(): raise UnsafePathError("staged file must be regular")
        destination = self.validate_project_path(project_slug, relative_path)
        if destination.is_symlink(): raise UnsafePathError("symlink destination")
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with staged.open("rb") as source:
            fd, temporary = tempfile.mkstemp(prefix=".publish-", dir=str(destination.parent))
            try:
                with os.fdopen(fd, "wb") as target:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk: break
                        target.write(chunk); digest.update(chunk); size += len(chunk)
                    target.flush(); os.fsync(target.fileno())
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)
        return "sha256:" + digest.hexdigest(), size
