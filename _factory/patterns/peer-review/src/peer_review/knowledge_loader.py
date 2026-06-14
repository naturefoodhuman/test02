# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 16:40:00 CST
"""知识加载器模块

从 orchestrator.py 提取，单一职责：加载专家知识库 (ChromaDB)，实现去重机制。

核心改进：
- Collection 存在性检查：避免每次启动重建索引
- 版本标记机制：知识库版本变更时自动重建
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

# --- 防御性导入 ---
SimpleDirectoryReader = None
try:
    from llama_index.core.readers import SimpleDirectoryReader
except ImportError:
    try:
        from llama_index.readers.file import SimpleDirectoryReader
    except ImportError:
        pass

ChromaDb = None
try:
    from agno.vectordb.chromadb import ChromaDb
except ImportError:
    try:
        from agno.vectordb.chroma import ChromaDb
    except ImportError:
        pass

from rich.console import Console
console = Console()


class KnowledgeLoader:
    """知识加载器：管理 ChromaDB collection 生命周期，实现去重"""

    _instances: dict[str, Any] = {}
    _version_cache: dict[str, str] = {}

    @classmethod
    def load_knowledge(
        cls,
        config: "ExpertConfig",
        persist_dir: str = "runtime/chroma_data"
    ) -> Optional[Any]:
        """加载或构建专家知识库

        Args:
            config: 专家配置 (需包含 id, knowledge_dir)
            persist_dir: ChromaDB 持久化目录

        Returns:
            ChromaDb 实例，或 None (加载失败/无知识源)
        """
        if SimpleDirectoryReader is None or ChromaDb is None:
            return None

        expert_id = config.id
        if not expert_id or expert_id.startswith("_"):
            return None

        # 缓存命中：返回已加载实例
        if expert_id in cls._instances:
            console.print(f"📦 复用专家 [{expert_id}] 知识库缓存")
            return cls._instances[expert_id]

        source_dir = Path(config.knowledge_dir)
        if not source_dir.exists() or not any(source_dir.iterdir()):
            console.print(f"[dim]📭 专家 [{expert_id}] 无知识源目录: {source_dir}[/dim]")
            return None

        # 去重检查：Collection 是否已存在且版本一致
        if cls._is_index_current(expert_id, persist_dir, source_dir):
            console.print(f"✅ 专家 [{expert_id}] 索引已存在且版本一致，跳过构建")
            db = ChromaDb(path=persist_dir, collection=expert_id)
            cls._instances[expert_id] = db
            return db

        # 需要构建/重建索引
        console.print(f"📚 正在构建专家 [{expert_id}] 向量索引...")
        try:
            docs = SimpleDirectoryReader(input_dir=str(source_dir)).load_data()
            db = ChromaDb(path=persist_dir, collection=expert_id)
            if hasattr(db, 'load_documents'):
                db.load_documents(documents=docs, upsert=True)

            # 记录版本
            cls._update_version(expert_id, source_dir)

            cls._instances[expert_id] = db
            console.print(f"✅ 专家 [{expert_id}] 索引构建完成 ({len(docs)} 文档)")
            return db

        except Exception as e:
            console.print(f"[yellow]⚠️ [{expert_id}] 索引构建失败: {e}[/yellow]")
            return None

    @classmethod
    def _is_index_current(cls, expert_id: str, persist_dir: str, source_dir: Path) -> bool:
        """检查索引是否存在且版本与磁盘一致

        双重检查：
        1. ChromaDB collection 是否存在
        2. 版本标记是否与知识源目录一致
        """
        # 1. 检查 collection 是否存在
        try:
            db = ChromaDb(path=persist_dir, collection=expert_id)
            collections = db.client.list_collections() if hasattr(db, 'client') else []
            collection_names = [c.name for c in collections] if collections else []
            if expert_id not in collection_names:
                return False
        except Exception:
            return False

        # 2. 检查版本一致性
        current_version = cls._get_source_version(source_dir)
        cached_version = cls._version_cache.get(expert_id)

        if cached_version and cached_version == current_version:
            return True

        # 从 ChromaDB metadata 读取版本 (如果支持)
        try:
            collection = db.client.get_collection(expert_id) if hasattr(db, 'client') else None
            if collection:
                metadata = collection.metadata or {}
                stored_version = metadata.get("knowledge_version")
                if stored_version and stored_version == current_version:
                    cls._version_cache[expert_id] = current_version
                    return True
        except Exception:
            pass

        return False

    @classmethod
    def _get_source_version(cls, source_dir: Path) -> str:
        """计算知识源目录的版本标识 (基于文件 mtime + size)"""
        import hashlib
        hasher = hashlib.md5()
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                stat = file_path.stat()
                hasher.update(f"{file_path.relative_to(source_dir)}:{stat.st_mtime}:{stat.st_size}".encode())
        return hasher.hexdigest()[:16]

    @classmethod
    def _update_version(cls, expert_id: str, source_dir: Path) -> None:
        """更新版本缓存，并写入 ChromaDB metadata"""
        version = cls._get_source_version(source_dir)
        cls._version_cache[expert_id] = version

        # 尝试写入 ChromaDB collection metadata
        try:
            from agno.vectordb.chromadb import ChromaDb as _ChromaDb
            db = _ChromaDb(path="runtime/chroma_data", collection=expert_id)
            if hasattr(db, 'client'):
                collection = db.client.get_collection(expert_id)
                if collection:
                    collection.modify(metadata={"knowledge_version": version})
        except Exception:
            pass  # metadata 写入失败不阻塞主流程

    @classmethod
    def clear_cache(cls) -> None:
        """清空缓存 (用于测试或强制重建)"""
        cls._instances.clear()
        cls._version_cache.clear()