import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))

from paratranz_api import ParaTranzClient

from src.ie_manuals import PROJECT_ROOT

def _get_client(token: str):
    try:
        return ParaTranzClient(token)
    except TypeError:
        return ParaTranzClient(token=token)


def _get_project_files(client, project_id: str) -> list[dict]:
    return client.get_files(project_id)


def _get_translation_segments(client, project_id: str, file_id: int) -> list[dict]:
    return client.get_file_translation(project_id, file_id)


def _extract_translation_map(segments: list[dict]) -> dict[str, str] | None:
    if not isinstance(segments, list):
        return None

    translation_map: dict[str, str] = {}
    for item in segments:
        if not isinstance(item, dict):
            continue

        key = item.get("key") or item.get("name") or item.get("id")
        translation = item.get("translation")
        if isinstance(translation, dict):
            translation = translation.get("text") or translation.get("translated") or translation.get("translation")
        if isinstance(translation, str) and key is not None:
            translation_map[str(key)] = translation
            continue

        if item.get("data") and isinstance(item["data"], dict):
            translation = item["data"].get("translation")
            if isinstance(translation, str) and key is not None:
                translation_map[str(key)] = translation
                continue

    return translation_map if translation_map else None


def _write_translation_file(output_path: Path, content):
    if output_path.exists() and output_path.is_dir():
        shutil.rmtree(output_path)
    if output_path.parent.exists() and not output_path.parent.is_dir():
        output_path.parent.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(content, ensure_ascii=False, indent=4))


def main():
    token = os.environ.get("PARA_TOKEN") or os.environ.get("PARATRANZ_TOKEN")
    project_id = os.environ.get("PARA_PROJECT_ID")
    locale = "zh_cn"
    remote_prefix = "immersiveengineering/1.21/manual/en_us/"
    target_root = PROJECT_ROOT / locale

    if not token or not project_id:
        print("环境变量未配置：需要 PARA_TOKEN 和 PARA_PROJECT_ID")
        raise SystemExit(2)

    client = _get_client(token)
    files = _get_project_files(client, project_id)
    if not files:
        print("未找到任何远程文件。")
        return

    saved_files = 0
    for file_info in files:
        remote_path = (file_info.get("path") or file_info.get("name") or "").replace("\\", "/")
        remote_prefix = remote_prefix.replace("\\", "/")
        if not remote_prefix.endswith("/"):
            remote_prefix += "/"
        if not remote_path or not remote_path.startswith(remote_prefix):
            continue

        file_id_value = file_info.get("id")
        if file_id_value is None:
            print(f"跳过远程文件 {remote_path}：缺少 id")
            continue

        try:
            file_id = int(str(file_id_value))
        except ValueError:
            print(f"跳过远程文件 {remote_path}：id 无效 {file_id_value!r}")
            continue

        relative_part = remote_path[len(remote_prefix):].strip("/")
        if not relative_part:
            continue
        relative_path = Path(relative_part)
        if (
            len(relative_path.parts) >= 2
            and relative_path.parts[-1] == relative_path.parts[-2]
            and relative_path.suffix == Path(relative_path.parts[-2]).suffix
        ):
            relative_path = Path(relative_path.parts[-1])
        output_path = target_root / relative_path

        segments = _get_translation_segments(client, project_id, file_id)
        translation_map = _extract_translation_map(segments)
        if translation_map is None:
            print(f"无法解析文件 {remote_path} 的翻译内容，保存原始返回数据。")
            _write_translation_file(output_path, segments)
        else:
            _write_translation_file(output_path, translation_map)
            print(f"已写入翻译文件：{output_path}")
        saved_files += 1

    print(f"完成拉取：{saved_files} 个文件写入 {target_root}")


if __name__ == "__main__":
    main()