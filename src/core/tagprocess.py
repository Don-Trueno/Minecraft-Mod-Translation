import re
from typing import Iterable, Tuple, cast, Dict, Set, List


tag_map: dict[str, str] = {}
tag_id = 0

pattern = re.compile(r"<([^<>]*)>")


def new_tag(text: str) -> str:
    """生成占位符，占位符的序号递增"""
    global tag_id
    key = f"{{{tag_id}}}"
    tag_id += 1
    tag_map[key] = text
    return key


def normalize_tag_rules(tag_rules: dict[str, int | list[int]] | list[dict[str, int | list[int]]] | None) -> List[Dict[str, object]]:
    """Normalize various rule formats into a list of rule dicts.

    Each rule dict: { 'prefix_parts': list[str], 'preserved': set[int], 'required_parts': {index: set[str]} }
    """
    if not tag_rules:
        return []

    normalized: List[Dict[str, object]] = []

    if isinstance(tag_rules, dict):
        items: Iterable[Tuple[str, int | list[int]]] = tag_rules.items()
        iterator = ((tag, {"preserved_index": preserved}) for tag, preserved in items)
    else:
        iterator = (rule for rule in tag_rules if isinstance(rule, dict))

    for rule in iterator:
        if isinstance(rule, tuple):
            required_prefix, preserved_index = rule
            required = None
        else:
            required_prefix = rule.get("required_prefix") or rule.get("tag")
            preserved_index = rule.get("preserved_index")
            required = rule.get("required_parts")

        if not isinstance(required_prefix, str):
            continue

        prefix_parts = required_prefix.split(";") if required_prefix else []

        preserved_set: Set[int] = set()
        if isinstance(preserved_index, int):
            preserved_set = {preserved_index}
        elif isinstance(preserved_index, list):
            preserved_set = {int(i) for i in preserved_index}

        req_parts: Dict[int, Set[str]] = {}
        if isinstance(required, dict):
            for k, v in required.items():
                try:
                    idx = int(k)
                except Exception:
                    if isinstance(k, int):
                        idx = k
                    else:
                        continue

                if isinstance(v, str):
                    req_parts[idx] = {v}
                elif isinstance(v, list):
                    req_parts[idx] = {str(x) for x in v}

        normalized.append({"prefix_parts": prefix_parts, "preserved": preserved_set, "required_parts": req_parts})

    return normalized


def placeholder_for_group(parts: list[str], start: int, end: int) -> str:
    text = "<" if start == 0 else ";"
    text += ";".join(parts[start:end])
    return new_tag(text)


def replace_tag(match: re.Match, tag_rules: dict[str, int | list[int]] | list[dict[str, int | list[int]]] | None = None) -> str:
    content = match.group(1)
    parts = content.split(";")
    rules = normalize_tag_rules(tag_rules)

    matched_rule = None
    for r in rules:
        prefix_parts = cast(List[str], r.get("prefix_parts", []))
        if len(prefix_parts) == 0:
            continue
        if len(parts) >= len(prefix_parts) and parts[: len(prefix_parts)] == prefix_parts:
            matched_rule = r
            break

    if not matched_rule:
        return new_tag(match.group(0))

    preserved_indices: Set[int] = cast(Set[int], matched_rule.get("preserved", set()))
    required_parts: Dict[int, Set[str]] = cast(Dict[int, Set[str]], matched_rule.get("required_parts", {}))

    for idx, allowed in required_parts.items():
        if idx >= len(parts) or parts[idx] not in allowed:
            return new_tag(match.group(0))

    result = ""
    group_start = 0
    in_group = False

    for index, _part in enumerate(parts):
        if index not in preserved_indices:
            if not in_group:
                group_start = index
                in_group = True
            continue

        if in_group:
            result += placeholder_for_group(parts, group_start, index)
            in_group = False

        if index > 0:
            result += new_tag(";")
        result += parts[index]

    if in_group:
        result += placeholder_for_group(parts, group_start, len(parts))

    result += new_tag(">")
    return result


def preprocess(text: str, tag_rules: dict[str, int | list[int]] | list[dict[str, int | list[int]]] | None = None) -> tuple[str, dict[str, str]]:
    global tag_map, tag_id
    tag_map = {}
    tag_id = 0

    def replacer(match: re.Match) -> str:
        return replace_tag(match, tag_rules)

    result = pattern.sub(replacer, text)
    return result, tag_map


def preprocess_list(texts: list[str],  tag_rules: dict[str, int | list[int]] | list[dict[str, int | list[int]]] | None = None) -> tuple[list[str], dict[str, str]]:
    result = []
    tag_map = {}

    for text in texts:
        processed, mapping = preprocess(text, tag_rules)
        result.append(processed)
        tag_map.update(mapping)

    return result, tag_map


def postprocess(text: str, tag_map: dict[str, str]) -> str:
    for key in sorted(tag_map.keys(), key=len, reverse=True):
        text = text.replace(key, tag_map[key])
    return text
