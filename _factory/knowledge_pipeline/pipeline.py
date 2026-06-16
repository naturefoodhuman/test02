# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""知识工程流水线 (Knowledge Engineering Pipeline)

职责：
1. Acquire (获取): 从源头抓取数据
2. Audit (审核): 验证真实性与权威性
3. Clean (清洗): 结构化为知识原子
4. Ingest (入库): 同步至各专家知识库
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Optional
from .schemas import KnowledgeAtom, AuditStatus, DataSourceType
from .provenance_manager import ProvenanceManager

class KnowledgePipeline:
    def __init__(self, root: Path):
        self.root = root
        self.provenance = ProvenanceManager(root)

    def acquire(self, content: str, source_url: str, source_type: DataSourceType, region: str = "national") -> str:
        """步骤 1: 获取知识并注册原始状态"""
        atom_id = f"ATOM-{uuid.uuid4().hex[:8].upper()}"
        atom = KnowledgeAtom(
            atom_id=atom_id,
            content=content,
            source_url=source_url,
            source_type=source_type,
            region=region,
            audit_status=AuditStatus.RAW
        )
        self.provenance.register_atom(atom)
        return atom_id

    def audit(self, atom_id: str, auditor_id: str, status: AuditStatus) -> bool:
        """步骤 2: 审核知识"""
        self.provenance.update_status(atom_id, status, auditor_id)
        return status == AuditStatus.APPROVED

    def clean(self, atom_id: str, cleaned_content: str, version: str = "1.0") -> str:
        """步骤 3: 清洗并结构化知识"""
        # 在 provenance 中更新 cleaned_content
        if atom_id in self.provenance.registry:
            self.provenance.registry[atom_id]["clean_content"] = cleaned_content
            self.provenance.registry[atom_id]["clean_version"] = version
            self.provenance._save()
        return cleaned_content

    def ingest(self, atom_id: str, expert_name: str) -> bool:
        """步骤 4: 入库到指定专家知识库"""
        atom_data = self.provenance.get_provenance(atom_id)
        if not atom_data or atom_data["audit_status"] != AuditStatus.APPROVED.value:
            print(f"❌ 拒绝入库: {atom_id} 未通过审核")
            return False
        
        # 实际入库逻辑：写入 _factory/experts/{expert_name}/knowledge/ 目录下
        expert_knowledge_dir = self.root / "_factory" / "experts" / f"{expert_name}.expert" / "knowledge"
        expert_knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入知识碎片文件 (以原子 ID 命名)
        file_path = expert_knowledge_dir / f"{atom_id}.md"
        content = f"""---
atom_id: {atom_id}
source: {atom_data['source_url']}
type: {atom_data['source_type']}
region: {atom_data['region']}
weight: {atom_data['weight']}
---
{atom_data.get('clean_content', atom_data['content'])}
"""
        file_path.write_text(content, encoding="utf-8")
        return True
