"""简单的日志工具"""
import logging
from pathlib import Path


def setup_logger(log_file: str = "run.log") -> logging.Logger:
    logger = logging.getLogger("efc")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(Path(log_file), encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


log = setup_logger()