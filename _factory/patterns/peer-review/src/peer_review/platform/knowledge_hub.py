# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-16 13:30:00 CST
"""KnowledgeHub: 知识统一接口（新架构 v1.1.0 纯 ChromaDB + LlamaIndex 实现）

职责：
- 直接使用 ChromaDB + LlamaIndex（不再依赖旧 Agno）
- 实现 collection 存在性检查 + VERSION 版本控制（去重）
- 为 LangGraph 节点提供知识检索
- 注入 SKILL.md 技能到 Agent 上下文
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    import chromadb
    from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core.storage.storage_context import StorageContext
    from llama_index.embeddings.ollama import OllamaEmbedding
except ImportError:
    chromadb = None
    SimpleDirectoryReader = None
    VectorStoreIndex = None
    ChromaVectorStore = None
    StorageContext = None
    OllamaEmbedding = None

# 默认本地 embedding（与 models.yaml 中的 embedding 条目对应）
DEFAULT_EMBED_MODEL = "bge-m3"
DEFAULT_OLLAMA_BASE = "http://localhost:11434"

from rich.console import Console
console = Console()


class KnowledgeHub:
    """知识统一接口（新架构）"""

    def __init__(
        self,
        knowledge_root: Path | str = "_factory/experts",
        skills_root: Path | str = "_factory/skills",
        persist_dir: str = "runtime/chroma_data",
    ):
        self.knowledge_root = Path(knowledge_root)
        self.skills_root = Path(skills_root)
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._indexes: dict[str, Any] = {}

    def _get_client(self):
        if chromadb is None:
            return None
        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        return self._client

    def _get_version(self, expert_dir: Path) -> str:
        """计算知识目录版本（文件 mtime + size 哈希）"""
        if not expert_dir.exists():
            return "empty"
        hasher = hashlib.md5()
        for p in sorted(expert_dir.rglob("*")):
            if p.is_file():
                stat = p.stat()
                hasher.update(f"{p.relative_to(expert_dir)}:{stat.st_mtime}:{stat.st_size}".encode())
        return hasher.hexdigest()[:12]

    def load_expert_knowledge(self, expert_id: str) -> Any | None:
        """加载或构建专家知识库（带去重 + VERSION 检查）"""
        if SimpleDirectoryReader is None or VectorStoreIndex is None or chromadb is None:
            console.print("[yellow]⚠️ LlamaIndex/ChromaDB 未安装，跳过知识库[/yellow]")
            return None

        expert_dir = self.knowledge_root / f"{expert_id}.expert" / "knowledge"
        if not expert_dir.exists() or not any(expert_dir.iterdir()):
            return None

        client = self._get_client()
        if client is None:
            return None

        current_version = self._get_version(expert_dir)
        collection_name = expert_id

        # 去重检查
        try:
            collections = [c.name for c in client.list_collections()]
            if collection_name in collections:
                col = client.get_collection(collection_name)
                stored_version = col.metadata.get("knowledge_version") if col.metadata else None
                if stored_version == current_version:
                    console.print(f"📦 复用专家 {expert_id} 知识库缓存 (版本 {current_version})")
                    # 直接返回已存在的 index
                    if expert_id in self._indexes:
                        return self._indexes[expert_id]
                    # 重建轻量 index 句柄
                    vector_store = ChromaVectorStore(chroma_collection=col)
                    storage_context = StorageContext.from_defaults(vector_store=vector_store)
                    index = VectorStoreIndex.from_vector_store(
                        vector_store, storage_context=storage_context
                    )
                    self._indexes[expert_id] = index
                    return index
                else:
                    console.print(f"📚 专家 {expert_id} 知识版本变化，重建索引...")
                    client.delete_collection(collection_name)
        except Exception:
            pass

        # 构建新索引
        console.print(f"📚 正在构建专家 {expert_id} 向量索引...")
        try:
            docs = SimpleDirectoryReader(input_dir=str(expert_dir)).load_data()
            # 强制删除已存在 collection（避免残留）
            try:
                client.delete_collection(collection_name)
            except Exception:
                pass
            chroma_collection = client.create_collection(
                name=collection_name,
                metadata={"knowledge_version": current_version, "built_at": str(__import__("datetime").datetime.now())}
            )
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # 使用本地 Ollama embedding（避免 OpenAI 依赖）
            embed_model = None
            if OllamaEmbedding is not None:
                try:
                    embed_model = OllamaEmbedding(
                        model_name=DEFAULT_EMBED_MODEL,
                        base_url=DEFAULT_OLLAMA_BASE,
                    )
                except Exception as e:
                    console.print(f"[dim]⚠️ OllamaEmbedding 初始化失败: {e}，尝试默认[/dim]")

            if embed_model:
                index = VectorStoreIndex.from_documents(
                    docs, storage_context=storage_context, embed_model=embed_model
                )
            else:
                index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)

            self._indexes[expert_id] = index
            console.print(f"✅ 专家 {expert_id} 索引构建完成 ({len(docs)} 文档, 版本 {current_version})")
            return index
        except Exception as e:
            console.print(f"[yellow]⚠️ [{expert_id}] 索引构建失败: {e}[/yellow]")
            return None

    def search(self, expert_id: str, query: str, top_k: int = 5) -> list[str]:
        """检索专家知识库，返回文本片段"""
        index = self.load_expert_knowledge(expert_id)
        if index is None:
            return []
        try:
            retriever = index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            results = []
            for node in nodes:
                text = getattr(node, "text", "") or getattr(node, "node", {}).get("text", str(node))
                if text:
                    results.append(text[:800])  # 截断避免 prompt 爆炸
            return results
        except Exception as e:
            console.print(f"[dim]知识检索失败: {e}[/dim]")
            return []

    def inject_skill(self, skill_id: str, context: dict[str, Any]) -> None:
        """将 SKILL.md 技能文件内容注入上下文"""
        skill_path = self.skills_root / f"{skill_id}.skill.md"
        if skill_path.exists():
            context["injected_skills"] = skill_path.read_text(encoding="utf-8")
