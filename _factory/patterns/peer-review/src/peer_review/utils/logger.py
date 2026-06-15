# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 17:30:00 CST
"""统一日志配置模块

提供结构化日志系统：
- 文件输出：RotatingFileHandler -> runtime/logs/peer_review.log
- 终端输出：Rich Handler (带颜色、进度条)
- 统一格式：时间、模块、级别、消息
- 级别控制：环境变量 LOG_LEVEL (默认 INFO)
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# ──────────────────────────────────────────────────────────────────
# 配置常量
# ──────────────────────────────────────────────────────────────────

DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path("runtime/logs")
LOG_FILE = LOG_DIR / "peer_review.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# 统一格式
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ──────────────────────────────────────────────────────────────────
# 内部状态
# ──────────────────────────────────────────────────────────────────

_configured = False
_console = Console(stderr=True)


def _ensure_log_dir() -> None:
    """确保日志目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _create_file_handler() -> logging.handlers.RotatingFileHandler:
    """创建轮转文件处理器"""
    _ensure_log_dir()
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    handler.setLevel(logging.DEBUG)  # 文件记录所有级别
    return handler


def _create_rich_handler() -> RichHandler:
    """创建 Rich 终端处理器"""
    handler = RichHandler(
        console=_console,
        show_time=True,
        show_level=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    handler.setLevel(getattr(logging, DEFAULT_LOG_LEVEL))
    return handler


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    *,
    force: bool = False,
) -> None:
    """配置全局日志系统 (只需调用一次)

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)，默认读取 LOG_LEVEL 环境变量
        log_file: 自定义日志文件路径
        force: 强制重新配置 (测试用)
    """
    global _configured

    if _configured and not force:
        return

    # 确定日志级别
    log_level = level or DEFAULT_LOG_LEVEL
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 根级别设为最低，由 handler 控制

    # 清除现有 handler (避免重复)
    if force:
        root_logger.handlers.clear()

    # 文件 handler (始终添加，记录完整日志)
    file_handler = _create_file_handler()
    root_logger.addHandler(file_handler)

    # 终端 handler (Rich，带颜色)
    rich_handler = _create_rich_handler()
    root_logger.addHandler(rich_handler)

    # 避免第三方库日志过多
    logging.getLogger("agno").setLevel(logging.WARNING)
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _configured = True

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成 | 级别=%s | 文件=%s", log_level, LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """获取模块级日志器

    用法：
        from peer_review.utils.logger import get_logger
        logger = get_logger(__name__)

        logger.debug("调试信息")
        logger.info("正常信息")
        logger.warning("警告")
        logger.error("错误")
    """
    if not _configured:
        configure_logging()
    return logging.getLogger(name)


# ──────────────────────────────────────────────────────────────────
# 便捷函数 (兼容旧版 print/console.print)
# ──────────────────────────────────────────────────────────────────

def log_info(msg: str, *args, **kwargs) -> None:
    """快速记录 INFO 级别日志"""
    get_logger("peer_review").info(msg, *args, **kwargs)


def log_warning(msg: str, *args, **kwargs) -> None:
    """快速记录 WARNING 级别日志"""
    get_logger("peer_review").warning(msg, *args, **kwargs)


def log_error(msg: str, *args, **kwargs) -> None:
    """快速记录 ERROR 级别日志"""
    get_logger("peer_review").error(msg, *args, **kwargs)


def log_debug(msg: str, *args, **kwargs) -> None:
    """快速记录 DEBUG 级别日志"""
    get_logger("peer_review").debug(msg, *args, **kwargs)


def log_exception(msg: str, *args, **kwargs) -> None:
    """记录异常 (含堆栈跟踪)"""
    get_logger("peer_review").exception(msg, *args, **kwargs)


# ──────────────────────────────────────────────────────────────────
# 自动配置 (导入即生效)
# ──────────────────────────────────────────────────────────────────

# 延迟配置：首次调用 get_logger 或便捷函数时自动配置
# 也可显式调用 configure_logging() 自定义配置