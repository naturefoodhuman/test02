<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
-->

---
skill_id: data-ingestion
name: 本地资料整理（多格式→结构化）
phase: [DISCOVERY, SPEC, BUILD]
load_when: "任何项目需要把本地 PDF/图片/录音/Office 整理成结构化数据时"
last_verified: 2026-06-11
version: 0.1
---

# 技能：本地资料整理（工厂通用能力 FB-8）

## 何时用
- 项目有一堆杂格式本地资料（合同 PDF、借据照片、通话录音、Excel 台账）需统一成结构化数据。

## 核心步骤
1. 用 `_factory/patterns/ingestion-pipeline`（复制或直接调用）。
2. `python -m ingestion.cli <资料目录> -o <输出>` → 得到每个文件的 `.md` + `.json`。
3. 真机按需装增强库：MinerU(中文PDF/图片)、markitdown(多格式)、funasr(录音+说话人)。
4. 输出的结构化 segments 喂给 `local/embedding`(bge-m3) 向量化 → 进 RAG/分析。
5. 检查每个 doc 的 `warnings`：若是"降级/占位"，说明该装对应库了。

## 检查清单
- [ ] 所有资料都转出了 .md + .json
- [ ] 关键文件没有停留在"降级"（该装的库已装）
- [ ] 录音的 utterance 带了 speaker（多人通话需说话人分离）

## 反模式
- 把原始 PDF/录音直接塞给 LLM（上下文爆炸、质量差）。
- 缺库就放弃——本 Pattern 支持降级，先跑通流程再增强。

## 输出物
- 结构化 Markdown + JSON（StructuredDoc），供下游 RAG/分析/台账。
