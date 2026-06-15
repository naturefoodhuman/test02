# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 01:45:00 CST
"""KnowledgeHub: 知识统一接口

职责：
- 封装 ChromaDB + LlamaIndex
- 实现 collection 存在性检查 + VERSION 版本控制
- 为 LangGraph 节点提供知识检索
- 注入 SKILL.md 技能到 Agent 上下文
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from peer_review.knowledge_loader import KnowledgeLoader
from peer_review.agent_factory import ExpertConfig


class KnowledgeHub:
    """知识统一接口"""

    def __init__(
        self,
        knowledge_root: Path | str = "_factory/experts",
        skills_root: Path | str = "_factory/skills",
        persist_dir: str = "runtime/chroma_data",
    ):
        self.knowledge_root = Path(knowledge_root)
        self.skills_root = Path(skills_root)
        self.persist_dir = persist_dir

    def load_expert_knowledge(self, expert_id: str) -> Any | None:
        """加载或复用专家知识库"""
        cfg = ExpertConfig(
            id=expert_id,
            name=expert_id,
            role="reviewer",
            knowledge_dir=str(self.knowledge_root / f"{expert_id}.expert" / "knowledge"),
        )
        return KnowledgeLoader.load_knowledge(cfg, persist_dir=self.persist_dir)

    def search(self, expert_id: str, query: str, top_k: int = 5) -> list[str]:
        """检索专家知识库

        当前实现优先返回知识库文本片段；若 ChromaDB 不可用则返回空列表。
        """
        kb = self.load_expert_knowledge(expert_id)
        if kb is None:
            return []
        # ChromaDb 直接查询能力依赖 agno 封装；这里做兼容尝试
        try:
            if hasattr(kb, "search"):
                results = kb.search(query, n_results=top_k)
                return [str(r) for r in results]
        except Exception:
            pass
        return []

    def inject_skill(self, skill_id: str, context: dict[str, Any]) -> None:
        """将 SKILL.md 技能文件内容注入上下文"""
        skill_path = self.skills_root / f"{skill_id}.skill.md"
        if skill_path.exists():
            context["injected_skills"] = skill_path.read_text(encoding="utf-8")
