# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""知识回溯管理器

负责管理所有知识原子的生命周期，并提供从结论回溯到来源的链路查询。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional
from .schemas import KnowledgeAtom, AuditStatus, DataSourceType

class ProvenanceManager:
    def __init__(self, root: Path):
        self.root = root
        self.registry_path = root / "_factory" / "knowledge_pipeline" / "provenance_registry.json"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry = json.load(f)
        else:
            self.registry = {}

    def register_atom(self, atom: KnowledgeAtom) -> None:
        """注册一个新的知识原子"""
        self.registry[atom.atom_id] = atom.to_dict()
        self._save()

    def update_status(self, atom_id: str, status: AuditStatus, auditor_id: str) -> None:
        """更新审核状态"""
        if atom_id in self.registry:
            self.registry[atom_id]["audit_status"] = status.value
            self.registry[atom_id]["auditor_id"] = auditor_id
            from datetime import datetime
            self.registry[atom_id]["audit_date"] = datetime.now().isoformat()
            self._save()

    def get_provenance(self, atom_id: str) -> Optional[dict]:
        """获取单个原子的全链路信息"""
        return self.registry.get(atom_id)

    def _save(self) -> None:
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def query_by_region(self, region: str) -> list[dict]:
        """查询特定区域的所有知识"""
        return [v for k, v in self.registry.items() if v.get("region") == region]
