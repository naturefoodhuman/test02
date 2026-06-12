<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 18:30:00 CST
-->
# 专家模板（_TEMPLATE.expert）

复制本目录为 `<name>.expert/`，填 expert.yaml + 用 ingestion 把知识灌入 knowledge/ + 维护 _gaps.md/_sources.yaml。
专家 = 角色画像 + 领域知识库(RAG) + 模型路由 + 更新机制。详见 docs/research/expert-system-design.md。
