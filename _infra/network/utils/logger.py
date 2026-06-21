# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:55:00 CST

"""
结构化日志（FORGE Network 增量）

功能：
- JSON 或人类可读格式
- 文件 + 控制台
- 支持 logger.info("msg", key=val) 风格
- 自动创建 runtime/logs/
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path("runtime/logs")
LOG_FILE = LOG_DIR / "network-agent.log"


def _ensure_logs_dir(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        # 支持通过 extra 传递
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            data.update(record.extra_data)
        return json.dumps(data, ensure_ascii=False)


class NetworkLogger:
    """轻量封装，支持 logger.info(msg, **kwargs)"""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(self, level: str, msg: str, **kwargs: Any) -> None:
        if kwargs:
            # 存到 extra 以便 formatter 使用
            extra = {"extra_data": kwargs}
            getattr(self._logger, level)(msg, extra=extra)
        else:
            getattr(self._logger, level)(msg)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log("error", msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log("debug", msg, **kwargs)


def setup_logging(
    level: str = "INFO",
    json_logs: bool | None = None,
    log_file: Path | str = LOG_FILE,
) -> None:
    log_file = Path(log_file)
    _ensure_logs_dir(log_file)

    lvl = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(lvl)

    # 文件 handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    use_json = json_logs if json_logs is not None else (os.getenv("NETWORK_LOG_JSON", "false").lower() == "true")

    if use_json:
        fh.setFormatter(_JSONFormatter())
    else:
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    # 控制台
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root.addHandler(fh)
    root.addHandler(ch)


def get_logger(name: str) -> NetworkLogger:
    """返回封装后的 logger"""
    return NetworkLogger(name)


# 模块导入时自动初始化（除测试外）
if "pytest" not in sys.modules:
    setup_logging()
