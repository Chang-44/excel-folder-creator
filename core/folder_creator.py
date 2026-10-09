"""文件夹创建：递归建树，自动合并"""
from pathlib import Path


def create_tree(tree: dict, root: Path) -> tuple[int, int, list[str]]:
    """
    递归创建整棵树。
    返回 (新建数, 已存在数, 错误列表)
    """
    created = skipped = 0
    errors: list[str] = []

    def _walk(node: dict, base: Path):
        nonlocal created, skipped
        for name, child in node.items():
            p = base / name
            try:
                if p.exists():
                    skipped += 1
                else:
                    p.mkdir(parents=True, exist_ok=False)
                    created += 1
                _walk(child, p)
            except PermissionError:
                errors.append(f"权限不足: {p}")
            except OSError as e:
                errors.append(f"创建失败 {p}: {e}")

    _walk(tree, root)
    return created, skipped, errors


def create_tasks_tree(tasks, root: Path):
    """
    把多个 task 的 paths 合并成一棵树后创建。
    返回 (created, skipped, errors)
    """
    all_paths = []
    for t in tasks:
        if t.status == "invalid":
            continue
        all_paths.extend(t.paths)

    # 合并
    tree: dict = {}
    for path in all_paths:
        node = tree
        for seg in path:
            node = node.setdefault(seg, {})

    return create_tree(tree, root), tree


def rollback_tree(tree: dict, root: Path) -> tuple[int, int]:
    """
    尝试删除本次创建的目录（仅空目录）。
    深度优先，从叶子往根删。
    """
    ok = fail = 0

    def _walk(node: dict, base: Path):
        nonlocal ok, fail
        for name, child in node.items():
            p = base / name
            _walk(child, p)
            if p.exists():
                try:
                    p.rmdir()
                    ok += 1
                except OSError:
                    fail += 1

    _walk(tree, root)
    return ok, fail