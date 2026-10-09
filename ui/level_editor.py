"""层级配置控件：可选择列、绑定数量列、上下移动、增删"""
import ttkbootstrap as tb
from ttkbootstrap.constants import *


class LevelEditor(tb.Frame):
    """层级编辑器：一个 Treeview + 按钮 + 编辑区"""

    def __init__(self, master, columns_provider, **kw):
        super().__init__(master, **kw)
        self.columns_provider = columns_provider   # 回调：返回当前可选列
        self.levels: list[dict] = []               # [{column, count_column}, ...]
        self._build()

    def _build(self):
        # 表格
        self.tree = tb.Treeview(
            self, columns=("order", "column", "count"),
            show="headings", height=6, selectmode="browse")
        self.tree.heading("order", text="顺序")
        self.tree.heading("column", text="命名列")
        self.tree.heading("count", text="数量列（可选）")
        self.tree.column("order", width=60, anchor=CENTER)
        self.tree.column("column", width=200)
        self.tree.column("count", width=200)
        self.tree.pack(fill=X)

        # 编辑区
        edit = tb.Frame(self)
        edit.pack(fill=X, pady=(6, 0))

        tb.Label(edit, text="命名列:").grid(row=0, column=0, sticky=W, padx=(0, 4))
        self.cb_col = tb.Combobox(edit, state="readonly", width=18)
        self.cb_col.grid(row=0, column=1, padx=(0, 12))

        tb.Label(edit, text="数量列:").grid(row=0, column=2, sticky=W, padx=(0, 4))
        self.cb_cnt = tb.Combobox(edit, state="readonly", width=18)
        self.cb_cnt.grid(row=0, column=3, padx=(0, 12))

        tb.Button(edit, text="添加", bootstyle="success-outline",
                  command=self._on_add).grid(row=0, column=4, padx=2)
        tb.Button(edit, text="更新选中", bootstyle="info-outline",
                  command=self._on_update).grid(row=0, column=5, padx=2)
        tb.Button(edit, text="删除选中", bootstyle="danger-outline",
                  command=self._on_delete).grid(row=0, column=6, padx=2)

        # 排序按钮
        sort_bar = tb.Frame(self)
        sort_bar.pack(fill=X, pady=(6, 0))
        tb.Button(sort_bar, text="↑ 上移", bootstyle="secondary-outline",
                  command=lambda: self._move(-1)).pack(side=LEFT, padx=2)
        tb.Button(sort_bar, text="↓ 下移", bootstyle="secondary-outline",
                  command=lambda: self._move(1)).pack(side=LEFT, padx=2)

        # 选中行 → 回填到编辑区
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # -------- 对外接口 --------
    def set_columns(self, columns: list[str]):
        """更新可选列"""
        self.cb_col["values"] = columns
        self.cb_cnt["values"] = ["(无)"] + columns

    def get_levels(self) -> list[dict]:
        return [dict(lv) for lv in self.levels]

    def set_levels(self, levels: list[dict]):
        """从配置恢复"""
        self.levels = []
        for lv in levels:
            self.levels.append({
                "column": lv.get("column", ""),
                "count_column": lv.get("count_column") or None,
            })
        self._refresh()

    # -------- 内部 --------
    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, lv in enumerate(self.levels, 1):
            self.tree.insert("", END, iid=str(i - 1), values=(
                i, lv["column"], lv.get("count_column") or "(无)"))

    def _on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        lv = self.levels[idx]
        self.cb_col.set(lv["column"])
        self.cb_cnt.set(lv.get("count_column") or "(无)")

    def _on_add(self):
        col = self.cb_col.get().strip()
        if not col:
            return
        cnt = self.cb_cnt.get().strip()
        cnt = None if cnt in ("", "(无)") else cnt
        self.levels.append({"column": col, "count_column": cnt})
        self._refresh()

    def _on_update(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        col = self.cb_col.get().strip()
        if not col:
            return
        cnt = self.cb_cnt.get().strip()
        cnt = None if cnt in ("", "(无)") else cnt
        self.levels[idx] = {"column": col, "count_column": cnt}
        self._refresh()

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.levels[idx]
        self._refresh()

    def _move(self, delta: int):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        new_idx = idx + delta
        if 0 <= new_idx < len(self.levels):
            self.levels[idx], self.levels[new_idx] = \
                self.levels[new_idx], self.levels[idx]
            self._refresh()
            self.tree.selection_set(str(new_idx))