# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 16:30:00 CST
"""专家工厂模块

从 orchestrator.py 提取，单一职责：根据配置创建 Agent 实例。
"""

from __future__ import annotations

from typing import Any

# --- 防御性导入 ---
try:
    from agno.agent import Agent
    from agno.models.ollama import Ollama
except ImportError as e:
    from rich.console import Console
    Console().print(f"[bold red]❌ Agno 导入失败: {e}[/bold red]")
    raise

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
    """专家 Agent 工厂：根据配置创建配置好知识库的 Agent"""

    @staticmethod
    def create_agent(config: ExpertConfig, kb: Any) -> Agent:
        """创建专家 Agent

        Args:
            config: 专家配置
            kb: 知识库实例 (ChromaDb)

        Returns:
            配置完成的 Agent 实例
        """
        sys_prompt = config.system_prompt if config.system_prompt else f"你是 {config.name}。"
        agent_kb = None
        if kb and AgentKnowledge:
            try:
                agent_kb = AgentKnowledge(vector_db=kb, num_documents=config.top_k)
            except Exception:
                pass

        return Agent(
            name=config.name,
            model=Ollama(id=config.model_id),
            instructions=[sys_prompt, "基于知识库回答，客观专业。"],
            knowledge=agent_kb,
        )