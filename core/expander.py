"""多级目录展开逻辑"""
import re
from typing import Any

from .models import LevelConfig, FolderTask
from .name_cleaner import clean_name, is_valid_name

TEMPLATE_FIELD_RE = re.compile(r"\{([^{}]+)\}")


def parse_count(value: Any) -> int:
    """安全转非负整数"""
    if value is None:
        return 0
    if isinstance(value, float) and value != value:  # NaN
        return 0
    s = str(value).strip()
    if not s:
        return 0
    try:
        return max(int(float(s)), 0)
    except ValueError:
        m = re.search(r"\d+", s)
        return int(m.group()) if m else 0


def render_template(template: str, value: str, seq: str, count: int,
                    row: dict) -> str:
    """渲染展开模板"""
    fields = {
        "value": value, "名称": value, "列值": value,
        "序号": seq, "序号": seq,
        "数量": str(count),
        **{k: ("" if v is None else str(v)) for k, v in row.items()},
    }

    def _replace(m):
        key = m.group(1).strip()
        return str(fields.get(key, m.group(0)))
    return TEMPLATE_FIELD_RE.sub(_replace, template)


def expand_row_to_paths(row, levels):
    paths = [[]]

    for lv in levels:
        raw_value = row.get(lv.column, "")
        value = clean_name("" if raw_value is None else str(raw_value).strip())

        if not value:
            continue

        ok, reason = is_valid_name(value)
        if not ok:
            return [], f"列【{lv.column}】的值非法: {reason}"

        count = parse_count(row.get(lv.count_column)) if lv.count_column else 0
        need_expand = lv.count_column and (
            count > 1 or (count == 1 and not lv.one_no_suffix)
        )

        if not need_expand:
            # 普通层：直接追加一段
            new_paths = []
            for p in paths:
                new_paths.append(p + [value])
            paths = new_paths
        else:
            # ★ 展开层：主目录 + 子目录是【嵌套】关系
            # 对每条已有路径，生成：[..., value, value-1] / [..., value, value-2] / ...
            children = []
            for i in range(lv.start, lv.start + count):
                seq = str(i).zfill(lv.pad) if lv.pad > 0 else str(i)
                child = clean_name(render_template(lv.template, value, seq, count, row))
                if child and child != value:
                    children.append(child)

            if not children:
                # 数量异常时退化为只建主目录
                new_paths = []
                for p in paths:
                    new_paths.append(p + [value])
                paths = new_paths
            else:
                new_paths = []
                for p in paths:
                    for child in children:
                        new_paths.append(p + [value, child])   # ★ 主目录 + 子目录
                paths = new_paths

    return paths, ""

def build_tasks(rows: list[dict], levels: list[LevelConfig]) -> list[FolderTask]:
    """把整表转成 FolderTask 列表"""
    tasks: list[FolderTask] = []
    for i, row in enumerate(rows, start=2):
        raw_name = ""
        if levels:
            raw_name = str(row.get(levels[0].column, "") or "").strip()
        paths, reason = expand_row_to_paths(row, levels)
        t = FolderTask(source_row=i, source_name=raw_name, paths=paths)
        if reason:
            t.status = "invalid"
            t.reason = reason
        elif not paths or all(not p for p in paths):
            t.status = "invalid"
            t.reason = "所有层级均为空"
        tasks.append(t)
    return tasks


def merge_paths_into_tree(all_paths: list[list[str]]) -> dict:
    """
    把所有路径合并成一棵树。
    中间层重复自动合并（同地区只建一次）。
    """
    tree: dict = {}
    for path in all_paths:
        node = tree
        for seg in path:
            node = node.setdefault(seg, {})
    return tree