from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "sync-config.yml"


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        return ROOT / path
    return path


def load_sync_projects() -> list[dict]:
    if not CONFIG_FILE.exists():
        return []

    with CONFIG_FILE.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    projects = []
    for entry in config.get("projects", []):
        if not entry.get("enabled", True):
            continue
        upload_source = entry.get("upload_source")
        remote_prefix = entry.get("remote_prefix")
        download_target = entry.get("download_target")
        if not upload_source or not remote_prefix or not download_target:
            continue

        projects.append({
            "name": entry.get("name") or remote_prefix,
            "upload_source": _resolve_path(upload_source),
            "remote_prefix": remote_prefix.replace("\\", "/"),
            "download_target": _resolve_path(download_target),
        })

    return projects
