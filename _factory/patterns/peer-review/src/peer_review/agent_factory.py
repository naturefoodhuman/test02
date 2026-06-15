# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 16:30:00 CST
"""专家工厂模块

从 orchestrator.py 提取，单一职责：根据配置创建 Agent 实例。
"""

from __future__ import annotations

from typing import Any

# Agno 导入移至具体函数内部，避免在 LangGraph 纯净环境下启动崩溃

AgentKnowledge = None
try:
    from agno.knowledge.agent import AgentKnowledge
except ImportError:
    pass

# --- 兼容性：模型别名映射 ---
MODEL_ALIAS_MAP = {
    "local/primary": "qwen3.6:35b-a3b-q8_0",
    "local/r1": "deepseek-r1:32b",
    "cloud/glm-primary": "openai/glm-4-plus",
}

def resolve_model_id(raw_model_id: str) -> str:
    """将别名解析为真实的 Ollama/Model ID"""
    return MODEL_ALIAS_MAP.get(raw_model_id, raw_model_id)


# --- 数据类 (内部使用，兼容 KnowledgeLoader) ---
from dataclasses import dataclass

@dataclass
class ExpertConfig:
    """专家配置数据类 (内部使用)"""
    id: str
    name: str
    role: str
    system_prompt: str = ""
    model_id: str = "qwen3.6:35b-a3b-q8_0"
    knowledge_dir: str = ""
    top_k: int = 5


# --- 专家工厂 ---
class ExpertFactory:
    """专家 Agent 工厂：根据配置创建配置好知识库和技能的 Agent"""

    @staticmethod
    def create_agent(config: Any, kb: Any) -> Any:
        """创建专家 Agent

        Args:
            config: 专家配置 (应包含 id, name, role, requires_skills)
            kb: KnowledgeHub 实例
        """
        from agno.agent import Agent
        from agno.models.ollama import Ollama

        # 1. 基础系统提示词
        sys_prompt = getattr(config, "system_prompt", "") or f"你是 {getattr(config, 'name', '专家')}。"
        
        # 2. 技能注入 (SKILL.md 激活)
        skill_content = ""
        skills = getattr(config, "requires_skills", [])
        if hasattr(kb, "inject_skill") and skills:
            for skill_id in skills:
                # 技能注入到临时上下文
                context = {}
                kb.inject_skill(skill_id, context)
                if "injected_skills" in context:
                    skill_content += f"\n\n### 核心技能: {skill_id}\n{context['injected_skills']}\n"

        # 3. 构建最终指令
        final_instructions = [
            sys_prompt,
            "基于知识库回答，客观专业。",
        ]
        if skill_content:
            final_instructions.append(f"你必须严格遵循以下专业技能要求：\n{skill_content}")

        # 4. 知识库挂载
        agent_kb = None
        from agno.knowledge.agent import AgentKnowledge
        if kb and AgentKnowledge:
            try:
                # 确保传入的是 ChromaDb 实例而非 KnowledgeHub
                db_instance = kb if not hasattr(kb, "load_expert_knowledge") else kb.load_expert_knowledge(config.id)
                top_k = getattr(config, "top_k", 5)
                agent_kb = AgentKnowledge(vector_db=db_instance, num_documents=top_k)
            except Exception:
                pass

        return Agent(
            name=getattr(config, "name", "Expert"),
            model=Ollama(id=getattr(config, "model", "qwen3.6:35b-a3b-q8_0")),
            instructions=final_instructions,
            knowledge=agent_kb,
        )

