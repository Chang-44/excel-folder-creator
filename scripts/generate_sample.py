"""
示例数据生成脚本
运行：python scripts/generate_sample.py
生成：samples/示例数据.xlsx（含 4 个 Sheet，覆盖各种边界场景）
"""
import sys
import io
from pathlib import Path

# 强制 stdout 使用 UTF-8，避免 Windows 控制台编码报错
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 允许直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import pandas as pd
except ImportError:
    print("请先安装 pandas：pip install pandas openpyxl")
    sys.exit(1)


SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
OUTPUT_FILE = SAMPLES_DIR / "示例数据.xlsx"


def build_sheet_basic() -> pd.DataFrame:
    """Sheet1：基础多级 + 数量展开"""
    return pd.DataFrame({
        "地区":   ["石家庄", "石家庄", "石家庄", "保定",   "保定",   "唐山"],
        "样点号": ["1001",   "1002",   "1003",   "2001",   "2002",   "3001"],
        "样点数": [3,        1,        0,        5,        2,        4],
        "类型":   ["水样",   "水样",   "水样",   "土样",   "土样",   "气样"],
        "负责人": ["张三",   "张三",   "李四",   "王五",   "王五",   "赵六"],
    })


def build_sheet_multi_level() -> pd.DataFrame:
    """Sheet2：纯多级目录，不带数量展开"""
    return pd.DataFrame({
        "公司":   ["甲公司", "甲公司", "甲公司", "乙公司", "乙公司"],
        "部门":   ["研发部", "研发部", "市场部", "研发部", "财务部"],
        "项目":   ["A项目",  "B项目",  "C项目",  "D项目",  "E项目"],
        "状态":   ["进行中", "已完成", "进行中", "进行中", "已完成"],
    })


def build_sheet_edge_cases() -> pd.DataFrame:
    """Sheet3：边界情况大集合"""
    return pd.DataFrame({
        "名称": [
            "正常名称",
            "  带空格  ",
            "含/非法\\字符",
            "结尾有点.",
            "CON",
            "超长" + "啊" * 200,
            "",
            None,
            "1001",
            "emoji测试",
        ],
        "数量": [3, 1, 2, 1, 0, 2, 1, 3, 1, 2],
        "备注": [
            "普通", "去空格", "字符替换", "去结尾点", "加_前缀",
            "截断", "跳过", "跳过", "正常", "正常",
        ],
    })


def build_sheet_single_column() -> pd.DataFrame:
    """Sheet4：最简单，单列"""
    return pd.DataFrame({
        "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    })


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    sheets = {
        "1-基础多级": build_sheet_basic(),
        "2-纯多级目录": build_sheet_multi_level(),
        "3-边界测试": build_sheet_edge_cases(),
        "4-单列最简": build_sheet_single_column(),
    }

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print(f"[OK] 已生成: {OUTPUT_FILE}")
    print(f"     共 {len(sheets)} 个 Sheet:")
    for name, df in sheets.items():
        print(f"       - {name} ({len(df)} 行, {len(df.columns)} 列)")
    print()
    print("使用建议：")
    print("   1. 启动程序: python main.py")
    print("   2. 选择 Excel: samples/示例数据.xlsx")
    print("   3. 分别测试 4 个 Sheet 的效果")


if __name__ == "__main__":
    main()