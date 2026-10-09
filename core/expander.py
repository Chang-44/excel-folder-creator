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


def expand_row_to_paths(
    row: dict,
    levels: list[LevelConfig],
) -> tuple[list[list[str]], str]:
    """
    把一行按层级配置展开成多条路径。
    返回 (paths, error_reason)
    paths 例：[
        ['石家庄', '1001', '1001-1', '水样'],
        ['石家庄', '1001', '1001-2', '水样'],
    ]
    A1 规则：数量展开的序号层作为【下一级】插入，后续层级挂在展开层内部。
    """
    paths: list[list[str]] = [[]]

    for lv in levels:
        raw_value = row.get(lv.column, "")
        value = clean_name("" if raw_value is None else str(raw_value).strip())

        # 空值层跳过
        if not value:
            continue

        ok, reason = is_valid_name(value)
        if not ok:
            return [], f"列【{lv.column}】的值非法: {reason}"

        # 本层要追加的"段"列表
        # 无数量列 或 数量<=1且不加后缀 → 单段
        # 有数量列 且 (数量>1 或 数量==1且加后缀) → [value, value-1, value-2...]
        count = parse_count(row.get(lv.count_column)) if lv.count_column else 0
        need_expand = lv.count_column and (
            count > 1 or (count == 1 and not lv.one_no_suffix)
        )

        if not need_expand:
            new_segments = [value]
        else:
            segments = [value]  # 主目录
            for i in range(lv.start, lv.start + count):
                seq = str(i).zfill(lv.pad) if lv.pad > 0 else str(i)
                child = clean_name(render_template(lv.template, value, seq, count, row))
                if child and child != value:
                    segments.append(child)
            new_segments = segments

        # 拼接：本层的每个段都要和已有所有路径组合
        # 注意 A1 语义：展开层产生的多个段，是【并列的独立分支】
        # 后续层级会分别挂到每个段下面
        new_paths = []
        for p in paths:
            for seg in new_segments:
                new_paths.append(p + [seg])
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