# -*- coding=utf-8 -*-
"""适用于沉浸工程系列手册的转换器"""

import json
import sys
from pathlib import Path
from core.tagprocess import preprocess, postprocess

P = Path(__file__).resolve().parents[1]

TAG_RULES = [
    # <link;xxx;Text>
    # <link;xxx;Text;xxx>
    {"required_prefix": "link", "preserved_index": 2},
    # <config;b;xxx;Text1;Text2>
    {"required_prefix": "config;b", "preserved_index": [3, 4]},
]

MOD_NAMESPACE_ID = "immersiveengineering"
MOD_VERSION = 1.21

SOURCE_ROOT = P / f"sources/{MOD_NAMESPACE_ID}/{MOD_VERSION}/manual"
PROJECT_ROOT = P / f"projects/{MOD_NAMESPACE_ID}/{MOD_VERSION}/manual"
TAG_PATH = P / f"tags/{MOD_NAMESPACE_ID}_{MOD_VERSION}.json"

tags = {}


def collect_paths(source_root: Path, filetype: str) -> list[Path]:
    """在源文件根目录寻找指定后缀名的文件，返回文件路径的列表。"""
    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(
            f"Namespace directory does not exist: {source_root}")
    return sorted(source_root.rglob(f"*.{filetype}"))


def process_file(
    source_path: Path,
    project_path: Path
) -> None:
    """将源文件按行读取，转换标签，然后输出到目标位置的JSON文件中。"""

    global tags

    project_path.parent.mkdir(parents=True, exist_ok=True)
    lines = source_path.read_text(encoding="utf-8").splitlines()
    key_prefix = "manual." + source_path.stem

    output = {}

    for index, line in enumerate(lines):
        line2, tag = preprocess(line, TAG_RULES)
        output.update({f"{key_prefix}.line{index}": line2})
        for k in tag.keys():
            tags.update({f"{key_prefix}.line{index}.{k}": tag[k]})
    project_path.write_text(json.dumps(
        output, ensure_ascii=False, indent=4), encoding="utf-8")


TRANSLATION_ROOT = P / f"translation/{MOD_NAMESPACE_ID}/{MOD_VERSION}/manual"


def load_tags(tag_path: Path) -> dict[str, str]:
    if not tag_path.exists():
        raise SystemExit(f"Tag file does not exist: {tag_path}")
    return json.loads(tag_path.read_text(encoding="utf-8"))


def get_line_tags(line_key: str, tags: dict[str, str]) -> dict[str, str]:
    prefix = f"{line_key}."
    return {k[len(prefix):]: v for k, v in tags.items() if k.startswith(prefix)}


def generate_translated_line(line_key: str, translated_line: str, tags: dict[str, str]) -> str:
    return postprocess(translated_line, get_line_tags(line_key, tags))


def generate_translated_file(
    translated_path: Path,
    tags: dict[str, str],
    output_path: Path
) -> None:
    data = json.loads(translated_path.read_text(encoding="utf-8"))
    line_prefix = f"manual.{translated_path.stem}"
    line_keys = sorted(
        [k for k in data.keys() if k.startswith(line_prefix + ".line")],
        key=lambda k: int(k.rsplit(".line", 1)[1])
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            generate_translated_line(line_key, data[line_key], tags)
            for line_key in line_keys
        ),
        encoding="utf-8"
    )


def generate_translated_project(locale: str = "zh_cn") -> None:
    tags_data = load_tags(TAG_PATH)
    translated_root = PROJECT_ROOT / locale
    if not translated_root.exists() or not translated_root.is_dir():
        raise SystemExit(
            f"Translated directory does not exist: {translated_root}")

    output_root = TRANSLATION_ROOT / locale
    files = collect_paths(translated_root, "json")
    for file in files:
        output_path = output_root / \
            file.relative_to(translated_root).with_suffix(".txt")
        generate_translated_file(file, tags_data, output_path)


def main() -> None:
    files = collect_paths(SOURCE_ROOT, "txt")
    for file in files:
        project_path = PROJECT_ROOT / \
            file.relative_to(SOURCE_ROOT).with_suffix(".json")
        process_file(file, project_path)
    TAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    TAG_PATH.write_text(json.dumps(
        tags, ensure_ascii=False, indent=4), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "r":
        main()
    else:
        generate_translated_project()
