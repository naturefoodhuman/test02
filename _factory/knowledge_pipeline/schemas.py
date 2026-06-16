# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""知识原子模式定义

定义知识从抓取到入库的全生命周期元数据，确保每一个结论都有据可查。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

class AuditStatus(Enum):
    RAW = "raw"              # 原始抓取，未审核
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已审核通过
    REJECTED = "rejected"    # 审核拒绝
    NEEDS_REVISION = "needs_revision" # 需修改后重新审核

class DataSourceType(Enum):
    STATUTE = "statute"      # 法律条文
    GUIDELINE = "guideline"  # 司法指南/法院公告
    CASE_LAW = "case_law"    # 典型案例
    PRACTICE = "practice"    # 实操经验/白皮书
    LOCAL_CUSTOM = "local_custom" # 地方惯例/地方法规

@dataclass
class KnowledgeAtom:
    """知识原子：知识库的最小可回溯单位"""
    atom_id: str
    content: str
    source_url: str
    source_type: DataSourceType
    region: str = "national" # 如 "henan"
    
    # 回溯链路 (Provenance Chain)
    fetch_date: str = field(default_factory=lambda: datetime.now().isoformat())
    audit_status: AuditStatus = AuditStatus.RAW
    auditor_id: Optional[str] = None
    audit_date: Optional[str] = None
    
    # 质量与权重
    clean_version: Optional[str] = None # 清洗后的版本号
    weight: float = 1.0 # 权重：权威源 > 案例 > 经验
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "content": self.content,
            "source_url": self.source_url,
            "source_type": self.source_type.value,
            "region": self.region,
            "fetch_date": self.fetch_date,
            "audit_status": self.audit_status.value,
            "auditor_id": self.auditor_id,
            "audit_date": self.audit_date,
            "clean_version": self.clean_version,
            "weight": self.weight,
            "tags": self.tags,
        }
