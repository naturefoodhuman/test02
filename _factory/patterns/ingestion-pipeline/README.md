<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
-->

# Pattern：ingestion-pipeline（工厂通用资料整理能力 · FB-8）

> 工厂级通用能力：把本地多格式资料（PDF / 图片 / 通话录音 / Office / 文本）
> **统一转为结构化 Markdown + JSON**，供下游 RAG / 分析 / 台账消费。
> 满足老板要点6。**不只服务讨债项目，是所有项目可复用的地基能力。**

## 设计原则
- **核心零依赖**：只用标准库即可跑通调度+文本处理+落盘（本沙箱已验证 7 passed + CLI 实跑）。
- **优雅降级**：缺 MinerU/markitdown/funasr 时不报死，降级并提示真机装什么；装了自动升级效果。
- **统一输出**：所有来源 → 同一个 `StructuredDoc`（markdown + segments + meta + warnings）。
- **可扩展**：用抽象基类 `BaseProcessor` 定义处理器接口，加新格式只需加一个处理器。

## 选型（详见 docs/research/ingestion-tools-comparison.md）
| 类型 | 真机首选 | 备选/降级 |
|---|---|---|
| PDF/图片(中文复杂版面) | **MinerU** | markitdown → pypdf → 占位 |
| Office/多格式入口 | **MarkItDown**(MIT) | 占位 |
| 通话录音 | **FunASR**(本地/说话人分离) | 占位 |

## 用法
```bash
# 复制到项目或直接用
cd _factory/patterns/ingestion-pipeline
python -m pytest -q                      # 7 passed（沙箱核心逻辑）

# 真机增强（按需）
uv pip install -e ".[enhance]" -i https://pypi.tuna.tsinghua.edu.cn/simple
# 大模型类单独装：pip install funasr ；MinerU 见其官方文档

# 跑批量整理
python -m ingestion.cli ./我的资料目录 -o ./结构化输出
# 或装好后用命令：forge-ingest ./资料 -o ./out
```

## 输出
每个文件产出两份：
- `<name>.md`：结构化 Markdown（人读 + RAG 切分）
- `<name>.json`：机器可读（segments 带 kind/speaker/level/page 等），含 `warnings`（降级/质量提示）

## 与工厂其它能力的衔接
- 输出可直接喂给 `local/embedding`(bge-m3) 做向量化 → RAG。
- 录音的 `utterance` segment 带 speaker/start_ms（真机 FunASR），适合催收通话"谁说了什么"分析。

## 真机接入点（TODO，已在 processors.py 标注）
- PdfProcessor：接 MinerU CLI/SDK 输出填充 markdown+segments
- AudioProcessor：接 FunASR(AutoModel + spk_model) 填充 utterance segments
- ImageProcessor：接 MinerU/OCR

## 最后验证
- 2026-06-11：沙箱 `pytest` 7 passed；CLI 对 .md/.pdf/.wav 实跑通过（文本结构化，PDF/音频降级提示正确）。
