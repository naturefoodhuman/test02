# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 16:00:00 CST
"""工厂级 LLM 遥测（老板第21轮全局要求 R4）。

目标：
  ① 每次 LLM 工作都记录【事件 + 耗时 + 模型 + token + 成败】；
  ② 终端实时显示【计时器】（让老板看到"正在跑、跑了多久"）；
  ③ 结构化落盘 JSONL，为以后不同模型能力对比储备数据。

零三方依赖（标准库 threading/time/json）。任何项目可复用。
"""
from __future__ import annotations

import json
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


# 默认事件日志路径（JSONL，每行一条事件）。项目可覆盖。
DEFAULT_LOG = "runtime/llm_events.jsonl"


@dataclass
class LLMEvent:
    """一次 LLM 工作的结构化事件。"""

    event: str                      # 事件名，如 strategy_report / compliance_recheck
    model: str                      # 模型名
    started_at: str                 # ISO 时间
    elapsed_ms: int                 # 耗时（毫秒）
    ok: bool                        # 成败
    project: str = ""               # 项目名
    phase: str = ""                 # 阶段，如 BUILD/RETRO
    prompt_chars: int = 0           # 输入字符数（无 token 时的近似）
    output_chars: int = 0           # 输出字符数
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None       # 估算成本（元）
    error: str = ""                 # 失败原因
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class _LiveTimer:
    """终端实时计时器：在后台线程刷新 'event ... 12.3s'，结束时清行。"""

    def __init__(self, label: str, stream=sys.stderr, interval: float = 0.1) -> None:
        self.label = label
        self.stream = stream
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = stream is not None and hasattr(stream, "isatty") and stream.isatty()

    def _run(self) -> None:
        start = time.monotonic()
        while not self._stop.is_set():
            el = time.monotonic() - start
            self.stream.write(f"\r⏳ {self.label} … {el:5.1f}s")
            self.stream.flush()
            time.sleep(self.interval)

    def __enter__(self) -> "_LiveTimer":
        if self._enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self._enabled:
            # 清掉计时器那一行
            self.stream.write("\r" + " " * (len(self.label) + 20) + "\r")
            self.stream.flush()


def log_event(ev: LLMEvent, log_path: str | Path = DEFAULT_LOG) -> None:
    """把事件追加写入 JSONL。"""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(ev.to_json() + "\n")


@contextmanager
def track(event: str, model: str, *, project: str = "", phase: str = "",
          prompt_chars: int = 0, log_path: str | Path = DEFAULT_LOG,
          show_timer: bool = True) -> Iterator[dict]:
    """上下文管理器：自动计时 + 终端实时计时器 + 落盘事件。

    用法：
        with track("strategy_report", "cloud/glm-primary", project="debt") as t:
            out = call_llm(...)
            t["output_chars"] = len(out)     # 可回填结果信息
        # 退出时自动打印耗时 + 写 JSONL

    Yields:
        一个 dict，可回填 output_chars/tokens/cost/ok/error/extra。
    """
    started = datetime.now()
    t0 = time.monotonic()
    box: dict = {"ok": True, "output_chars": 0, "prompt_tokens": None,
                 "output_tokens": None, "cost": None, "error": "", "extra": {}}
    timer = _LiveTimer(f"{event} [{model}]") if show_timer else None
    try:
        if timer:
            timer.__enter__()
        yield box
    except Exception as e:  # noqa: BLE001
        box["ok"] = False
        box["error"] = str(e)
        raise
    finally:
        if timer:
            timer.__exit__(None, None, None)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        ev = LLMEvent(
            event=event, model=model, started_at=started.isoformat(timespec="seconds"),
            elapsed_ms=elapsed_ms, ok=box["ok"], project=project, phase=phase,
            prompt_chars=prompt_chars, output_chars=box["output_chars"],
            prompt_tokens=box["prompt_tokens"], output_tokens=box["output_tokens"],
            cost=box["cost"], error=box["error"], extra=box["extra"],
        )
        log_event(ev, log_path)
        # 终端友好汇总（即使非 TTY 也打一行结论）
        status = "✅" if box["ok"] else "❌"
        sys.stderr.write(
            f"{status} {event} [{model}] 耗时 {elapsed_ms/1000:.1f}s"
            + (f"（输出{box['output_chars']}字）" if box["output_chars"] else "")
            + (f" 失败:{box['error']}" if not box["ok"] else "") + "\n"
        )
        sys.stderr.flush()


def summarize(log_path: str | Path = DEFAULT_LOG) -> dict[str, Any]:
    """汇总 JSONL 事件（为模型对比/成本分析储备）。"""
    p = Path(log_path)
    if not p.exists():
        return {"total": 0, "by_model": {}}
    by_model: dict[str, dict[str, Any]] = {}
    total = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        m = d.get("model", "?")
        b = by_model.setdefault(m, {"count": 0, "ok": 0, "total_ms": 0, "total_cost": 0.0})
        b["count"] += 1
        b["ok"] += 1 if d.get("ok") else 0
        b["total_ms"] += d.get("elapsed_ms", 0)
        b["total_cost"] += d.get("cost") or 0.0
    for m, b in by_model.items():
        b["avg_ms"] = round(b["total_ms"] / b["count"], 1) if b["count"] else 0
        b["success_rate"] = round(b["ok"] / b["count"], 3) if b["count"] else 0
    return {"total": total, "by_model": by_model}
