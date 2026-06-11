<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 18:10:00 CST
-->

# 工厂通用能力调研：本地资料整理（多格式 → 结构化）横向对比

> 来源：老板要点6——工厂需具备通用的本地资料整理能力（图片/PDF/通话录音 → 统一结构化）。
> 这是**工厂级通用能力**（KR-003 技能库 / KR-004 模式库候选），不只服务讨债项目。
> 目标格式：结构化 Markdown / JSON，便于下游 RAG、信息抽取、人工复核。

## 一、PDF / 文档 / 图片 → 结构化（文档类）

| 工具 | 出品 | 许可 | 中文/CJK | 表格 | 公式 | 输入格式 | 本地/Apple MPS | 选型结论 |
|---|---|---|---|---|---|---|---|---|
| **MinerU** | OpenDataLab(清华&上研所) | 代码友好，**模型含 AGPL** | ⭐⭐⭐⭐⭐ 强 | HTML 嵌入，复杂表格好 | UniMERNet，强 | PDF/Office/图片 | 推荐 GPU，可 CPU pipeline | **中文复杂版面首选** |
| **Marker** | Datalab | **GPL/研究许可，商用需授权** | ⭐⭐⭐⭐ | LLM 可优化复杂表格 | LaTeX，强 | PDF/DOCX/PPTX/EPUB | ✅ 支持 MPS | 速度最快，结构保真好 |
| **MarkItDown** | 微软 | **MIT（最宽松）** | ⭐⭐⭐ 一般 | 简单表格/可能丢样式 | 弱 | **最广**：PDF/Office/图片/音频/URL | ✅ 纯规则+可选 LLM | **多格式快速入口/轻量首选** |
| **Docling** | IBM | MIT | ⭐⭐⭐⭐ | 表格结构识别强 | 一般 | PDF/Office 等 | ✅ CPU 可跑 | RAG 管线友好(LangChain/LlamaIndex) |
| **Dolphin** | 字节 | MIT | ⭐⭐⭐⭐ | 复杂表格一般 | — | PDF/图片 | 本地 CLI | 布局要求高的场景 |
| PyMuPDF4LLM | — | AGPL/商业 | — | 一般 | — | 原生 PDF（非扫描）| ✅ CPU 极快 | 原生 PDF 最快、无 OCR |

### 文档类选型建议（给工厂）
- **默认主力 = MinerU**：中文友好、表格/公式强、可纯 CPU 跑（老板 M1 Max 无独显，走 `pipeline` 后端或 MPS）。⚠️ 模型 AGPL，**个人自用没问题**，未来若商用要注意。
- **轻量/多格式入口 = MarkItDown**：MIT 许可最干净，能吃 Office/图片/音频/URL，适合"先快速转成文本"。
- **组合策略**：MarkItDown 做"杂格式统一入口" + MinerU 做"复杂 PDF 精解析"。
- ⚠️ 通病：所有工具对**多级标题/章节顺序**识别都可能错乱，需保留"人工复核"环节。

## 二、通话录音 / 音频 → 文本（语音类）

| 工具 | 许可 | 中文精度 | 说话人分离 | 本地 | 选型结论 |
|---|---|---|---|---|---|
| **FunASR**（含 Paraformer/SenseVoice/Fun-ASR-Nano）| 开源免费 | ⭐⭐⭐⭐⭐ 最强 | ✅ 内置(cam++/spk_model) | ✅ 完全本地 | **中文通话录音首选** |
| Whisper (OpenAI) | MIT | ⭐⭐⭐⭐ | ❌ 需额外工具 | ✅ 本地 | 多语言强，中文略逊 |
| SenseVoice | 开源 | ⭐⭐⭐⭐⭐ | ✅(新版) | ✅ | 带情感/事件识别 |

### 语音类选型建议（给工厂）
- **默认 = FunASR**：中文最强、免费、**本地处理（隐私关键）**、内置说话人分离（讨债通话"谁说了什么"很重要）。
- 老板的本地已有 ASR 相关基础（Ollama 里有相关模型生态），FunASR 可 `pip install funasr` 独立装。
- ⚠️ M1 Max 无 CUDA，FunASR 在 Apple 上走 CPU/MPS，长录音较慢但可用；隐私优先于速度。

## 三、对工厂架构的建议（要点6 落地）

把"资料整理"做成工厂的**通用前置能力层**，而非每个项目重造轮子：
```
原始资料(图片/PDF/录音/Office)
   │
   ▼
[工厂通用 Ingestion 层]  ← 新增，建议做成 _factory/skills/ + 一个可复用 Pattern
   ├─ 文档 → MinerU / MarkItDown → 结构化 Markdown+JSON
   ├─ 录音 → FunASR(带说话人分离) → 带时间戳/说话人文本
   └─ 图片 → MinerU/OCR → 文本
   │
   ▼
统一结构化输出(Markdown/JSON) → 进入各项目的 RAG/分析/台账
```
- 建议产出物：`_factory/skills/data-ingestion.skill.md`（怎么做）+ `_factory/patterns/ingestion-pipeline/`（可运行脚手架）。
- 这正好用上工厂已配的 `local/embedding`（bge-m3）做后续向量化。

## 引用
- PDF 工具横向对比：CSDN 深度调研、themenonlab 2026、阿里云开发者社区 MinerU 实战。
- 语音：FunASR 官方 README、阿里云百炼 ASR 模型表、腾讯云开发者中文 ASR 对比。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-11 18:10:00 | 初版：文档类(MinerU/Marker/MarkItDown/Docling)+语音类(FunASR)横向对比与选型 | Claude Sonnet 4.5 |
