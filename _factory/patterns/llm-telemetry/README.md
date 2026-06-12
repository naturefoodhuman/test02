<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 16:00:00 CST
-->
# Pattern：llm-telemetry（工厂通用 LLM 遥测 · R4）

> 工厂级全局要求(老板第21轮)：所有 LLM 工作都记录事件+耗时等参数：
> ① 实时监控(终端显示实时计时器) ② 为以后不同模型能力对比储备数据。

## 能力
- `track(event, model, ...)` 上下文管理器：自动计时 + **终端实时计时器**(⏳ event … 12.3s) + 落盘 JSONL 事件。
- `log_event(ev)`：手动写一条事件。
- `summarize(log)`：按模型汇总(次数/成功率/平均耗时/成本)，供模型对比。

## 用法
```python
from llm_telemetry.telemetry import track
with track("strategy_report", "cloud/glm-primary", project="debt", phase="BUILD") as t:
    out = call_llm(...)
    t["output_chars"] = len(out)
# 退出时：终端打印 ✅ strategy_report [cloud/glm-primary] 耗时 8.2s，并写 runtime/llm_events.jsonl
```

## 事件字段(JSONL)
event/model/started_at/elapsed_ms/ok/project/phase/prompt_chars/output_chars/tokens/cost/error/extra

## 最后验证
- 2026-06-12：沙箱 pytest 通过；track+summarize 验证。
