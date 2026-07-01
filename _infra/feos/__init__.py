# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FORGE Escalation OS (FEOS) incremental infrastructure module.

FEOS is implemented under `_infra/feos` as an additive FORGE Factory module.
This package intentionally exposes only static metadata at FEOS-001; business
logic starts in later backlog tasks.
"""

from __future__ import annotations

__all__ = ["__version__", "load_config", "bootstrap_feos"]

__version__ = "0.4.0-feos-storage"

from .config_loader import load_config
from .bootstrap import bootstrap_feos
