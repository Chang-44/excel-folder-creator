"""Excel 读取"""
import pandas as pd


def read_excel_info(path: str) -> dict[str, list[str]]:
    """返回 {sheet_name: [列名, ...]}"""
    xls = pd.ExcelFile(path)
    info: dict[str, list[str]] = {}
    for s in xls.sheet_names:
        df = xls.parse(s, nrows=0)
        info[s] = [str(c).strip() for c in df.columns]
    return info


def read_rows(path: str, sheet: str) -> list[dict]:
    """读整张表为 list[dict]，列名已 strip，NaN 保留"""
    df = pd.read_excel(path, sheet_name=sheet, dtype=object)
    df.columns = [str(c).strip() for c in df.columns]
    # 用 NaN 保持原样，交给 expander 处理
    return df.to_dict(orient="records")