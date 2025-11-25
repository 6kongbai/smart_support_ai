import sys
from pathlib import Path
from loguru import logger

# 假设你的结构是 project_root/src/...
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"


def path_patcher(record):
    """
    Loguru patcher：注入 rel_path，并保证 thread_id 有默认值，避免 format KeyError。
    """
    try:
        file_path = Path(record["file"].path)
        rel_path = file_path.relative_to(PROJECT_ROOT)
        record["extra"]["rel_path"] = str(rel_path)
    except ValueError:
        record["extra"]["rel_path"] = record["file"].name

    record["extra"].setdefault("thread_id", "-")


def _setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.configure(patcher=path_patcher)

    # ✅ 只额外打印 thread_id
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>{extra[thread_id]}</magenta> | "
        "<cyan>{extra[rel_path]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG",
        enqueue=True,
        catch=True,
    )

    logger.add(
        LOG_DIR / "app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level="INFO",
        format=log_format,
        encoding="utf-8",
        enqueue=True,
        catch=True,
    )

    logger.add(
        LOG_DIR / "error.log",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        format=log_format,
        encoding="utf-8",
        enqueue=True,
        catch=True,
    )


_setup_logging()
