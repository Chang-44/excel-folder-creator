"""主界面"""
import threading
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, X, W, LEFT, END, RIGHT

from core.excel_reader import read_excel_info, read_rows
from core.expander import build_tasks, merge_paths_into_tree
from core.folder_creator import create_tree, rollback_tree
from core.models import LevelConfig, AppConfig
from core.config_manager import load_config, save_config
from ui.level_editor import LevelEditor
from utils.logger import log


class MainWindow(tb.Window):
    def __init__(self):
        cfg = load_config()
        super().__init__(themename=cfg.theme or "cosmo")
        self.title("Excel 文件夹批量创建工具 · 多级版")
        self.geometry("1020x860")
        self.minsize(940, 760)

        self.cfg = cfg

        # ---- 变量 ----
        self.excel_path = tb.StringVar(value=cfg.excel_path)
        self.sheet_name = tb.StringVar(value=cfg.sheet_name)
        self.root_dir = tb.StringVar(value=cfg.root_dir)
        self.template = tb.StringVar(value="{value}-{序号}")
        self.start_seq = tb.IntVar(value=1)
        self.pad = tb.IntVar(value=0)
        self.one_no_suffix = tb.BooleanVar(value=True)

        self.tasks = []
        self._excel_info: dict[str, list[str]] = {}

        self._build_ui()
        self._restore_config()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = dict(padx=10, pady=6)

        # ===== 基础配置 =====
        frm = tb.Labelframe(self, text="① 基础配置", padding=10)
        frm.pack(fill=X, **pad)
        frm.columnconfigure(1, weight=1)

        tb.Label(frm, text="Excel 文件:").grid(row=0, column=0, sticky=W, pady=3)
        tb.Entry(frm, textvariable=self.excel_path).grid(row=0, column=1, sticky="ew", padx=6)
        tb.Button(frm, text="浏览", command=self.on_pick_excel,
                  bootstyle="secondary-outline").grid(row=0, column=2)

        tb.Label(frm, text="工作表:").grid(row=1, column=0, sticky=W, pady=3)
        self.cb_sheet = tb.Combobox(frm, textvariable=self.sheet_name, state="readonly", width=28)
        self.cb_sheet.grid(row=1, column=1, sticky=W, padx=6)
        self.cb_sheet.bind("<<ComboboxSelected>>", self.on_sheet_change)

        tb.Label(frm, text="输出根目录:").grid(row=2, column=0, sticky=W, pady=3)
        tb.Entry(frm, textvariable=self.root_dir).grid(row=2, column=1, sticky="ew", padx=6)
        tb.Button(frm, text="浏览", command=self.on_pick_root,
                  bootstyle="secondary-outline").grid(row=2, column=2)

        # ===== 层级配置 =====
        frm2 = tb.Labelframe(self, text="② 目录层级配置（顺序=由外到内）", padding=10)
        frm2.pack(fill=X, **pad)

        self.level_editor = LevelEditor(frm2, columns_provider=lambda: self._current_columns())
        self.level_editor.pack(fill=X)

        # 展开参数
        param = tb.Frame(frm2)
        param.pack(fill=X, pady=(8, 0))
        tb.Label(param, text="展开模板:").pack(side=LEFT)
        tb.Entry(param, textvariable=self.template, width=22).pack(side=LEFT, padx=4)
        tb.Label(param, text="（可用 {value} {序号} {数量} {任意列名}）",
                 bootstyle="secondary").pack(side=LEFT)
        tb.Label(param, text="  起始:").pack(side=LEFT)
        tb.Spinbox(param, from_=0, to=9999, textvariable=self.start_seq,
                   width=6).pack(side=LEFT)
        tb.Label(param, text="补零:").pack(side=LEFT)
        tb.Spinbox(param, from_=0, to=10, textvariable=self.pad,
                   width=5).pack(side=LEFT)
        tb.Checkbutton(param, text="数量1不加后缀",
                       variable=self.one_no_suffix,
                       onvalue=True, offvalue=False).pack(side=LEFT, padx=10)

        # ===== 操作栏 =====
        bar = tb.Frame(self)
        bar.pack(fill=X, **pad)
        tb.Button(bar, text="🔍 预览", command=self.on_preview,
                  bootstyle="info").pack(side=LEFT, padx=4)
        tb.Button(bar, text="🚀 开始创建", command=self.on_create,
                  bootstyle="success").pack(side=LEFT, padx=4)
        tb.Button(bar, text="🧹 清理本次创建", command=self.on_rollback,
                  bootstyle="danger-outline").pack(side=LEFT, padx=4)
        tb.Button(bar, text="清空", command=self.on_clear,
                  bootstyle="secondary-outline").pack(side=LEFT, padx=4)
        tb.Button(bar, text="💾 保存配置", command=self.on_save_cfg,
                  bootstyle="secondary-outline").pack(side=RIGHT, padx=4)

        # ===== 预览表格 =====
        tree_frm = tb.Labelframe(self, text="③ 预览 / 结果", padding=6)
        tree_frm.pack(fill=BOTH, expand=True, **pad)

        cols = ("row", "path", "status", "reason")
        self.tree = tb.Treeview(tree_frm, columns=cols, show="headings", height=14)
        for c, t, w in zip(cols,
                           ("来源行", "路径", "状态", "备注"),
                           (70, 620, 90, 200)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=W)
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)

        sb = tb.Scrollbar(tree_frm, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # ===== 进度条 =====
        self.pb = tb.Progressbar(self, bootstyle="success-striped", maximum=100)
        self.pb.pack(fill=X, padx=10, pady=(0, 4))

        self.status_var = tb.StringVar(value="就绪")
        tb.Label(self, textvariable=self.status_var,
                 bootstyle="secondary").pack(fill=X, padx=10, pady=(0, 6))

    # ---------------- 配置恢复 ----------------
    def _restore_config(self):
        if self.cfg.excel_path and Path(self.cfg.excel_path).exists():
            try:
                self._excel_info = read_excel_info(self.cfg.excel_path)
                sheets = list(self._excel_info.keys())
                self.cb_sheet["values"] = sheets
                if not self.sheet_name.get() and sheets:
                    self.sheet_name.set(sheets[0])
                self._refresh_columns()
            except Exception:
                log.warning("恢复配置时读取 Excel 失败", exc_info=True)

        self.level_editor.set_levels(self.cfg.levels)
        self.level_editor.set_columns(self._current_columns())

    def _current_columns(self) -> list[str]:
        sheet = self.sheet_name.get()
        return self._excel_info.get(sheet, [])

    def _refresh_columns(self):
        self.level_editor.set_columns(self._current_columns())

    # ---------------- 事件 ----------------
    def on_pick_excel(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            self.excel_path.set(path)
            self._excel_info = read_excel_info(path)
            sheets = list(self._excel_info.keys())
            if not sheets:
                messagebox.showwarning("提示", "文件里没有工作表")
                return
            self.cb_sheet["values"] = sheets
            self.sheet_name.set(sheets[0])
            self._refresh_columns()
            log.info(f"加载 Excel: {path}, sheets={sheets}")
        except Exception as e:
            log.error(traceback.format_exc())
            messagebox.showerror("读取失败", f"{e}")

    def on_sheet_change(self, _evt=None):
        self._refresh_columns()

    def on_pick_root(self):
        d = filedialog.askdirectory(title="选择输出根目录")
        if d:
            self.root_dir.set(d)

    def on_clear(self):
        self.tree.delete(*self.tree.get_children())
        self.tasks = []
        self.pb["value"] = 0
        self.status_var.set("已清空")

    def on_save_cfg(self):
        cfg = AppConfig(
            excel_path=self.excel_path.get(),
            sheet_name=self.sheet_name.get(),
            root_dir=self.root_dir.get(),
            levels=self.level_editor.get_levels(),
        )
        save_config(cfg)
        self.status_var.set("配置已保存到 config.json")
        messagebox.showinfo("提示", "配置已保存")

    # ---------------- 预览 ----------------
    def on_preview(self):
        try:
            self.tasks, self._tree = self._build_tasks_and_tree()
        except Exception as e:
            log.error(traceback.format_exc())
            messagebox.showerror("错误", str(e))
            return

        self.tree.delete(*self.tree.get_children())
        for t in self.tasks:
            if t.status == "invalid":
                self.tree.insert("", END, values=(
                    t.source_row, t.source_name or "(空)", "非法", t.reason))
                continue
            for p in t.paths:
                self.tree.insert("", END, values=(
                    t.source_row, "/".join(p), "待创建", ""))

        total_paths = sum(len(t.paths) for t in self.tasks)
        self.status_var.set(
            f"预览完成：{len(self.tasks)} 行，展开 {total_paths} 条路径")
        log.info(f"预览: {len(self.tasks)} 行, {total_paths} 路径")

    def _build_tasks_and_tree(self):
        path = self.excel_path.get().strip()
        sheet = self.sheet_name.get().strip()
        if not path:
            raise ValueError("请先选择 Excel 文件")
        if not sheet:
            raise ValueError("请先选择工作表")

        level_dicts = self.level_editor.get_levels()
        if not level_dicts:
            raise ValueError("请至少配置一个层级")

        # 组装 LevelConfig，把展开参数填进去
        levels = []
        for ld in level_dicts:
            levels.append(LevelConfig(
                column=ld["column"],
                count_column=ld.get("count_column"),
                template=self.template.get() or "{value}-{序号}",
                start=self.start_seq.get(),
                pad=self.pad.get(),
                one_no_suffix=self.one_no_suffix.get(),
            ))

        rows = read_rows(path, sheet)
        tasks = build_tasks(rows, levels)

        all_paths = []
        for t in tasks:
            if t.status != "invalid":
                all_paths.extend(t.paths)
        tree = merge_paths_into_tree(all_paths)
        return tasks, tree

    # ---------------- 创建 ----------------
    def on_create(self):
        if not self.tasks:
            messagebox.showwarning("提示", "请先点击「预览」")
            return
        root_str = self.root_dir.get().strip()
        if not root_str:
            messagebox.showerror("错误", "请选择输出根目录")
            return
        root = Path(root_str)
        if not root.exists() or not root.is_dir():
            messagebox.showerror("错误", "输出根目录不存在")
            return

        total_paths = sum(len(t.paths) for t in self.tasks)
        if not messagebox.askyesno(
                "确认",
                f"将在:\n{root}\n创建 {total_paths} 条路径对应的目录，是否继续？"):
            return

        self._run_create(root)

    def _run_create(self, root: Path):
        def worker():
            created, skipped, errors = create_tree(self._tree, root)
            summary = f"完成：新建 {created}，已存在 {skipped}，错误 {len(errors)}"
            if errors:
                summary += "\n\n前 5 条错误：\n" + "\n".join(errors[:5])
            self.status_var.set(summary.split("\n")[0])
            log.info(summary)
            messagebox.showinfo("完成", summary)

        threading.Thread(target=worker, daemon=True).start()

    # ---------------- 清理 ----------------
    def on_rollback(self):
        if not hasattr(self, "_tree") or not self._tree:
            messagebox.showwarning("提示", "没有可清理的记录")
            return
        root_str = self.root_dir.get().strip()
        if not root_str:
            return
        root = Path(root_str)
        if not messagebox.askyesno(
                "危险操作",
                "将尝试删除本次创建的所有【空】目录。\n"
                "非空目录会被保留。是否继续？"):
            return
        ok, fail = rollback_tree(self._tree, root)
        messagebox.showinfo("清理完成",
                            f"已删除 {ok} 个空目录，{fail} 个因非空被保留")
        self.status_var.set(f"清理：成功 {ok}，保留 {fail}")


def run():
    MainWindow().mainloop()