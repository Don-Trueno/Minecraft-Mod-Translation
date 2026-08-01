import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))

from paratranz_api import ParaTranzClient
from sync_config import load_sync_projects

from src.ie_manuals import PROJECT_ROOT


def _get_client(token: str):
    try:
        return ParaTranzClient(token)
    except TypeError:
        return ParaTranzClient(token=token)


def _get_existing_files(client, project_id: str) -> dict:
    for name in ("list_files", "get_files", "get_project_files", "list_project_files"):
        if hasattr(client, name):
            func = getattr(client, name)
            files = func(project_id)
            if isinstance(files, list):
                return {f.get("path") or f.get("name"): f for f in files}
            if isinstance(files, dict):
                return files
    return {}


def _create_file(client, project_id: str, remote_path: str, local_file: Path):
    for name in ("create_file", "upload_file", "add_file"):
        if hasattr(client, name):
            func = getattr(client, name)
            try:
                return func(project_id, local_file, remote_path)
            except TypeError:
                return func(project_id, str(local_file), remote_path)
    raise RuntimeError("Client has no create/upload method")


def _update_file(client, project_id: str, file_id: str, local_file: Path):
    for name in ("update_file", "edit_file"):
        if hasattr(client, name):
            func = getattr(client, name)
            try:
                return func(project_id, file_id, local_file)
            except TypeError:
                return func(project_id, file_id, str(local_file))
    raise RuntimeError("Client has no update method")


def upload_file(client, project_id, remote_path, local_file, existing_files):
    file_name = local_file.name
    if remote_path and not remote_path.endswith("/"):
        remote_path = remote_path + "/"
    full_path = f"{remote_path}{file_name}" if remote_path else file_name
    existing_file = existing_files.get(full_path)

    if existing_file:
        _update_file(client, project_id, existing_file["id"], local_file)
        print(f"文件已更新：{full_path}")
        return

    _create_file(client, project_id, remote_path, local_file)
    print(f"已创建远端文件：{remote_path}{file_name}")


def _get_sync_projects():
    projects = load_sync_projects()
    if projects:
        return projects

    return []


def main():
    token = os.environ.get("PARA_TOKEN") or os.environ.get("PARATRANZ_TOKEN")
    project_id = os.environ.get("PARA_PROJECT_ID")

    if not token or not project_id:
        print("环境变量未配置：需要 PARA_TOKEN 和 PARA_PROJECT_ID")
        sys.exit(2)

    client = _get_client(token)
    existing = _get_existing_files(client, project_id)
    projects = _get_sync_projects()

    for project in projects:
        source_root = Path(project["upload_source"])
        if not source_root.exists():
            print(f"源目录不存在：{source_root}，跳过 {project.get('name')}")
            continue

        if source_root.is_file():
            files = [source_root]
        else:
            files = list(source_root.rglob("*.json"))

        if not files:
            print(f"未找到任何源 JSON 文件，跳过 {project.get('name')}")
            continue

        print(f"上传项目：{project.get('name')} -> {project.get('remote_prefix')}")
        for f in files:
            upload_file(client, project_id, project["remote_prefix"], f, existing)


if __name__ == "__main__":
    main()
