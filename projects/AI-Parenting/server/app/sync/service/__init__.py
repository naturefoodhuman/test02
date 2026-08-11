# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/sync/service/__init__.py —— 同步用例服务层聚合导出。
# 依据：ENGINEERING_DESIGN §6.3（同步契约）、§9.1（不自研同步）；ARCHITECTURE_FINAL §9.2；
#       TASK_BACKLOG APC-T012。
"""同步用例服务层聚合导出（契约校验 + 冲突软提示）。"""

from .conflict_detector import ConflictHint, detect_duplicate_feeding
from .contract_validator import validate_sync_contract

__all__ = ["ConflictHint", "detect_duplicate_feeding", "validate_sync_contract"]
