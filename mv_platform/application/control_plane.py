import json
import os
import shutil
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


class ControlPlaneError(ValueError):
    pass


PROVIDER_FIELDS = {
    "llm": ("base_url", "api_key", "model"),
    "image": ("base_url", "api_key", "model"),
    "video": ("base_url", "api_key", "model"),
}
PATH_FIELDS = ("ffmpeg_path", "ffprobe_path", "whisper_model_path")
SECRET_FIELDS = {"llm.api_key", "image.api_key", "video.api_key"}
ENV_MAP = {
    "llm.base_url": "LLM_BASE_URL", "llm.api_key": "LLM_API_KEY", "llm.model": "LLM_MODEL",
    "image.base_url": "GPT_IMAGE_BASE_URL", "image.api_key": "GPT_IMAGE_API_KEY",
    "image.model": "GPT_IMAGE_MODEL",
    "video.base_url": "SEEDANCE_BASE_URL", "video.api_key": "SEEDANCE_API_KEY",
    "video.model": "SEEDANCE_MODEL",
    "paths.ffmpeg_path": "MVSTUDIO_FFMPEG_PATH",
    "paths.ffprobe_path": "MVSTUDIO_FFPROBE_PATH",
    "paths.whisper_model_path": "MVSTUDIO_WHISPER_MODEL",
}


def default_runtime_config(workspace_root):
    value = {
        "paths": {
            "workspace_root": str(Path(workspace_root)),
            "ffmpeg_path": shutil.which("ffmpeg") or "",
            "ffprobe_path": shutil.which("ffprobe") or "",
            "whisper_model_path": "",
        },
        "llm": {"base_url": "", "api_key": "", "model": ""},
        "image": {"base_url": "", "api_key": "", "model": "gpt-image-2"},
        "video": {"base_url": "", "api_key": "", "model": "doubao-seedance-2-0"},
    }
    for dotted, env_name in ENV_MAP.items():
        section, key = dotted.split(".", 1)
        if os.environ.get(env_name):
            value[section][key] = os.environ[env_name]
    return value


def _validate_url(value, label):
    if value == "":
        return value
    parsed = urllib.parse.urlparse(value)
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme not in ({"http", "https"} if loopback else {"https"}):
        raise ControlPlaneError(label + " must use HTTPS or loopback HTTP")
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.netloc:
        raise ControlPlaneError(label + " is invalid")
    return value.rstrip("/")


def _text(value, label, limit=4096):
    if not isinstance(value, str) or "\x00" in value or len(value.encode("utf-8")) > limit:
        raise ControlPlaneError(label + " is invalid")
    return value.strip()


def merge_runtime_config(current, update, workspace_root):
    if not isinstance(update, dict) or set(update) - {"paths", *PROVIDER_FIELDS}:
        raise ControlPlaneError("runtime configuration has unknown sections")
    merged = json.loads(json.dumps(current))
    merged.setdefault("paths", {})["workspace_root"] = str(Path(workspace_root))
    for section, values in update.items():
        if not isinstance(values, dict):
            raise ControlPlaneError(section + " configuration must be an object")
        allowed = set(PATH_FIELDS if section == "paths" else PROVIDER_FIELDS[section])
        if set(values) - allowed:
            raise ControlPlaneError(section + " configuration has unknown fields")
        for key, value in values.items():
            label = section + "." + key
            checked = _text(value, label)
            if key == "base_url":
                checked = _validate_url(checked, label)
            if section == "paths" and checked and not Path(checked).expanduser().is_absolute():
                raise ControlPlaneError(label + " must be an absolute path")
            merged.setdefault(section, {})[key] = checked
    return merged


def read_config(path, workspace_root):
    value = default_runtime_config(workspace_root)
    if Path(path).is_file() and not Path(path).is_symlink():
        try:
            stored = json.loads(Path(path).read_text(encoding="utf-8"))
            if isinstance(stored, dict) and isinstance(stored.get("paths"), dict):
                stored["paths"].pop("workspace_root", None)
            value = merge_runtime_config(value, stored, workspace_root)
        except (OSError, json.JSONDecodeError, ControlPlaneError) as exc:
            raise ControlPlaneError("saved runtime configuration is invalid") from exc
    return value


def write_config(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise ControlPlaneError("runtime configuration path is unsafe")
    descriptor, temporary = tempfile.mkstemp(prefix=".settings-", dir=str(target.parent))
    try:
        if hasattr(os, "fchmod"):  # Unix only; not available on Windows
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1  # fdopen owns the fd now; prevent double-close in finally
            json.dump(value, handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    finally:
        if descriptor != -1:
            # fchmod or earlier step failed before fdopen could take ownership;
            # close the fd explicitly so Windows allows the unlink below (WinError 32).
            try:
                os.close(descriptor)
            except OSError:
                pass
        if os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                pass


def apply_environment(config):
    for dotted, env_name in ENV_MAP.items():
        section, key = dotted.split(".", 1)
        value = config.get(section, {}).get(key, "")
        if value:
            os.environ[env_name] = value
        else:
            os.environ.pop(env_name, None)


def public_config(config):
    result = json.loads(json.dumps(config))
    for dotted in SECRET_FIELDS:
        section, key = dotted.split(".", 1)
        secret = result[section].get(key, "")
        configured = bool(secret)
        result[section][key] = ""
        result[section]["api_key_configured"] = configured
        result[section]["api_key_hint"] = (
            (secret[:3] + "••••" + secret[-4:]) if len(secret) >= 12
            else ("••••" + secret[-4:]) if secret else ""
        )
    for section in PROVIDER_FIELDS:
        provider = config.get(section, {})
        result[section]["ready"] = all(
            bool(provider.get(key)) for key in ("base_url", "api_key", "model")
        )
    result["paths"]["ffmpeg_detected"] = bool(
        config.get("paths", {}).get("ffmpeg_path")
        and Path(config["paths"]["ffmpeg_path"]).is_file()
    )
    result["paths"]["ffprobe_detected"] = bool(
        config.get("paths", {}).get("ffprobe_path")
        and Path(config["paths"]["ffprobe_path"]).is_file()
    )
    result["paths"]["whisper_configured"] = bool(
        config.get("paths", {}).get("whisper_model_path")
    )
    result["pricing"] = {
        "currency": "CNY", "image_per_item": 0.5, "video_per_second": 0.6,
        "llm_input_per_million": 5.0, "llm_output_per_million": 30.0,
        "llm_cache_read_per_million": 0.5, "llm_multiplier": 0.04,
    }
    result["updated_at"] = datetime.now(timezone.utc).isoformat()
    return result
