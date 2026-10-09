"""数据模型"""
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class LevelConfig:
    """一个层级配置：用某列做目录名，可选绑定数量列展开"""
    column: str                         # 用哪列做目录名
    count_column: str | None = None     # 该层绑定的数量列（None=不展开）
    template: str = "{value}-{序号}"    # 展开模板
    start: int = 1
    pad: int = 0
    one_no_suffix: bool = True          # 数量1时是否不加后缀

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "LevelConfig":
        return cls(
            column=d.get("column", ""),
            count_column=d.get("count_column") or None,
            template=d.get("template", "{value}-{序号}"),
            start=int(d.get("start", 1)),
            pad=int(d.get("pad", 0)),
            one_no_suffix=bool(d.get("one_no_suffix", True)),
        )


@dataclass
class FolderTask:
    """Excel 一行 → 展开成一组路径"""
    source_row: int
    source_name: str
    paths: list[list[str]] = field(default_factory=list)  # 每行可能产生多条路径
    status: str = "pending"
    reason: str = ""


@dataclass
class AppConfig:
    """应用配置（可保存到 config.json）"""
    excel_path: str = ""
    sheet_name: str = ""
    root_dir: str = ""
    levels: list[dict] = field(default_factory=list)
    theme: str = "cosmo"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        return cls(
            excel_path=d.get("excel_path", ""),
            sheet_name=d.get("sheet_name", ""),
            root_dir=d.get("root_dir", ""),
            levels=d.get("levels", []),
            theme=d.get("theme", "cosmo"),
        )