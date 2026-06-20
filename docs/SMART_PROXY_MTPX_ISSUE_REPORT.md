# Smart Proxy + MTPLX 转发问题完整报告

**创建时间**：2026-06-20  
**问题状态**：进行中（已尝试多次修复仍存在超时）  
**目标**：让 Smart Proxy (4000) 稳定转发请求到 MTPLX (8080) 并获得真实模型响应

---

## 1. 问题描述

### 1.1 核心现象
- Smart Proxy 启动后能成功拉起 MTPLX 模型（日志显示 `HTTP/1.1 200 OK`）
- 但 benchmark / LangGraph 调用时频繁出现：
  - `timed out`
  - `HTTP Error 400: Bad Request`
  - `Connection refused`
  - 最终 `❌ 后端调用失败: timed out`
- 即使模型已完全加载并监听 8080，请求仍然超时（最长等待 900 秒）

### 1.2 环境信息
- **硬件**：MacBook Pro M1 Max 64GB
- **模型后端**：MTPLX (Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality)
- **端口映射**：
  - 4000 → Smart Proxy（协议转换 + 按需加载）
  - 8080 → MTPLX Qwen 主大脑
- **调用链路**：LangGraph → peer_review/llm_client.py → Smart Proxy (4000) → MTPLX (8080)

---

## 2. 关键配置文件

### 2.1 `config/models.yaml`（部分）
```yaml
models:
  mtplx-qwen36-27b:
    display_name: "Qwen3.6-27B-MTPLX-Optimized (主大脑)"
    provider: mtplx
    backend: mtplx
    model_id: Qwen3.6-27B-MTPLX-Optimized-Quality
    base_url: http://localhost:4000/v1          # ← 必须经过 Smart Proxy
    type: local
    memory_required_gb: 20
```

### 2.2 `config/routing_plans.yaml`（default 方案）
```yaml
plans:
  default:
    nodes:
      primary_expert:
        model: mtplx-qwen36-27b
      reviewer_1:
        model: mtplx-gemma4
      consensus:
        model: mtplx-qwen36-27b
```

---

## 3. 核心代码文件

### 3.1 `_infra/smart_proxy.py`（当前版本）

**关键部分**：

```python
REAL_ID_MAP = {
    8080: "mtplx-qwen36-27b-optimized-quality",   # ← 已修正为 MTPLX 实际 ID
    ...
}

http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0),
    limits=httpx.Limits(max_keepalive_connections=5)
)

# 转发逻辑（已添加重试）
for attempt in range(3):
    try:
        resp = await http_client.post(target_url, json=forward_payload)
        ...
    except Exception as e:
        ...
        await asyncio.sleep(2)
```

**已尝试的修改**：
- 将 `REAL_ID_MAP` 从长 display_name 改为短 model id
- 超时从 300s 提升到 600s
- 增加 3 次重试机制
- 添加 `top_p`、`max_tokens` 等参数

### 3.2 `peer_review/llm_client.py`（LiteLLMBackend）

```python
class LiteLLMBackend(LLMBackend):
    def chat(self, model_cfg, messages):
        ...
        with urllib.request.urlopen(req, timeout=600) as r:   # ← 已提升到 600s
            ...
```

**已尝试的修改**：
- urllib timeout 从 300s → 600s

### 3.3 `scripts/benchmark_test.py`

```python
def run_benchmark(...):
    state = run_langgraph_review(
        case_query,
        project_root=root,
        plan_id=plan,
        privacy_approved=True
    )
```

---

## 4. 已尝试的解决方案（按时间顺序）

### 4.1 模型启动与清理
- 使用 `forge-start.sh`（自检 + 立即卸载）
- 手动 `uv run mtplx quickstart --port 8080`
- `pkill -9 -f "mtplx.*8080"` 清理残留进程
- `bash scripts/purge_vram.sh` 强制释放显存

### 4.2 Smart Proxy 修复
- 修改 `REAL_ID_MAP` 使用正确 model id
- 提升 `httpx` 超时到 600s + 3次重试
- 增加 `top_p`、`max_tokens` 参数
- 降低连接池大小

### 4.3 LLM Client 修复
- `LiteLLMBackend` urllib timeout 提升到 600s

### 4.4 诊断工具
- 创建 `scripts/diagnose_proxy.sh`
- 创建 `scripts/test_single_plan.py`（简化测试）

### 4.5 其他尝试
- 直接绕过 Smart Proxy（临时把 base_url 指向 8080）
- 只运行 `default` 方案（减少并行压力）
- 前台运行 Smart Proxy 观察日志

---

## 5. 当前日志证据

### 5.1 Smart Proxy 日志（部分）
```
2026-06-20 15:20:41,293 [INFO]: ✅ 后端 8080 响应就绪
2026-06-20 15:20:46,342 [INFO]: HTTP Request: POST ... "HTTP/1.1 400 Bad Request"
2026-06-20 15:20:47,998 [INFO]: HTTP Request: POST ... "HTTP/1.1 200 OK"
2026-06-20 15:39:22,661 [ERROR]: ❌ 转发失败:
2026-06-20 15:44:22,664 [ERROR]: ❌ 转发失败:
```

### 5.2 Benchmark 输出
```
❌ 后端调用失败: timed out
✅ 完成: 耗时 900.0s, 分歧度 0.0
```

### 5.3 模型状态
- MTPLX 已成功启动并输出 `MTPLX is ready.`
- 端口 8080 正常监听
- 但 Smart Proxy 转发后经常超时

---

## 6. 可能的原因分析（供参考）

1. **MTPLX 长思考模式**：Qwen3.6-27B 在复杂债务案件上思考时间极长，超过 600s 仍未返回。
2. **协议不兼容**：MTPLX 对某些请求字段要求严格（即使已添加 top_p/max_tokens）。
3. **Smart Proxy 连接池/Keep-Alive 问题**：多次转发后连接失效。
4. **LangGraph 节点超时**：即使 Smart Proxy 超时设置再高，LangGraph 内部可能有更短的超时。
5. **AppleScript 拉起模型不稳定**：模型有时被系统杀掉。

---

## 7. 建议进一步尝试的方向（供其他 AI 参考）

1. **在 MTPLX 启动命令中添加** `--reasoning-effort low` 或 `--max-tokens 1024`
2. **Smart Proxy 中增加** `stream=True` 支持 + 流式转发
3. **在 llm_client.py 的 MTPLXBackend 中** 直接调用 8080（绕过 Smart Proxy 作为对比）
4. **增加更详细的请求/响应日志**（打印完整 payload）
5. **尝试使用 LiteLLM 作为中间层**（`litellm --model mtplx/...`）
6. **降低模型温度**（`temperature=0.1`）减少思考时间
7. **使用更短的测试 case**（只发 “你好”）验证基础连通性

---

## 8. 相关文件清单

- `_infra/smart_proxy.py`
- `_factory/patterns/peer-review/src/peer_review/llm_client.py`
- `config/models.yaml`
- `config/routing_plans.yaml`
- `scripts/benchmark_test.py`
- `scripts/forge-start.sh`
- `scripts/purge_vram.sh`
- `forge_diagnose_*.log`（诊断日志）

---

**希望其他 AI 能基于以上完整信息给出新的解决方案。**