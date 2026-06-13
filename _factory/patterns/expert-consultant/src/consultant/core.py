# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-13 14:30:00 CST
"""专家咨询核心逻辑 (FB-12)。

实现 RAG (检索增强生成)：
1. 索引：读取专家知识库，分段，生成向量并保存。
2. 咨询：搜索相关片段 -> 组装 Prompt -> 调 R1 推理。
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass

import urllib.request
import json

@dataclass
class Chunk:
    text: str
    source: str
    vector: list[float] | None = None

class ExpertConsultant:
    def __init__(self, expert_name: str, base_dir: str = "_factory/experts"):
        self.expert_dir = os.path.join(base_dir, f"{expert_name}.expert")
        self.knowledge_dir = os.path.join(self.expert_dir, "knowledge")
        self.index_path = os.path.join(self.expert_dir, "index.json")
        self.config = self._load_config()
        self.chunks: list[Chunk] = []
        self.gateway_url = "http://localhost:4000/v1"

    def _load_config(self):
        import yaml
        cfg_path = os.path.join(self.expert_dir, "expert.yaml")
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def index(self, force: bool = False):
        """扫描知识库并建立索引。"""
        if os.path.exists(self.index_path) and not force:
            print(f"[INFO] 索引已存在: {self.index_path}")
            return

        all_chunks = []
        for root, _, files in os.walk(self.knowledge_dir):
            for f in files:
                if f.endswith(".md") and not f.startswith("_"):
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8") as f_in:
                        content = f_in.read()
                        # 简单分段：按标题或固定长度
                        segments = re.split(r'\n(?=#{1,3} )', content)
                        for seg in segments:
                            if len(seg.strip()) > 50:
                                all_chunks.append(Chunk(text=seg.strip(), source=f))

        print(f"[INFO] 开始生成向量，共 {len(all_chunks)} 段...")
        for i, chunk in enumerate(all_chunks):
            chunk.vector = self._get_embedding(chunk.text)
            if i % 10 == 0:
                print(f"  进度: {i}/{len(all_chunks)}")

        # 保存索引
        with open(self.index_path, "w", encoding="utf-8") as f_out:
            json.dump([{"text": c.text, "source": c.source, "vector": c.vector} for c in all_chunks], f_out, ensure_ascii=False)
        print(f"[SUCCESS] 索引已保存至: {self.index_path}")

    def _get_embedding(self, text: str) -> list[float]:
        """通过网关调用 local/embedding。"""
        body = json.dumps({"input": text, "model": "local/embedding"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.gateway_url}/embeddings", data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer any"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.loads(r.read().decode("utf-8"))
                return res["data"][0]["embedding"]
        except Exception as e:
            # 降级：返回随机向量（仅用于测试，真实环境需网关开启）
            print(f"[WARN] 向量生成失败: {e}")
            return [0.0] * 1024

    def ask(self, query: str, top_k: int = 3) -> str:
        """检索并回答。"""
        if not self.chunks:
            self._load_index()

        query_vec = self._get_embedding(query)
        # 计算余弦相似度并排序
        scored = []
        for c in self.chunks:
            sim = self._cosine_similarity(query_vec, c.vector)
            scored.append((sim, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        
        context = "\n---\n".join([f"[来源: {c.source}]\n{c.text}" for _, c in scored[:top_k]])
        
        model = self.config.get("routing", {}).get("primary_reasoning", "local/r1")
        identity = self.config.get("role", {}).get("identity", "专家")
        expertise = ", ".join(self.config.get("role", {}).get("expertise", []))
        
        system_prompt = (
            f"你是一位{identity}。你的专长领域包括: {expertise}。\n"
            f"请基于以下检索到的【参考资料】回答用户问题。如果资料中没有相关信息，请诚实说明。\n"
            f"请保持专业、严谨的语气，并给出具体的博弈建议。\n\n"
            f"【参考资料】:\n{context}"
        )
        
        print(f"⏳ 正在请教专家 ({model})...")
        return self._chat(query, system_prompt, model)

    def _load_index(self):
        if not os.path.exists(self.index_path):
            self.index()
        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.chunks = [Chunk(text=d["text"], source=d["source"], vector=d["vector"]) for d in data]

    def _cosine_similarity(self, v1, v2):
        if not v1 or not v2 or len(v1) != len(v2): return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        return dot / (mag1 * mag2) if mag1 * mag2 > 0 else 0.0

    def _chat(self, prompt: str, system: str, model: str) -> str:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.gateway_url}/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer any"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                res = json.loads(r.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[ERROR] 专家咨询失败: {e}"
