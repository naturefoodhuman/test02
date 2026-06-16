# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-16 10:00:00 CST
"""FORGE 工厂：Mac M1 Max (64G) 部署与内存管理指南

本指南旨在确保在有限的统一内存下，最大化利用 MTPLX, MLX, Ollama 和 Llama.cpp 的性能，同时避免 OOM 崩溃。
"""

## 1. 硬件基准 (Hardware Baseline)
- **设备**: MacBook Pro M1 Max
- **内存**: 64GB Unified Memory
- **可用内存预估**: 操作系统及基础应用占用 ~8-12GB $\rightarrow$ 可用约 52GB。

## 2. 模型内存占用矩阵 (Memory Matrix)

| 模型 | 框架 | 预计占用 | 优先级 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| Qwen3.6-27B-MTPLX | MLX | ~20 GB | P0 | 主大脑 / 编码 |
| Gemma4-MTPLX | MLX | ~16 GB | P1 | 独立评审 |
| Qwopus3.6-35B (Q8_0) | Llama.cpp | ~36 GB | P1 | 深度评审 |
| DeepSeek-R1 32B | Ollama | ~20 GB | P1 | 逻辑推理 |

**结论**: $\text{Total (All)} \approx 92\text{GB} > 64\text{GB}$。**严禁所有模型同时加载。**

## 3. 部署路径标准 (Path Standards)
- **工作目录**: `~/LocalAI/servers`
- **MLX 权重**: `~/LocalAI/hf-cache/hub/`
- **GGUF 权重**: `~/LocalAI/gguf-models/`

## 4. 部署执行命令 (Step-by-Step)

### A. 启动主大脑 (Port 8080)
```bash
cd ~/LocalAI/servers
uv run python -m mlx_lm.server \
  --model ~/LocalAI/hf-cache/hub/models--Youssofal--Qwen3.6-27B-MTPLX-Optimized-Quality \
  --port 8080
```

### B. 启动评审模型 (Port 8082)
```bash
cd ~/LocalAI/servers
uv run python -m mlx_lm.server \
  --model ~/LocalAI/hf-cache/hub/models--Youssofal--Gemma4-MTPLX-Optimized-Quality \
  --port 8082
```

### C. 启动 GGUF 模型 (Port 8081)
```bash
cd ~/LocalAI/servers
~/LocalAI/servers/llama-server \
  --model ~/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf \
  --host 127.0.0.1 \
  --port 8081 \
  --n_gpu_layers -1 \
  --ctx_size 9000 \
  --threads 8
```

## 5. 内存调度测试方案 (Sequential Test Plan)

由于不能全部并行，请采用 **【加载 $\rightarrow$ 测试 $\rightarrow$ 卸载】** 循环。

### 第一阶段：主大脑 + 轻量评审 (MLX Combo)
1. 启动 **Port 8080** (Qwen) $\rightarrow$ 启动 **Port 8082** (Gemma4)。
2. 执行 `uv run python -m forge.cli --root . eval --plans mtplx-hybrid`。
3. 关闭 8080 和 8082。

### 第二阶段：主大脑 + 深度评审 (MLX + Llama.cpp)
1. 启动 **Port 8080** (Qwen) $\rightarrow$ 启动 **Port 8081** (Qwopus)。
2. 执行 `uv run python -m forge.cli --root . eval --plans deep-review`。
3. 关闭 8080 和 8081。

### 第三阶段：主大脑 + 逻辑推理 (MLX + Ollama)
1. 启动 **Port 8080** (Qwen) $\rightarrow$ 启动 **Ollama** (DeepSeek-R1)。
2. 执行 `uv run python -m forge.cli --root . eval --plans r1-hybrid`。
3. 关闭 8080 和 Ollama。
