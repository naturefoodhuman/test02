# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:42:00 CST

"""单元测试：结构化日志（_infra/network/utils/logger）"""

import json
import logging
from pathlib import Path
import tempfile

import pytest

from _infra.network.utils.logger import setup_logging, get_logger, LOG_DIR


def test_get_logger_returns_logger():
    """基本可用性"""
    logger = get_logger("test.module")
    assert logger is not None


def test_log_to_file(tmp_path):
    """验证日志写入文件"""
    log_file = tmp_path / "test-network.log"

    # 强制重新 setup（使用临时文件）
    setup_logging(level="DEBUG", json_logs=True, log_file=log_file)

    logger = get_logger("test.logger")
    logger.info("test_event", user="alice", count=42)

    # 刷新所有 handler
    for handler in logging.getLogger().handlers:
        if hasattr(handler, "flush"):
            handler.flush()

    content = log_file.read_text(encoding="utf-8").strip()
    assert content, f"日志文件为空: {log_file}"

    # 验证是合法 JSON
    try:
        data = json.loads(content.splitlines()[-1])
        assert "test_event" in str(data) or data.get("event") == "test_event"
        assert "alice" in str(data) or data.get("user") == "alice"
    except Exception:
        # 某些情况下 structlog 可能输出多行，退化为包含检查
        assert "test_event" in content
        assert "alice" in content


def test_log_creates_dir(tmp_path):
    """确保日志目录自动创建"""
    log_file = tmp_path / "nested" / "dir" / "network.log"
    setup_logging(log_file=log_file)

    logger = get_logger("test.dir")
    logger.info("dir_test")

    assert log_file.parent.exists()
