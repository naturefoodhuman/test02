<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 23:55:00 CST
-->

# SETUP GUIDE —— 真机增强组件安装指南（M1 Max / macOS）

> 针对 Ingestion(MinerU/FunASR) 与取数(browser-use) 的真机安装。
> 你终端遇到的：图片/PDF 是扫描件→需 MinerU；FunASR 报 No module named 'torch'→需补 torch。

---

## 一、MinerU 安装（OCR：扫描件 PDF / 图片，中文必备）

> 你的检验报告.jpg、血常规.pdf 是**扫描/图片版**（无文本层），MarkItDown 提不出字，必须 MinerU OCR。
> M1 Max 走 MPS/CPU（无 CUDA）。Python 需 3.10–3.12（⚠️ 不要用 3.13）。

### 推荐：独立隔离环境装（避免污染你现有 .venv）
```bash
# 1) 建一个独立目录和 venv（Python 3.10~3.12）
mkdir -p ~/mineru_env && cd ~/mineru_env
uv venv --python 3.12
source .venv/bin/activate

# 2) 用 ModelScope 源（国内快、稳）
export MINERU_MODEL_SOURCE=modelscope

# 3) 装 MinerU（含全部功能；国内镜像）
brew install libmagic            # 缺它会报 magic 相关错误
uv pip install -U "mineru[core]" -i https://mirrors.aliyun.com/pypi/simple

# 4) 下载模型权重（从 ModelScope）
mineru-models-download -s modelscope -m all

# 5) macOS 必加：避免 fork 安全警告
echo 'export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES' >> ~/.zshrc
export PYTORCH_ENABLE_MPS_FALLBACK=1   # MPS 不支持的算子回退 CPU
```

### 验证 MinerU
```bash
mineru -p ~/forge_test_data/血常规补充.pdf -o ~/mineru_out --source local
# 看 ~/mineru_out 下是否生成了 markdown（含 OCR 出的文字）
```
- ⚠️ M1 上 MinerU 较慢（纯 CPU/MPS，公式识别在 MPS 可能不稳，会自动回退 CPU），耐心等。
- ⚠️ 若 `device-mode` 想强制：编辑 `~/mineru.json` 设 `"device-mode": "mps"`（或 cpu 更稳）。

### 让工厂 Ingestion 用上 MinerU（两种方式）
- **方式A（最简单，推荐）**：直接用 MinerU CLI 把扫描件转好，再把输出喂给后续流程。
- **方式B（集成）**：在装了 mineru 的那个环境里跑 ingestion CLI；
  我们的 PdfProcessor/ImageProcessor 会检测到 mineru 并提示用 CLI（见下"已知限制"）。

### 已知限制（诚实告知）
- MinerU 的 SDK 在不同版本 API 差异大，我们的 processors.py 对 MinerU 默认**提示走 CLI**（最稳）。
- 即：`ingestion` 检测到 mineru 时会建议你 `mineru -p <file> -o <out>`，而不是 SDK 直调。
- 后续若你确定了 MinerU 版本，我可以把 SDK 直调接进去（告诉我 `mineru --version`）。

---

## 二、FunASR 修复（你的报错：No module named 'torch'）

FunASR 依赖 PyTorch，但没自动装。补装即可（M1 用 MPS/CPU 版）：
```bash
# 在装了 funasr 的那个环境（你的 ~/.venv）里：
source ~/.venv/bin/activate
uv pip install torch torchaudio -i https://mirrors.aliyun.com/pypi/simple
# 验证 MPS 可用
python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```
然后重跑录音转写：
```bash
bash _factory/patterns/ingestion-pipeline/verify-real.sh ~/forge_test_data
```
- ⚠️ FunASR 首次运行会**下载模型**（paraformer-zh + cam++ 说话人分离等），需等待。
- ⚠️ M1 上长录音较慢（CPU/MPS），隐私优先于速度。

---

## 三、browser-use 接什么本地模型？如何切 GLM？

### 结论：本地模型选型（你已有的够用）
浏览器 Agent 对模型的**指令遵循 + 工具调用**要求高，参数太小不行。社区与你现有资源结合：

| 选项 | 模型 | 评价 |
|---|---|---|
| **本地最佳（你已有）** | `qwen3.6:35b-a3b-q8_0`（你的 local/primary） | ✅ 35B MoE，工具调用强，浏览器 Agent 本地首选 |
| 本地备选 | `qwen3:14b` | 🟡 能跑但多步骤任务成功率明显低于 35b |
| 本地编程向 | `qwen3-coder-next` | 🟡 偏代码，浏览器任务不一定更好 |
| **云端最佳** | GLM（你的 cloud/glm-primary） | ✅ 复杂页面/多步骤明显更稳，建议关键任务用它 |

> 经验：浏览器 Agent **本地 14B 常翻车、35B 勉强、GLM/商业模型最稳**。
> 建议：**默认 GLM**（成功率优先，符合你"落地优先"），省成本时切本地 35b。

### 关键：全部走你的 LiteLLM 网关，切换=改一个名字
browser-use 不直连模型，而是走你已搭好的 LiteLLM 网关（localhost:4000）。
切换模型只改 `--bu-model` 一个参数：
```bash
# 用 GLM（默认，最稳）
python -m acquisition.cli "张三" --l2          # 默认 cloud/glm-primary

# 切本地 35b（零成本）
python -m acquisition.cli "张三" --l2 --bu-model local/primary

# 切本地 14b（更快但弱）
python -m acquisition.cli "张三" --l2 --bu-model local/fallback
```
（`--bu-model` 选项在 data-acquisition CLI 已支持，见下方补丁。）

### 安装 browser-use
```bash
source ~/.venv/bin/activate
uv pip install browser-use playwright -i https://mirrors.aliyun.com/pypi/simple
playwright install chromium
# 启动 GLM 网关（另一个终端）
bash _infra/start-litellm.sh
```

---

## 四、安装优先级建议（按你的真实需求）
1. **FunASR 补 torch**（一行命令，立刻能转写催收录音）← 最快见效
2. **MinerU**（你的资料多是扫描件/图片，不装就读不出内容）← 必须
3. **browser-use**（要自动化查官方渠道时再装）← 按需

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-11 23:55:00 | 初版：MinerU(M1)/FunASR(torch)/browser-use(模型选型+GLM切换)安装指南 | Claude Sonnet 4.5 |
