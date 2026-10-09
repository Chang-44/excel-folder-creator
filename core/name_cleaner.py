"""文件夹名称清洗"""
import re

# Windows / 跨平台非法字符
ILLEGAL_CHARS = r'[\\/:*?"<>|\r\n\t]'

# Windows 保留字（不能单独作为文件名）
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *[f"COM{i}" for i in range(1, 10)],
    *[f"LPT{i}" for i in range(1, 10)],
}

MAX_NAME_LEN = 120   # 单段文件夹名长度上限


def clean_name(name: str) -> str:
    """把任意字符串清洗成合法文件夹名"""
    if not name:
        return ""

    # 全角空格、零宽字符归一化
    name = name.replace("\u3000", " ").replace("\u200b", "")

    # 非法字符 → 下划线
    name = re.sub(ILLEGAL_CHARS, "_", name)

    # 首尾处理：去空白、去结尾的点（Windows 不允许）
    name = name.strip().strip(".")

    # 折叠连续空白
    name = re.sub(r"\s+", " ", name)

    # 长度截断
    if len(name) > MAX_NAME_LEN:
        name = name[:MAX_NAME_LEN].rstrip()

    # 保留字
    if name.upper() in WINDOWS_RESERVED:
        name = f"_{name}"

    return name


def is_valid_name(name: str) -> tuple[bool, str]:
    """返回 (是否合法, 原因)"""
    if not name:
        return False, "名称为空"
    if name in (".", ".."):
        return False, "名称为 . 或 .."
    return True, ""