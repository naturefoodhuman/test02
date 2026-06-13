<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-13 15:40:00
-->

# HANDOFF —— 接力交接文档（最终版）

> 目标：任何 Agent 5 分钟内接手并继续开发。

---

## 1. 项目定位
本产品为 **AI 项目孵化工厂 (FORGE Factory)**。
试点项目 `debt-collection` 是用来压测工厂能力的。

## 2. 运行环境与路径
**绝对路径：** `/Users/naturist/MusicProject/AI-Project-Incubation-Factory`

### 虚拟环境 (Venv) 矩阵：
1. **主工厂环境**：位于根目录 `.venv` (建议创建)。
   - 用途：运行网关 (start-litellm.sh)、专家咨询 (consultant/cli.py)。
2. **MinerU 专用环境**：位于 `projects/debt-collection/runtime/mineru_env`。
   - 用途：运行 PDF 深度解析。

### 模型矩阵 (Ollama)：
- `deepseek-r1:32b` (本地推理核心)
- `qwen3.6:35b-a3b-q8_0` (本地执行核心)
- `bge-m3` (本地向量检索)

## 3. 核心规则
- **R2 (反方评估)**：决策前调研主流方案，给出优劣对比。
- **R3 (保姆级指示)**：给老板的每条指令必须包含：终端编号、路径、虚拟环境状态、预期输出。
- **R7 (文件头规范)**：所有文件必须注明修改大模型和时间。

## 4. 操作 SOP
### 启动网关 (终端 A)
1. `cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory`
2. `source .venv/bin/activate`
3. `bash _infra/start-litellm.sh`

### 运行专家咨询 (终端 B)
1. `cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory`
2. `source .venv/bin/activate`
3. `export PYTHONPATH=$PYTHONPATH:$(pwd)/_factory/patterns/expert-consultant/src`
4. `python -m consultant.cli "你的法律问题"`

## 5. 常见排障
- **MinerU Hub 报错**：执行 `export MINERU_MODEL_SOURCE=modelscope`。
- **模块找不到**：检查 `PYTHONPATH` 是否包含 `src` 目录。
