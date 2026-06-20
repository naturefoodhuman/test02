# Smart Proxy + MTPLX 长思考模型调用经验教训

**创建时间**：2026-06-20  
**版本**：v1.0  
**状态**：已验证成功

---

## 一、核心经验教训

### 1. 对长思考模型（27B+）必须使用 Streaming + Chunk 超时

**教训**：
- 单纯把总超时（timeout）从 300s 提到 600s/900s **无效**
- 27B 模型在复杂案件上可沉默思考 **5~15 分钟**（`mtplx_stream_silence`）
- **正确做法**：使用 `stream=True` + `read=None` + **chunk 级超时**（每收到新 token 就续命）

**最终方案**：
```python
CHUNK_IDLE_TIMEOUT = 600.0   # 10 分钟无新 token 才超时
TOTAL_HARD_LIMIT   = 14400.0 # 4 小时
```

### 2. MTPLX 必须使用启动日志中的短 Model ID

**教训**：
- `models.yaml` 里写 `Qwen3.6-27B-MTPLX-Optimized-Quality` 会导致 400 Bad Request
- **必须使用**启动日志中显示的短 ID：`mtplx-qwen36-27b-optimized-quality`

**正确映射**：
```python
REAL_ID_MAP = {
    8080: "mtplx-qwen36-27b-optimized-quality",
}
```

### 3. `urllib.request.urlopen` 不支持真正流式，必须改用 `httpx.stream`

**教训**：
- `urllib` 是阻塞式一次性读取，无法处理长思考模型的流式输出
- 必须使用 `httpx.Client().stream()` + `iter_lines()` 消费 SSE

### 4. Smart Proxy 需要字段白名单 + 自动拉起模型

**教训**：
- MTPLX 对某些字段严格校验（`tools:[]`、`response_format` 等）
- 必须实现 `ensure_server()` 自动拉起模型（AppleScript + 就绪探针）

### 5. 心跳保活是流式代理的必需品

**教训**：
- 如果上游 30~60 秒不输出 token，中间任何一层（代理、负载均衡）都可能断开
- 必须每 45~60 秒发送 SSE 注释行（`: keepalive\n\n`）

---

## 二、最终技术栈（已验证成功）

| 组件 | 版本/实现 | 关键参数 |
|------|-----------|----------|
| Smart Proxy | `smart_proxy_streaming.py` | SSE 透传 + 字段白名单 + 60s 心跳 |
| LLM Client | `LiteLLMBackend`（httpx 流式） | chunk 超时 600s + 总时长 4h |
| 模型后端 | MTPLX Qwen3.6-27B | `--reasoning-mode auto` |
| 超时策略 | Chunk 级 + 心跳 | 600s chunk / 45~60s 心跳 |

---

## 三、推荐的调试流程

1. **直连模型验证**（最重要）
   ```bash
   curl -N http://localhost:8080/v1/chat/completions ...
   ```

2. **经 Smart Proxy 验证**
   ```bash
   curl -N http://localhost:4000/v1/chat/completions ...
   ```

3. **简化 prompt 先跑通**（“你好”）
4. **再上复杂案件**

---

## 四、避坑清单

- [x] 不要用 `urllib` 做流式
- [x] 不要把 `read` 超时设得太小
- [x] 不要相信“加大 timeout 就能解决”
- [x] 必须用 MTPLX 启动日志里的短 model_id
- [x] 必须实现自动拉起 + 就绪探针
- [x] 必须加心跳保活

---

**本教训已通过真实 27B 模型 + 复杂债务案件验证。**