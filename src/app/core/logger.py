import sys
from pathlib import Path
from loguru import logger

# 假设你的结构是 project_root/src/...
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"


def path_patcher(record):
    """
    Loguru 的补丁函数。
    它会在每次日志记录之前运行，用于计算相对路径并注入到 extra 字典中。
    """
    try:
        file_path = Path(record["file"].path)
        # 计算相对于 PROJECT_ROOT 的路径
        rel_path = file_path.relative_to(PROJECT_ROOT)
        record["extra"]["rel_path"] = str(rel_path)
    except ValueError:
        # 如果文件不在 PROJECT_ROOT 下，回退到仅显示文件名
        record["extra"]["rel_path"] = record["file"].name


def _setup_logging():
    """
    配置日志的内部函数。
    私有函数（下划线开头），不需要外部调用。
    """
    # 1. 创建日志目录
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 清除旧配置（防止重复添加 sink）
    logger.remove()

    # 3. 应用 patcher
    # 注意：configure 只需要调用一次
    logger.configure(patcher=path_patcher)

    # 定义统一的格式字符串
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[rel_path]}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 4. 添加控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG",
        enqueue=True,
    )

    # 5. 添加常规文件输出
    logger.add(
        LOG_DIR / "app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level="INFO",
        format=log_format,
        encoding="utf-8",
        enqueue=True,
    )

    # 6. 添加错误日志输出
    logger.add(
        LOG_DIR / "error.log",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        format=log_format,
        encoding="utf-8",
        enqueue=True,
    )


_setup_logging()

__all__ = ["logger"]
