# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-16 10:20:00
# 修改本文件中的配置比如“FORGE_CTX_MAX_TOKENS = int(os.getenv("FORGE_CTX_MAX_TOKENS", "502752"))“ 后
# 要重启 bash scripts/forge-start.sh 以使新配置生效

import os
import sys
import uvicorn
import json
import time
import random
import subprocess
import socket
import logging
import uuid
import re
import hashlib
import httpx
import asyncio
import contextlib
import yaml
from collections import deque
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from threading import Lock

# ============================================================
# .env 加载
# ============================================================
def _load_dotenv(env_path: str) -> int:
    if not os.path.exists(env_path):
        return 0
    count = 0
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v
                count += 1
    return count

FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.insert(0, FORGE_ROOT)

_dotenv_loaded = _load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
if not _dotenv_loaded:
    _dotenv_loaded = _load_dotenv(os.path.join(FORGE_ROOT, ".env"))
print(f"📦 .env 加载了 {_dotenv_loaded} 个环境变量")

try:
    from _infra.model_runtime import get_server_commands
    SERVER_COMMANDS = get_server_commands()
except Exception as _e:
    print(f"⚠️ SERVER_COMMANDS 加载失败: {_e}")
    SERVER_COMMANDS = {}

try:
    from _infra.model_runtime import get_memory_required_gb
except ImportError:
    def get_memory_required_gb(p):
        return 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("SmartProxy")
app = FastAPI(title="FORGE Smart Proxy v9.0 — Patched Two-Stage Tool Selector")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ============================================================
# 配置开关
# ============================================================
FORGE_ALLOW_UNKNOWN_MODEL_FALLBACK = _env_bool("FORGE_ALLOW_UNKNOWN_MODEL_FALLBACK", False)

FORGE_LOCAL_FORWARD_TOOLS = _env_bool("FORGE_LOCAL_FORWARD_TOOLS", True)
FORGE_REMOTE_FORWARD_TOOLS = _env_bool("FORGE_REMOTE_FORWARD_TOOLS", True)

FORGE_LOCAL_DEFAULT_MAX_TOKENS = int(os.getenv("FORGE_LOCAL_DEFAULT_MAX_TOKENS", "1024"))
FORGE_LOCAL_MAX_TOKENS_CAP = int(os.getenv("FORGE_LOCAL_MAX_TOKENS", "2048"))
FORGE_REMOTE_MAX_TOKENS_CAP = int(os.getenv("FORGE_REMOTE_MAX_TOKENS", "16384"))

FORGE_SORT_TOOLS_FOR_CACHE = _env_bool("FORGE_SORT_TOOLS_FOR_CACHE", True)
FORGE_COUNT_TOKENS_DIVISOR = int(os.getenv("FORGE_COUNT_TOKENS_DIVISOR", "4"))

# ── 上下文预算 guard（双职责：防 429 膨胀 + 防上游 400 超长）──────────────
# 估算 forward_payload["messages"] 的 token 数（= 整个会话多轮历史，cc-connect 每次全量带上）。
#  - SOFT 阈值：会话膨胀到此就压缩历史，防 NIM 大请求 429 + 降 TTFB（2026-08-04 实测
#    body 289KB/25 工具的请求易 429；soft 降到 ~32K tokens ≈ 128KB body）。
#  - HARD 阈值： 硬上限 1000000，超此即使压缩后仍超则拒绝（400 不可重试）。如果 .env / 环境变量里有 FORGE_CTX_MAX_TOKENS，就用环境变量；
# 否则用代码默认 1000000。
# 与 count_tokens 端点同口径（_json_bytes // FORGE_COUNT_TOKENS_DIVISOR）。
FORGE_CTX_MAX_TOKENS = int(os.getenv("FORGE_CTX_MAX_TOKENS", "1000000"))
FORGE_CTX_SOFT_RATIO = float(os.getenv("FORGE_CTX_SOFT_RATIO", "0.80"))
FORGE_CTX_HARD_RATIO = float(os.getenv("FORGE_CTX_HARD_RATIO", "0.95"))
# SOFT 直接指定（优先于 ratio）：防 429 用 ~32K tokens；设 >0 则覆盖 ratio 计算。
# 旧值 soft=162201(=202752*0.8) 太高，会话从未触发；新默认 32000 让 guard 真正生效。
FORGE_CTX_SOFT_TOKENS = int(os.getenv("FORGE_CTX_SOFT_TOKENS", "32000"))
FORGE_CTX_KEEP_RECENT_TURNS = int(os.getenv("FORGE_CTX_KEEP_RECENT_TURNS", "8"))
FORGE_CTX_TRUNC_TOOL_RESULT_CHARS = int(os.getenv("FORGE_CTX_TRUNC_TOOL_RESULT_CHARS", "2000"))

FORGE_TOOL_SELECTION_ENABLED = _env_bool("FORGE_TOOL_SELECTION_ENABLED", True)
FORGE_TOOL_SELECTION_THRESHOLD = int(os.getenv("FORGE_TOOL_SELECTION_THRESHOLD", "8"))
FORGE_TOOL_SELECTION_MAX = int(os.getenv("FORGE_TOOL_SELECTION_MAX", "8"))
FORGE_TOOL_SELECTION_DESC_MAX = int(os.getenv("FORGE_TOOL_SELECTION_DESC_MAX", "100"))
FORGE_TOOL_SELECTION_CACHE_SIZE = int(os.getenv("FORGE_TOOL_SELECTION_CACHE_SIZE", "1000"))
FORGE_TOOL_SELECTION_TIMEOUT_S = float(os.getenv("FORGE_TOOL_SELECTION_TIMEOUT_S", "20"))
FORGE_TOOL_SELECTION_MAX_TOKENS = int(os.getenv("FORGE_TOOL_SELECTION_MAX_TOKENS", "150"))
FORGE_TOOL_SELECTION_INTENT_MAX_CHARS = int(os.getenv("FORGE_TOOL_SELECTION_INTENT_MAX_CHARS", "2000"))
FORGE_TOOL_SCHEMA_BYTE_BUDGET = int(os.getenv("FORGE_TOOL_SCHEMA_BYTE_BUDGET", "32768"))
FORGE_TOOL_SELECTOR_POLICY_VERSION = os.getenv("FORGE_TOOL_SELECTOR_POLICY_VERSION", "v2")

# 远程路径(NIM)工具选择：NIM 免费档全量转发 25 工具时每个请求 ~289KB，是 429 膨胀
# 与 TTFB 过长主因（2026-08-04 实测 179/269 请求 >200KB）。开启后远程请求也走工具选择，
# 用本地轻量模型(默认 8080 mtplx-qwen36-27b)做选择，body 降至 ~39KB，零额外 NIM 额度。
# 有 core tools + 已用工具闭环 + 启发式兜底，漏选风险低；可随时关回全量。
FORGE_REMOTE_TOOL_SELECTION = _env_bool("FORGE_REMOTE_TOOL_SELECTION", True)
FORGE_REMOTE_SELECTOR_PORT = int(os.getenv("FORGE_REMOTE_SELECTOR_PORT", "8080"))

FORGE_CORE_TOOLS = [
    t.strip() for t in os.getenv(
        "FORGE_CORE_TOOLS", "Read,Bash,Edit,Grep,Glob,LS"
    ).split(",") if t.strip()
]

FORGE_SERIALIZE_LOCAL_PORTS = _env_bool("FORGE_SERIALIZE_LOCAL_PORTS", True)

FORGE_LOCAL_RETRY_COUNT = int(os.getenv("FORGE_LOCAL_RETRY_COUNT", "0"))
FORGE_REMOTE_RETRY_COUNT = int(os.getenv("FORGE_REMOTE_RETRY_COUNT", "2"))
# 429 纳入可重试：上游限流通常是瞬时的，退避后重试可自愈，避免直接透传 504 给客户端。
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}

FORGE_STREAM_PING_INTERVAL_SECONDS = float(os.getenv("FORGE_STREAM_PING_INTERVAL_SECONDS", "10"))
# 流式路径在"尚未向客户端发出任何内容"时，对 429/502/503/504 的有限重试次数。
# 一旦已发出正文（emitted_text=True）绝不重试（文档 §12），避免重复/错乱。
FORGE_STREAM_REMOTE_RETRY_COUNT = int(os.getenv("FORGE_STREAM_REMOTE_RETRY_COUNT", "2"))

# API Error auto-continue: do not drive VS Code/Feishu/terminal UI directly.
# Instead, when the NIM sidecar reports a transient API error before any content
# was emitted, the Smart Proxy waits according to Retry-After and replays the
# same request once. This is equivalent to the user typing “继续” after a
# transient gateway error, but keeps it client-agnostic and auditable.
FORGE_AUTO_CONTINUE_ON_API_ERROR = _env_bool("FORGE_AUTO_CONTINUE_ON_API_ERROR", True)
FORGE_AUTO_CONTINUE_MAX_ATTEMPTS = int(os.getenv("FORGE_AUTO_CONTINUE_MAX_ATTEMPTS", "1"))
FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS = float(os.getenv("FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS", "60"))
FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS = float(os.getenv("FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS", "300"))
FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS = float(os.getenv("FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS", "5"))
FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS = float(
    os.getenv("FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS", "900")
)
FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT = _env_bool("FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT", True)
FORGE_AUTO_CONTINUE_PARTIAL_TAIL_CHARS = int(os.getenv("FORGE_AUTO_CONTINUE_PARTIAL_TAIL_CHARS", "12000"))
FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS = int(
    os.getenv("FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS", "902752")
)
FORGE_AUTO_CONTINUE_STATUS_CODES_RAW = os.getenv("FORGE_AUTO_CONTINUE_STATUS_CODES", "*")
FORGE_AUTO_CONTINUE_ALL_STATUS_CODES = "*" in {
    item.strip() for item in FORGE_AUTO_CONTINUE_STATUS_CODES_RAW.split(",")
}
FORGE_AUTO_CONTINUE_STATUS_CODES = {
    int(item.strip())
    for item in FORGE_AUTO_CONTINUE_STATUS_CODES_RAW.split(",")
    if item.strip().isdigit()
}
_auto_continue_counters = {
    "attempts": 0,
    "api_error_replays": 0,
    "timeout_replays": 0,
    "no_output_replays": 0,
    "partial_replays": 0,
    "blocked_by_context": 0,
}
_auto_continue_last = {"reason": "", "wait_s": 0.0, "request_id": ""}
FORGE_REQUEST_EVENT_LOG_PATH = os.getenv("FORGE_REQUEST_EVENT_LOG_PATH", "/tmp/forge_request_events.jsonl")
FORGE_REQUEST_EVENT_LOG_INCLUDE_TEXT = _env_bool("FORGE_REQUEST_EVENT_LOG_INCLUDE_TEXT", False)
# Smart Proxy -> sidecar/upstream read timeout. Keep aligned with the 15min no-output watchdog.
FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS = float(os.getenv("FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS", "900"))

# 429/503 退避封顶（秒），防止上游给出过大 Retry-After 导致请求长时间挂起。
_RETRY_AFTER_CAP_SECONDS = 30.0

_SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m|\[[0-9;]*m")


# ============================================================
# 工具选择 LRU 缓存
# ============================================================
class ToolSelectionCache:
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = {}
        self.order = deque()
        self.lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    async def get(self, key):
        async with self.lock:
            if key in self.cache:
                self.order.remove(key)
                self.order.append(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None

    async def put(self, key, value):
        async with self.lock:
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.max_size:
                oldest = self.order.popleft()
                del self.cache[oldest]
            self.cache[key] = value
            self.order.append(key)

    def stats(self):
        return {"size": len(self.cache), "max_size": self.max_size,
                "hits": self.hits, "misses": self.misses}


tool_selection_cache = ToolSelectionCache(max_size=FORGE_TOOL_SELECTION_CACHE_SIZE)

_last_reduction_info: dict = {}
_last_reduction_lock = Lock()


def _record_reduction(info: dict):
    with _last_reduction_lock:
        _last_reduction_info.clear()
        _last_reduction_info.update(info)


# single-flight：同 key 并发请求只跑一次阶段1
_stage1_inflight: dict = {}
_stage1_inflight_guard = asyncio.Lock()


async def _get_inflight_lock(key: str) -> asyncio.Lock:
    async with _stage1_inflight_guard:
        lock = _stage1_inflight.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _stage1_inflight[key] = lock
        return lock


async def _release_inflight_lock(key: str):
    async with _stage1_inflight_guard:
        _stage1_inflight.pop(key, None)


# ============================================================
# RPM 限流
# ============================================================
class RPMGuard:
    def __init__(self, max_rpm=15):
        self.max_rpm = max_rpm
        self.windows = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key="default"):
        async with self._lock:
            now = time.time()
            if key not in self.windows:
                self.windows[key] = deque()
            win = self.windows[key]
            while win and win[0] < now - 60:
                win.popleft()
            waited = 0.0
            if len(win) >= self.max_rpm:
                wt = win[0] + 60 - now + 0.5
                if wt > 0:
                    await asyncio.sleep(wt)
                    waited = wt
                    now = time.time()
                    while win and win[0] < now - 60:
                        win.popleft()
            win.append(time.time())
            return waited

    def stats(self):
        return {
            "max_rpm": self.max_rpm,
            "active_keys": {
                k: len([t for t in v if t >= time.time() - 60])
                for k, v in self.windows.items()
            },
        }


rpm_guard = RPMGuard(max_rpm=int(os.getenv("FORGE_RPM_MAX", "15")))

# 远程上游并发上限。NIM 免费档对并发比对 RPM 更敏感；默认 2，
# 让 2 个自用 key 以每 key 1 并发起步，避免 VS Code/Feishu 多请求叠加。
FORGE_REMOTE_MAX_CONCURRENCY = int(os.getenv("FORGE_REMOTE_MAX_CONCURRENCY", "2"))
_remote_concurrency = asyncio.Semaphore(FORGE_REMOTE_MAX_CONCURRENCY)


# ============================================================
# 429 风暴熔断器（circuit breaker）
# ------------------------------------------------------------
# 动机：NIM 免费档无 Retry-After / ratelimit 头（实测），429 后无法从响应头得知
# 何时恢复。退避重试在"持续限流窗口"下会把请求量推更高 → 越重试越 429（今日
# 06:47–07:04 的 234 次 429 即此恶性循环）。熔断器在连续 429 达阈值后强制冷却，
# 冷却期内新请求在本地等待而非裸打上游，打破循环。
# ============================================================
class CircuitBreaker:
    def __init__(self, trip_threshold=5, cooldown_seconds=45.0, half_open_probe=True):
        self.trip_threshold = trip_threshold          # 连续 429 达此数即熔断
        self.cooldown_seconds = cooldown_seconds      # 熔断后强制冷却时长
        self.half_open_probe = half_open_probe        # 冷却后放一个探测请求验证恢复
        self._consecutive_429 = 0
        self._state = "closed"                        # closed / open / half_open
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    async def before_request(self) -> float:
        """请求前调用；返回需要等待的秒数（熔断冷却）。closed 时返回 0。"""
        async with self._lock:
            if self._state == "open":
                elapsed = time.time() - self._opened_at
                wait = self.cooldown_seconds - elapsed
                if wait > 0:
                    return wait
                # 冷却结束 → half_open，放一个探测请求
                self._state = "half_open"
                return 0.0
            return 0.0

    async def on_success(self):
        async with self._lock:
            self._consecutive_429 = 0
            if self._state == "half_open":
                self._state = "closed"               # 探测成功，恢复

    async def on_429(self):
        async with self._lock:
            self._consecutive_429 += 1
            if self._state == "half_open":
                # 探测请求仍 429 → 重新熔断
                self._state = "open"
                self._opened_at = time.time()
            elif self._consecutive_429 >= self.trip_threshold and self._state == "closed":
                self._state = "open"
                self._opened_at = time.time()

    def stats(self):
        return {
            "state": self._state,
            "consecutive_429": self._consecutive_429,
            "trip_threshold": self.trip_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "opened_at": self._opened_at,
        }


circuit_breaker = CircuitBreaker(
    trip_threshold=int(os.getenv("FORGE_CIRCUIT_BREAKER_TRIP", "5")),
    cooldown_seconds=float(os.getenv("FORGE_CIRCUIT_BREAKER_COOLDOWN", "45.0")),
)

# 退避加 jitter：base * 2^attempt + random(0, base)，避免多请求同步重试惊群。
def _backoff_with_jitter(attempt: int, base: float = 1.5, cap: float = 5.0) -> float:
    """指数退避 + 全抖动 jitter，封顶 cap（与 _RETRY_AFTER_CAP_SECONDS 协同）。"""
    exp = min(base * (2 ** attempt), cap)
    return min(exp + random.uniform(0, base), cap)


# 流式路径可重试的读类异常类型名（httpx 在排队/断流时抛这些，常空 message）。
# 未发内容时对它们退避重试，避免 turn 空挂 20 分钟 + 0 token。
_STREAM_RETRYABLE_EXC_TYPES = {
    "ReadTimeout", "ReadError", "RemoteProtocolError",
    "PoolTimeout", "ConnectTimeout", "ConnectError",
    "TimeoutException",  # httpx 基类
}


# 429/502/503/504 触发重试的累计计数（流式+非流式合计），供 /stats 观测重试是否在生效。
_retry_counters = {"429": 0, "502": 0, "503": 0, "504": 0}

FORGE_TRACKER_FINISHED_TTL_SECONDS = float(os.getenv("FORGE_TRACKER_FINISHED_TTL_SECONDS", "5"))

# 上下文预算 guard 计数，供 /stats 观测压缩是否在生效。
_ctx_budget_counters = {"pass": 0, "compacted": 0, "rejected": 0}
_ctx_budget_last = {"action": "pass", "est_before": 0, "est_after": 0}


# ============================================================
# 活跃请求追踪
# ============================================================
class ActiveTracker:
    def __init__(self):
        self.requests = {}
        self._lock = asyncio.Lock()
        self.total_requests = 0
        self.total_errors = 0

    def _prune_finished_locked(self, now: float) -> None:
        ttl = max(0.0, FORGE_TRACKER_FINISHED_TTL_SECONDS)
        stale = [
            rid for rid, req in self.requests.items()
            if req.get("status") in {"done", "error"}
            and now - float(req.get("finished_at", req.get("last", now))) > ttl
        ]
        for rid in stale:
            self.requests.pop(rid, None)

    async def start(self, rid, model, target, is_remote):
        async with self._lock:
            self.requests[rid] = {
                "id": rid, "model": model, "target": target, "is_remote": is_remote,
                "status": "waiting", "bytes": 0, "start": time.time(),
                "last": time.time(), "chunks": 0,
            }
            self.total_requests += 1

    async def update(self, rid, **kw):
        async with self._lock:
            if rid in self.requests:
                self.requests[rid].update(kw)

    async def heartbeat(self, rid, delta=0):
        async with self._lock:
            if rid in self.requests:
                r = self.requests[rid]
                r["bytes"] += delta
                r["chunks"] += 1
                r["last"] = time.time()
                if r["status"] not in {"done", "error"}:
                    r["status"] = "generating"

    async def finish(self, rid, success=True):
        async with self._lock:
            if rid in self.requests:
                self.requests[rid]["status"] = "done" if success else "error"
                self.requests[rid]["finished_at"] = time.time()
                self.requests[rid]["last"] = time.time()
            if not success:
                self.total_errors += 1

    async def remove(self, rid):
        async with self._lock:
            self.requests.pop(rid, None)

    async def active_count(self):
        async with self._lock:
            now = time.time()
            self._prune_finished_locked(now)
            return sum(1 for r in self.requests.values() if r.get("status") not in {"done", "error"})

    async def snapshot(self):
        async with self._lock:
            now = time.time()
            self._prune_finished_locked(now)
            out = []
            for r in self.requests.values():
                elapsed = now - r["start"]
                idle = now - r["last"]
                status = r["status"]
                if status == "generating" and idle > 30:
                    status = "stalled?"
                out.append({
                    "id": r["id"][:12], "model": r["model"], "target": r["target"],
                    "is_remote": r["is_remote"], "status": status,
                    "elapsed_s": round(elapsed, 1), "bytes": r["bytes"],
                    "chunks": r["chunks"], "idle_s": round(idle, 1),
                })
            return out


tracker = ActiveTracker()


# ============================================================
# 本地端口串行化（防止并发请求把 SessionBank/前缀缓存挤爆）
# ============================================================
_port_locks: dict[int, asyncio.Lock] = {}


def _get_port_lock(port: int) -> asyncio.Lock:
    if port not in _port_locks:
        _port_locks[port] = asyncio.Lock()
    return _port_locks[port]


class _NullContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _local_port_guard(port):
    if FORGE_SERIALIZE_LOCAL_PORTS and port is not None:
        return _get_port_lock(port)
    return _NullContext()


# ============================================================
# 路由表加载
# ============================================================
LITELLM_CONFIG_PATH = os.path.join(FORGE_ROOT, "_infra", "litellm-config.yaml")


def _fallback_routes():
    return {
        "mtplx-qwen36-27b": 8080, "claude-3-5-sonnet-20241022": 8080,
        "claude-opus-4-8": 8080, "claude-haiku-4-5": 8080,
    }, {}


def load_routes_from_litellm():
    if not os.path.exists(LITELLM_CONFIG_PATH):
        logger.warning(f"⚠️ LiteLLM config 不存在: {LITELLM_CONFIG_PATH}")
        return _fallback_routes()
    try:
        with open(LITELLM_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        M, R = {}, {}
        for e in cfg.get("model_list", []):
            mn = e.get("model_name")
            if not mn:
                continue
            p = e.get("litellm_params", {}) or {}
            base = p.get("api_base", "") or ""
            use_nim_proxy = (
                os.getenv("FORGE_USE_NIM_PROXY", "0").lower() in {"1", "true", "yes", "on"}
                and "integrate.api.nvidia.com" in base
            )
            if use_nim_proxy:
                base = os.getenv("NIM_PROXY_BASE_URL", "http://127.0.0.1:4010/v1")
            if ("127.0.0.1" in base or "localhost" in base) and not use_nim_proxy:
                try:
                    M[mn] = int(base.split(":")[-1].split("/")[0])
                except Exception:
                    logger.warning(f"⚠️ 无法从 {base} 提取端口，跳过 {mn}")
            else:
                ref = str(p.get("api_key", ""))
                env = ref.replace("os.environ/", "").strip("${}")
                if use_nim_proxy:
                    env = os.getenv("NIM_PROXY_API_KEY_ENV", "NIM_PROXY_API_KEY")
                R[mn] = {
                    "api_base": base.rstrip("/"),
                    "model": p.get("model", "").replace("openai/", ""),
                    "api_key_env": env,
                    "api_key_optional": use_nim_proxy,
                    "max_tokens": p.get("max_tokens", 16384),
                }
        logger.info(f"📋 路由表加载完成: {len(M)} 本地, {len(R)} 远程")
        return M, R
    except Exception as ex:
        logger.error(f"litellm parse fail {ex}")
        return _fallback_routes()


MODEL_TO_PORT, REMOTE_ROUTES = load_routes_from_litellm()

REAL_ID_MAP = {
    8080: "mtplx-qwen36-27b-optimized-quality",
    8082: "mtplx-gemma4-optimized-quality",
    8084: "qwopus-35b-a3b-v1-mtp-gguf-8bit",
    11434: "deepseek-r1:32b",
}


def normalize_model_name(s):
    return ANSI_RE.sub("", str(s or "")).strip()


# ============================================================
# Anthropic <-> OpenAI 转换
# ============================================================
def _to_anthropic_tool_id(raw):
    if not raw:
        return f"toolu_{uuid.uuid4().hex[:12]}"
    raw = str(raw)
    return raw if raw.startswith("toolu_") else f"toolu_{raw}"


def _extract_anthropic_text(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c)
    return str(c or "")


def _bounded_max_tokens(v, default, cap):
    try:
        p = int(v)
    except Exception:
        p = default
    return max(1, min(p, cap))


def _anthropic_tools_to_openai(tools: list, sort_for_cache: bool = True) -> list:
    """Anthropic tools -> OpenAI function tools。
    绝不截断 description/parameters（文档 §9.9）：已选中的工具必须保持完整 schema。
    体积控制只能通过“减少工具数量”和“字节预算丢弃低优先级工具”实现，见 _apply_schema_byte_budget。
    """
    out = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        out.append({
            "type": "function",
            "function": {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    if sort_for_cache:
        out.sort(key=lambda x: x.get("function", {}).get("name", ""))
    return out


def _anthropic_tool_choice_to_openai(tc):
    if not tc:
        return None
    if isinstance(tc, str):
        return tc
    if isinstance(tc, dict):
        tp = tc.get("type", "auto")
        if tp == "auto":
            return "auto"
        if tp == "any":
            return "required"
        if tp == "none":
            return "none"
        if tp == "tool":
            return {"type": "function", "function": {"name": tc.get("name", "")}}
    return None


def _convert_anthropic_messages_to_openai(messages: list) -> list:
    o = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user" and isinstance(content, list):
            txt, trs = [], []
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    trs.append(b)
                elif isinstance(b, dict) and b.get("type") == "text":
                    txt.append(b.get("text", ""))
                elif isinstance(b, dict):
                    txt.append(str(b.get("text", "")))
            for tr in trs:
                c = tr.get("content", "")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
                o.append({"role": "tool", "tool_call_id": tr.get("tool_use_id", ""), "content": str(c)})
            if txt:
                o.append({"role": "user", "content": "\n".join(txt)})
        elif role == "assistant" and isinstance(content, list):
            txt, tcs = [], []
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tcs.append({
                        "id": b.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": b.get("name", ""),
                            "arguments": json.dumps(b.get("input", {}), ensure_ascii=False),
                        },
                    })
                elif isinstance(b, dict) and b.get("type") == "text":
                    txt.append(b.get("text", ""))
                elif isinstance(b, dict):
                    txt.append(str(b))
            msg = {"role": "assistant", "content": "\n".join(txt) if txt else None}
            if tcs:
                msg["tool_calls"] = tcs
            o.append(msg)
        else:
            if isinstance(content, list):
                content = _extract_anthropic_text(content)
            o.append({"role": role, "content": content})
    return o


def _openai_tool_calls_to_anthropic(tcs: list) -> list:
    blocks = []
    for tc in tcs or []:
        if not isinstance(tc, dict):
            continue
        f = tc.get("function", {}) or {}
        try:
            args = json.loads(f.get("arguments", "{}") or "{}")
        except Exception:
            args = {"raw": f.get("arguments", "")}
        blocks.append({
            "type": "tool_use",
            "id": _to_anthropic_tool_id(tc.get("id") or ""),
            "name": f.get("name", ""),
            "input": args,
        })
    return blocks


def _anthropic_sse(ev, p) -> bytes:
    return f"event: {ev}\ndata: {json.dumps(p, ensure_ascii=False)}\n\n".encode("utf-8")


def _latest_user_message_summary(data: dict) -> dict:
    messages = data.get("messages") or []
    latest = ""
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, str):
                    latest = content
                elif isinstance(content, list):
                    latest = "".join(
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in content
                    )
                else:
                    latest = str(content or "")
                break
    encoded = latest.encode("utf-8", "ignore")
    out = {
        "latest_user_sha256": hashlib.sha256(encoded).hexdigest()[:16] if latest else "",
        "latest_user_chars": len(latest),
    }
    if FORGE_REQUEST_EVENT_LOG_INCLUDE_TEXT and latest:
        out["latest_user_preview"] = latest[:500]
    return out


def _record_request_event(kind: str, request_id: str, **fields) -> None:
    if not FORGE_REQUEST_EVENT_LOG_PATH:
        return
    event = {
        "ts": time.time(),
        "local_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "kind": kind,
        "request_id": request_id,
    }
    event.update(fields)
    try:
        with open(FORGE_REQUEST_EVENT_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    except Exception:
        # Diagnostics must never break request handling.
        pass


def _json_bytes(v) -> int:
    try:
        return len(json.dumps(v, ensure_ascii=False).encode("utf-8"))
    except Exception:
        return 0


# ============================================================
# 上下文预算 guard：估算 + 结构化裁剪（纯函数，便于单测）
# 口径与 /messages/count_tokens 端点一致：_json_bytes // FORGE_COUNT_TOKENS_DIVISOR。
# ============================================================
def _estimate_messages_tokens(messages) -> int:
    """估算 messages 数组的 input token 数。与 count_tokens 端点同口径。"""
    if not messages:
        return 0
    return max(1, _json_bytes(messages) // FORGE_COUNT_TOKENS_DIVISOR)


def _msg_text_len(msg) -> int:
    """单条 message 的可见文本字节数（用于裁剪时判断哪条最长）。"""
    c = msg.get("content") if isinstance(msg, dict) else None
    if c is None:
        return 0
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        total = 0
        for b in c:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    total += len(str(b.get("text", "")))
                elif b.get("type") == "tool_result":
                    rc = b.get("content", "")
                    if isinstance(rc, list):
                        rc = "".join(
                            x.get("text", "") if isinstance(x, dict) else str(x) for x in rc
                        )
                    total += len(str(rc))
        return total
    return 0


def _truncate_tool_result_content(content, max_chars: int):
    """截断 tool_result 的 content 到 max_chars，加截断标记。"""
    marker = "\n…[forge:tool_result truncated]"
    if isinstance(content, str):
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + marker
    if isinstance(content, list):
        out = []
        kept = 0
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                txt = str(b.get("text", ""))
                if kept + len(txt) > max_chars:
                    remain = max(0, max_chars - kept)
                    if remain:
                        out.append({"type": "text", "text": txt[:remain] + marker})
                    return out
                out.append(b)
                kept += len(txt)
            else:
                out.append(b)
        return out
    return content


def _compact_messages(messages: list, keep_recent_turns: int, trunc_tool_result_chars: int) -> list:
    """结构化裁剪历史 messages，降低 token 数。

    策略（不调 LLM，零额外 token 成本）：
      - 不删除：所有 system 消息、最近 keep_recent_turns*2 条 user/assistant、
        以及任何含 tool_calls / tool_use_id 的消息（保证工具调用配对完整）。
      - 不截断（原样保留）：最近 keep_recent_turns*2 条（保证最新上下文完整）。
      - 可截断 content：上述"不删除"之外的历史消息——
        中间历史 assistant 的长文本输出（保留首尾骨架）、tool_result 的大块内容
        （截断到 trunc_tool_result_chars）。含 tool_call_id 的消息保留结构但截断其 content。
    返回裁剪后的新列表（不修改入参）。
    """
    if not isinstance(messages, list) or len(messages) <= 2:
        return list(messages or [])

    n = len(messages)
    # no_delete: 不整条删除（system / 最近轮 / 含工具配对）
    # no_truncate: 原样保留不截断（仅最近轮，保证最新上下文完整）
    no_delete = set()
    for i, m in enumerate(messages):
        if isinstance(m, dict) and m.get("role") == "system":
            no_delete.add(i)
    tail_start = max(0, n - keep_recent_turns * 2)
    no_truncate = set(range(tail_start, n))
    no_delete |= no_truncate
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            continue
        if m.get("tool_calls") or m.get("tool_call_id"):
            no_delete.add(i)
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") in ("tool_use", "tool_result"):
                    no_delete.add(i)
                    break

    def _truncate_msg(m):
        """对单条消息做 content 截断，返回 (new_msg, changed)。"""
        if not isinstance(m, dict):
            return m, False
        role = m.get("role")
        c = m.get("content")
        # OpenAI 格式 tool_result（role=tool）截断 content
        if role == "tool" and isinstance(c, str) and len(c) > trunc_tool_result_chars:
            m2 = dict(m)
            m2["content"] = c[:trunc_tool_result_chars] + "\n…[forge:tool_result truncated]"
            return m2, True
        # Anthropic 格式：content 列表里的 tool_result 截断
        if isinstance(c, list):
            new_blocks = []
            changed = False
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    rc = b.get("content", "")
                    if _msg_text_len({"content": rc}) > trunc_tool_result_chars:
                        nb = dict(b)
                        nb["content"] = _truncate_tool_result_content(rc, trunc_tool_result_chars)
                        new_blocks.append(nb)
                        changed = True
                        continue
                new_blocks.append(b)
            if changed:
                m2 = dict(m)
                m2["content"] = new_blocks
                return m2, True
        # assistant 长文本输出：保留首尾骨架
        if role == "assistant" and isinstance(c, str) and len(c) > 2000:
            m2 = dict(m)
            m2["content"] = c[:500] + "\n…[forge:assistant output truncated]…\n" + c[-200:]
            return m2, True
        return m, False

    out = []
    for i, m in enumerate(messages):
        if i in no_delete:
            # 不删除，但若不在最近轮则可截断 content
            if i in no_truncate:
                out.append(m)
            else:
                new_m, _ = _truncate_msg(m)
                out.append(new_m)
            continue
        # 可删除的中间历史消息：截断后保留（不直接删，避免对话断裂）
        new_m, _ = _truncate_msg(m)
        out.append(new_m)
    return out


def _apply_context_budget(forward_payload: dict):
    """转发前应用上下文预算 guard。原地修改 forward_payload["messages"]。

    返回 (action, est_before, est_after, hint)：
      action ∈ {"pass", "compacted", "rejected"}
      hint  ∈ 非空时为给用户的提示文本（compacted/rejected 时）
    达 SOFT(80%) 触发结构化裁剪；达 HARD(95%) 拒绝并提示 /compact。
    """
    msgs = forward_payload.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return ("pass", 0, 0, "")

    est_before = _estimate_messages_tokens(msgs)
    # SOFT：优先用 FORGE_CTX_SOFT_TOKENS（防 429，~32K），否则回退 ratio 计算（防 400）。
    soft = FORGE_CTX_SOFT_TOKENS if FORGE_CTX_SOFT_TOKENS > 0 else int(FORGE_CTX_MAX_TOKENS * FORGE_CTX_SOFT_RATIO)
    hard = int(FORGE_CTX_MAX_TOKENS * FORGE_CTX_HARD_RATIO)

    if est_before < soft:
        return ("pass", est_before, est_before, "")

    # 已超 HARD：先尝试裁剪，裁剪后仍超 HARD 才拒绝（给一次自愈机会）
    compacted = _compact_messages(msgs, FORGE_CTX_KEEP_RECENT_TURNS, FORGE_CTX_TRUNC_TOOL_RESULT_CHARS)
    est_after = _estimate_messages_tokens(compacted)

    if est_before >= hard and est_after >= hard:
        hint = (
            f"上下文已达上游上限的 {int(FORGE_CTX_HARD_RATIO*100)}%"
            f"（约 {est_after}/{FORGE_CTX_MAX_TOKENS} tokens），即使压缩后仍超限。"
            f"请手动 /compact 或减少上下文后再试。"
        )
        return ("rejected", est_before, est_after, hint)

    # 软阈值触发，或超 HARD 但裁剪后已降到 HARD 以下：采用裁剪结果
    forward_payload["messages"] = compacted
    hint = (
        f"⚠️ 上下文已达上游上限的 {int(FORGE_CTX_SOFT_RATIO*100)}%"
        f"（约 {est_before}/{FORGE_CTX_MAX_TOKENS} tokens），已自动压缩历史消息"
        f"（{est_before}→{est_after}）。建议手动 /compact 以获得更好的语义压缩质量。"
    )
    return ("compacted", est_before, est_after, hint)


# ============================================================
# 意图提取 / 工具历史 / 启发式兜底 / 字节预算
# ============================================================
def _clean_user_intent(text: str) -> str:
    if not text:
        return ""
    cleaned = _SYSTEM_REMINDER_RE.sub("", text).strip()
    if len(cleaned) > FORGE_TOOL_SELECTION_INTENT_MAX_CHARS:
        cleaned = cleaned[:FORGE_TOOL_SELECTION_INTENT_MAX_CHARS]
    return cleaned


def _latest_user_text(messages: list) -> str:
    """从最后一个含真实文本的 user 回合提取意图；
    纯 tool_result 回合（无 text block）自然被跳过，继续向前查找（文档 §9.3/§9.4）。
    """
    if not isinstance(messages, list):
        return ""
    for msg in reversed(messages):
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip():
            return _clean_user_intent(content)
        if isinstance(content, list):
            parts = [b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()]
            if parts:
                return _clean_user_intent("\n".join(parts))
            # 纯 tool_result（parts 为空）：不 return，继续向前找
    return ""


def _extract_used_tool_names(messages: list) -> set:
    """扫描历史 assistant 消息，收集已调用过的工具名，
    保证工具闭环不因 tool_result 回合而被裁掉（文档 §9.4）。
    """
    used = set()
    if not isinstance(messages, list):
        return used
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name"):
                used.add(block["name"])
    return used


def _heuristic_rank_tools(user_text: str, tools: list, exclude: set) -> list:
    """selector 失败时的确定性关键词打分兜底（文档 §9.8）。"""
    words = set(w.lower() for w in _WORD_RE.findall(user_text or "") if len(w) > 2)
    scored = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        name = t.get("name", "")
        if not name or name in exclude:
            continue
        haystack = (name + " " + str(t.get("description", ""))).lower()
        score = sum(1 for w in words if w in haystack)
        scored.append((score, name))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [name for score, name in scored if score > 0]


def _apply_schema_byte_budget(ordered_names: list, tools_by_name: dict, mandatory: set) -> list:
    """数量上限之外的字节预算控制（文档 §9.9）。
    mandatory 工具即使很大也保留；预算不足时按 ordered_names 的优先级顺序
    丢弃低优先级候选工具（不截断内容）。
    """
    if FORGE_TOOL_SCHEMA_BYTE_BUDGET <= 0:
        return ordered_names
    kept, total = [], 0
    for name in ordered_names:
        if name in mandatory:
            kept.append(name)
            total += _json_bytes(tools_by_name.get(name, {}))
    for name in ordered_names:
        if name in mandatory:
            continue
        size = _json_bytes(tools_by_name.get(name, {}))
        if total + size > FORGE_TOOL_SCHEMA_BYTE_BUDGET:
            continue
        kept.append(name)
        total += size
    return kept


# ============================================================
# 两阶段工具选择
# ============================================================
_selector_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0, read=FORGE_TOOL_SELECTION_TIMEOUT_S, write=10.0, pool=10.0
    )
)


async def _select_tools_stage1(user_text, tools, target_port, real_model_id):
    """阶段1：极小 prompt 让模型选相关工具名。失败返回 None（由调用方走启发式兜底）。"""
    sorted_tools = sorted(
        [t for t in tools if isinstance(t, dict) and t.get("name")],
        key=lambda x: x.get("name", "")
    )
    tool_lines = []
    for t in sorted_tools:
        name = t.get("name", "")
        desc = str(t.get("description", "")).replace("\n", " ")[:FORGE_TOOL_SELECTION_DESC_MAX]
        tool_lines.append(f"- {name}: {desc}")

    prompt = (
        "You are a strict tool router. Based on the user's request, select the tools needed.\n"
        f"Choose up to {FORGE_TOOL_SELECTION_MAX} tools. If none are needed, return an empty list.\n"
        'Reply ONLY with JSON: {"tools": ["Name1","Name2"]}\n\n'
        "TOOLS:\n" + "\n".join(tool_lines) +
        f"\n\nUSER REQUEST:\n{user_text}\n"
    )
    url = f"http://127.0.0.1:{target_port}/v1/chat/completions"
    payload = {
        "model": real_model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": FORGE_TOOL_SELECTION_MAX_TOKENS,
        "temperature": 0.0,
        "stream": False,
    }
    try:
        if not is_listening(target_port):
            if not await asyncio.to_thread(ensure_server, target_port):
                return None
        async with _local_port_guard(target_port):
            resp = await _selector_http_client.post(url, json=payload)
        if resp.status_code != 200:
            logger.warning(f"🎯 stage1 selector HTTP {resp.status_code}")
            return None
        content = (resp.json().get("choices", [{}])[0]
                   .get("message", {}).get("content", "")) or ""
        selected = None
        try:
            selected = json.loads(content).get("tools")
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if m:
                try:
                    selected = json.loads(m.group()).get("tools")
                except json.JSONDecodeError:
                    return None
        if not isinstance(selected, list):
            return None
        valid = {t.get("name") for t in tools if isinstance(t, dict)}
        return [s for s in selected if s in valid]
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        logger.warning(f"🎯 stage1 network error: {e}")
        return None
    except Exception as e:
        logger.warning(f"🎯 stage1 unknown error: {e}")
        return None


async def _apply_tool_selection(data: dict, target_port: int, real_model_id: str) -> dict:
    """两阶段工具筛选，严格优先级（文档 §9.7）：
       1. 强制 tool_choice 指定的工具
       2. 当前会话工具闭环已使用过的工具（tool_result 回合不能丢失，§9.4）
       3. Core Tools（配置顺序）
       4. Selector 选中的工具，或 selector 失败时的确定性启发式兜底（§9.8）
       始终 len(final) <= FORGE_TOOL_SELECTION_MAX，从不回退全量。
    """
    tools = data.get("tools") or []
    if not isinstance(tools, list) or len(tools) <= FORGE_TOOL_SELECTION_THRESHOLD:
        return data

    valid_names = {t.get("name") for t in tools if isinstance(t, dict) and t.get("name")}
    tools_by_name = {t.get("name"): t for t in tools if isinstance(t, dict) and t.get("name")}
    used_tools = _extract_used_tool_names(data.get("messages", [])) & valid_names
    core_valid = [n for n in FORGE_CORE_TOOLS if n in valid_names]

    tool_choice = data.get("tool_choice")
    mandatory = set(used_tools)
    skip_selector = False
    mode = "stage1"

    if isinstance(tool_choice, dict) and tool_choice.get("type") == "tool":
        forced_name = tool_choice.get("name", "")
        skip_selector = True
        if forced_name in valid_names:
            mandatory.add(forced_name)
            mode = "forced_tool_choice"
        else:
            mode = "forced_tool_choice_not_found_fallback_core"

    ordered = sorted(mandatory)
    for n in core_valid:
        if n not in ordered:
            ordered.append(n)

    selected = []
    if not skip_selector:
        user_text = _latest_user_text(data.get("messages", []))
        if user_text:
            catalog_hash = hashlib.sha256(
                json.dumps(tools, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:20]
            cache_key = hashlib.sha256(
                f"{FORGE_TOOL_SELECTOR_POLICY_VERSION}|{real_model_id}|{user_text}|{catalog_hash}".encode("utf-8")
            ).hexdigest()

            selected = await tool_selection_cache.get(cache_key)
            cache_hit = selected is not None

            if selected is None:
                lock = await _get_inflight_lock(cache_key)
                async with lock:
                    selected = await tool_selection_cache.get(cache_key)
                    if selected is None:
                        selected = await _select_tools_stage1(user_text, tools, target_port, real_model_id)
                        if selected is None:
                            selected = _heuristic_rank_tools(user_text, tools, exclude=set(ordered))
                            mode = "heuristic_fallback"
                            logger.warning(f"🎯 selector 失败，启发式兜底: {selected[:FORGE_TOOL_SELECTION_MAX]}")
                        else:
                            await tool_selection_cache.put(cache_key, selected)
                await _release_inflight_lock(cache_key)
            else:
                mode = "cache"

            logger.info(f"🎯 工具选择 mode={mode} selected={selected}")

    for n in selected:
        if len(ordered) >= FORGE_TOOL_SELECTION_MAX:
            break
        if n in valid_names and n not in ordered:
            ordered.append(n)

    final_names = ordered[:FORGE_TOOL_SELECTION_MAX]
    final_names = _apply_schema_byte_budget(final_names, tools_by_name, mandatory)

    if not final_names:
        final_names = core_valid[:FORGE_TOOL_SELECTION_MAX] or sorted(mandatory)[:FORGE_TOOL_SELECTION_MAX]

    filtered = [tools_by_name[n] for n in final_names if n in tools_by_name]
    filtered.sort(key=lambda x: x.get("name", ""))

    logger.info(f"🪚 tool reduction: {len(tools)} -> {len(filtered)} (mode={mode}, names={final_names})")
    _record_reduction({
        "ts": time.time(), "original": len(tools), "final": len(filtered),
        "selected": final_names, "mode": mode,
    })

    data = dict(data)
    data["tools"] = filtered
    return data


# ============================================================
# 显存 / 后端生命周期管理
# ============================================================
VRAM_LIMIT = 48
MODEL_VRAM = {8080: get_memory_required_gb(8080), 8082: get_memory_required_gb(8082),
              8084: get_memory_required_gb(8084), 11434: 20}
active_servers = {}
vram_lock = Lock()
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=30.0, read=FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS, write=30.0, pool=30.0),
    limits=httpx.Limits(max_keepalive_connections=10),
)


def is_listening(p) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", p)) == 0


def ensure_server(port: int) -> bool:
    """同步函数，会阻塞最长 ~60s。调用方必须用 asyncio.to_thread 包装（Patch H），
    否则会阻塞整个事件循环，让并发请求全部卡住。"""
    with vram_lock:
        if is_listening(port):
            active_servers[port] = time.time()
            return True
        if port not in SERVER_COMMANDS:
            return False
        cur = sum(MODEL_VRAM.get(p, 20) for p in active_servers if is_listening(p))
        while cur + MODEL_VRAM.get(port, 20) > VRAM_LIMIT:
            listening = [p for p in active_servers if is_listening(p)]
            if not listening:
                break
            oldest = min(listening, key=lambda x: active_servers[x])
            logger.info(f"⚠️ 卸载离线模型释放显存 (Port {oldest})")
            subprocess.run(f"pkill -9 -f '.*{oldest}'", shell=True)
            active_servers.pop(oldest, None)
            cur = sum(MODEL_VRAM.get(p, 20) for p in active_servers if is_listening(p))

        logger.info(f"🚀 拉起真机模型 (Port {port})...")
        subprocess.run(["osascript", "-e",
                        f'tell application "Terminal" to do script "{SERVER_COMMANDS[port]}"'])
        st = time.time()
        while time.time() - st < 60:
            if is_listening(port):
                active_servers[port] = time.time()
                time.sleep(3)
                return True
            time.sleep(2)
        return False


# ============================================================
# 退避辅助：从上游 429/503 响应读 Retry-After，无则指数退避，统一封顶。
# ============================================================
def _retry_after_seconds_from_value(ra, default: float, cap: float | None = None) -> float:
    """从已提取的 Retry-After 头值计算退避秒数；非法或缺失返回 default。"""
    limit = _RETRY_AFTER_CAP_SECONDS if cap is None else cap
    if ra:
        try:
            return min(max(0.0, float(ra)), limit)
        except (ValueError, TypeError):
            pass  # HTTP-date 格式不解析，走 default
    return min(max(0.0, default), limit)


def _retry_after_seconds(resp, default: float, cap: float | None = None) -> float:
    """从 httpx 响应对象读 Retry-After 头；无则返回 default。"""
    try:
        ra = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    except Exception:
        ra = None
    return _retry_after_seconds_from_value(ra, default, cap=cap)


def _is_context_limit_error_text(text: str) -> bool:
    lower = str(text or "").lower()
    return (
        ("accepts at most" in lower and "tokens" in lower)
        or ("combined input and output tokens" in lower)
        or ("context_length_exceeded" in lower)
        or ("maximum context" in lower and "token" in lower)
        or ("context" in lower and "too large" in lower)
    )


def _auto_continue_status_allowed(status_code: int | None, body_text: str = "") -> bool:
    if _is_context_limit_error_text(body_text):
        return False
    if status_code is None:
        return True
    if FORGE_AUTO_CONTINUE_ALL_STATUS_CODES:
        return True
    return int(status_code) in FORGE_AUTO_CONTINUE_STATUS_CODES


def _auto_continue_wait_from_response(resp, default: float | None = None) -> float:
    return _retry_after_seconds(
        resp,
        default=FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS if default is None else default,
        cap=FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS,
    )


def _retry_after_seconds_from_error_payload(item, default: float | None = None) -> float:
    """从 sidecar SSE error payload 里解析 'retry after 124.9s'。"""
    if isinstance(item, dict):
        message = str(item.get("message") or item.get("error") or item)
    else:
        message = str(item or "")
    if _is_context_limit_error_text(message):
        return 0.0
    match = re.search(r"retry after\s+([0-9]+(?:\.[0-9]+)?)s?", message, re.IGNORECASE)
    if match:
        return min(float(match.group(1)), FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS)
    base = FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS if default is None else default
    return min(base, FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS)


def _auto_continue_context_too_large(forward_payload: dict) -> tuple[bool, int]:
    if FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS <= 0:
        return False, 0
    messages = forward_payload.get("messages")
    if not isinstance(messages, list):
        return False, 0
    est = _estimate_messages_tokens(messages)
    return est >= FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS, est


def _set_auto_continue_last(reason: str, wait_s: float, request_id: str = "") -> None:
    _auto_continue_last.update({"reason": reason, "wait_s": round(float(wait_s), 3), "request_id": request_id})


def _build_partial_continue_payload(base_payload: dict, text_content: str) -> dict:
    payload = dict(base_payload)
    messages = list(payload.get("messages") or [])
    tail = text_content[-FORGE_AUTO_CONTINUE_PARTIAL_TAIL_CHARS:] if text_content else ""
    messages.append({
        "role": "assistant",
        "content": tail,
    })
    messages.append({
        "role": "user",
        "content": (
            "上一次回答在流式输出中断。请严格从上面 assistant 已经输出内容之后继续，"
            "不要重复已经输出过的内容，不要重新执行任何工具。"
        ),
    })
    payload["messages"] = messages
    payload["stream"] = True
    return payload


# ============================================================
# 非流式请求转发（含重试策略，Patch B，抽成独立函数便于单测）
# ============================================================
async def _forward_with_retries(target_url: str, forward_payload: dict, headers: dict,
                                 is_remote: bool, target_port, handles_retries: bool = False):
    auto_continue = bool(
        handles_retries
        and is_remote
        and FORGE_AUTO_CONTINUE_ON_API_ERROR
        and FORGE_AUTO_CONTINUE_MAX_ATTEMPTS > 0
    )
    context_too_large, context_est = _auto_continue_context_too_large(forward_payload)
    retry_count = (
        FORGE_AUTO_CONTINUE_MAX_ATTEMPTS
        if auto_continue and not context_too_large
        else 0 if handles_retries else (FORGE_REMOTE_RETRY_COUNT if is_remote else FORGE_LOCAL_RETRY_COUNT)
    )
    max_attempts = max(1, retry_count + 1)
    last_exception = None
    resp = None

    for attempt in range(max_attempts):
        # 熔断前置：远程请求前检查是否处于熔断冷却期，避免裸打上游加剧 429 风暴。
        if is_remote:
            cb_wait = await circuit_breaker.before_request()
            if cb_wait > 0:
                logger.warning(f"🛑 熔断冷却中，等待 {cb_wait:.1f}s 后再发（attempt {attempt + 1}/{max_attempts}）")
                await asyncio.sleep(min(cb_wait, _RETRY_AFTER_CAP_SECONDS))

        try:
            port_ctx = _local_port_guard(target_port) if (not is_remote) else _NullContext()
            # 远程请求受并发信号量约束（NIM 免费档并发 ~5），本地请求不限。
            if is_remote:
                async with _remote_concurrency, port_ctx:
                    resp = await http_client.post(target_url, json=forward_payload, headers=headers)
            else:
                async with port_ctx:
                    resp = await http_client.post(target_url, json=forward_payload, headers=headers)

            if resp.status_code == 200:
                if is_remote:
                    await circuit_breaker.on_success()
                return resp, None

            err_body = resp.text[:500] if hasattr(resp, "text") else ""
            last_exception = f"HTTP {resp.status_code}: {err_body}"

            if resp.status_code not in RETRYABLE_STATUS_CODES:
                logger.warning(f"❌ 不可重试状态码 {resp.status_code}，立即失败")
                break

            logger.warning(f"⚠️ 可重试状态码 {resp.status_code}，第 {attempt + 1}/{max_attempts} 次")
            _retry_counters[str(resp.status_code)] = _retry_counters.get(str(resp.status_code), 0) + 1
            if auto_continue and context_too_large:
                _auto_continue_counters["blocked_by_context"] += 1
                last_exception = (
                    f"上下文接近超限，请新开会话 "
                    f"(estimated={context_est}, limit={FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS})"
                )
                break
            if auto_continue and not _auto_continue_status_allowed(resp.status_code, err_body):
                if _is_context_limit_error_text(err_body):
                    last_exception = "上下文接近超限，请新开会话: " + err_body[:300]
                    _auto_continue_counters["blocked_by_context"] += 1
                break
            # 429 喂熔断器：连续 429 达阈值即熔断，打破"重试也 429"的恶性循环。
            # NIM sidecar routes own key-pool/cooldown locally; their 429/503 may
            # mean local busy capacity, so do not trip the Smart Proxy global
            # circuit breaker for handles_retries=True routes.
            if resp.status_code == 429 and is_remote and not handles_retries:
                await circuit_breaker.on_429()
            if attempt < max_attempts - 1:
                if auto_continue:
                    wait = _auto_continue_wait_from_response(resp)
                    _auto_continue_counters["attempts"] += 1
                    _auto_continue_counters["api_error_replays"] += 1
                    _set_auto_continue_last(f"http_{resp.status_code}", wait)
                    logger.warning(
                        f"🔁 auto-continue: upstream status {resp.status_code}, "
                        f"wait {wait:.1f}s then replay request ({attempt + 2}/{max_attempts})"
                    )
                else:
                    wait = _retry_after_seconds(resp, default=_backoff_with_jitter(attempt))
                    logger.info(f"   退避 {wait:.1f}s 后重试")
                await asyncio.sleep(wait)

        except (
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.RemoteProtocolError,
            httpx.PoolTimeout,
        ) as e:
            last_exception = f"{type(e).__name__}: {e}"
            resp = None
            logger.warning(f"⚠️ 远程读/连接异常，第 {attempt + 1}/{max_attempts} 次: {type(e).__name__}: {e}")
            if auto_continue and context_too_large:
                _auto_continue_counters["blocked_by_context"] += 1
                last_exception = (
                    f"上下文接近超限，请新开会话 "
                    f"(estimated={context_est}, limit={FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS})"
                )
                break
            if attempt < max_attempts - 1:
                if auto_continue:
                    wait = FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS
                    _auto_continue_counters["attempts"] += 1
                    _auto_continue_counters["timeout_replays"] += 1
                    _set_auto_continue_last(type(e).__name__, wait)
                    logger.warning(
                        f"🔁 auto-continue: {type(e).__name__}, "
                        f"wait {wait:.1f}s then replay request ({attempt + 2}/{max_attempts})"
                    )
                else:
                    wait = _backoff_with_jitter(attempt)
                await asyncio.sleep(wait)
                continue
            break
        except Exception as e:
            last_exception = f"{type(e).__name__}: {e}"
            resp = None
            logger.warning(f"❌ 非连接类异常: {type(e).__name__}: {e}")
            if auto_continue and not context_too_large and attempt < max_attempts - 1:
                wait = FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS
                _auto_continue_counters["attempts"] += 1
                _auto_continue_counters["timeout_replays"] += 1
                _set_auto_continue_last(type(e).__name__, wait)
                await asyncio.sleep(wait)
                continue
            break

    return resp, last_exception


# ============================================================
# 通用 ping 包装器：用于阶段1工具选择也能被 SSE ping 覆盖（Patch G）
# ============================================================
async def _run_with_ping(coro, ping_interval: float):
    task = asyncio.ensure_future(coro)
    try:
        while True:
            done, _ = await asyncio.wait({task}, timeout=ping_interval)
            if task in done:
                try:
                    yield ("result", task.result())
                except Exception as e:
                    yield ("exception", e)
                return
            yield ("ping", None)
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


# ============================================================
# 流式后端读取生产者（Patch D：后台任务 + 队列，避免阻塞 ping）
# ============================================================
async def _stream_line_producer(target_url, forward_payload, headers, port_ctx, queue: asyncio.Queue,
                                is_remote: bool = False):
    try:
        # 远程请求受并发信号量约束（NIM 免费档并发 ~5），本地请求不限。
        sem = _remote_concurrency if is_remote else _NullContext()
        async with sem, port_ctx:
            async with http_client.stream("POST", target_url, json=forward_payload, headers=headers) as resp:
                if resp.status_code != 200:
                    err_body = (await resp.aread()).decode("utf-8", errors="ignore")
                    # 附带状态码 + Retry-After，供上层在"未发内容"时按可重试状态码有限重试。
                    ra = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
                    await queue.put(("http_error", {
                        "status": resp.status_code,
                        "body": err_body,
                        "retry_after": ra,
                    }))
                    return
                # 200：通知熔断器恢复（half_open 探测成功 → closed）。
                if is_remote:
                    await circuit_breaker.on_success()
                async for line in resp.aiter_lines():
                    if line:
                        await queue.put(("line", line))
    except asyncio.CancelledError:
        raise
    except Exception as e:
        # 带上异常类型名：httpx 的 ReadTimeout/ReadError/RemoteProtocolError 等经常
        # str(e) 为空（日志里"非连接类异常，不重试:"后面空白即此），上层无法据此
        # 区分"可重试的读超时"与"真不可重试的协议错误"。这里把 type 名一并传出，
        # 供 consumer 在"未发内容"时对读类异常按 429 同策略退避重试，避免 turn 空挂。
        await queue.put(("exception", {"message": str(e), "exc_type": type(e).__name__}))
    finally:
        await queue.put(("eof", None))


# ============================================================
# 监控端点
# ============================================================
@app.get("/_forge/status")
async def forge_status():
    active = await tracker.snapshot()
    active_count = sum(1 for item in active if item.get("status") not in {"done", "error"})
    with _last_reduction_lock:
        last_reduction = dict(_last_reduction_info)
    return JSONResponse({
        "proxy": "FORGE Smart Proxy v9.0-patched",
        "active_requests": active_count,
        "requests": active,
        "total_requests": tracker.total_requests,
        "total_errors": tracker.total_errors,
        "rpm_guard": rpm_guard.stats(),
        "local_models": dict(MODEL_TO_PORT),
        "remote_models": list(REMOTE_ROUTES.keys()),
        "tool_selection": {
            "enabled": FORGE_TOOL_SELECTION_ENABLED,
            "threshold": FORGE_TOOL_SELECTION_THRESHOLD,
            "max": FORGE_TOOL_SELECTION_MAX,
            "core_tools": FORGE_CORE_TOOLS,
            "schema_byte_budget": FORGE_TOOL_SCHEMA_BYTE_BUDGET,
            "policy_version": FORGE_TOOL_SELECTOR_POLICY_VERSION,
            "cache": tool_selection_cache.stats(),
            "last_reduction": last_reduction,
            "remote_tool_selection": FORGE_REMOTE_TOOL_SELECTION,
            "remote_selector_port": FORGE_REMOTE_SELECTOR_PORT,
        },
        "retry": {
            "local_retry_count": FORGE_LOCAL_RETRY_COUNT,
            "remote_retry_count": FORGE_REMOTE_RETRY_COUNT,
            "stream_remote_retry_count": FORGE_STREAM_REMOTE_RETRY_COUNT,
            "retryable_status_codes": sorted(RETRYABLE_STATUS_CODES),
            "retry_counters": dict(_retry_counters),
        },
        "auto_continue": {
            "enabled": FORGE_AUTO_CONTINUE_ON_API_ERROR,
            "max_attempts": FORGE_AUTO_CONTINUE_MAX_ATTEMPTS,
            "default_wait_seconds": FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS,
            "max_wait_seconds": FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS,
            "timeout_wait_seconds": FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS,
            "no_output_timeout_seconds": FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS,
            "partial_output_enabled": FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT,
            "context_limit_tokens": FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS,
            "status_codes": "*" if FORGE_AUTO_CONTINUE_ALL_STATUS_CODES else sorted(FORGE_AUTO_CONTINUE_STATUS_CODES),
            "counters": dict(_auto_continue_counters),
            "last": dict(_auto_continue_last),
        },
        "circuit_breaker": circuit_breaker.stats(),
        "remote_concurrency": {
            "max": FORGE_REMOTE_MAX_CONCURRENCY,
        },
        "context_budget": {
            "max_tokens": FORGE_CTX_MAX_TOKENS,
            "soft_tokens": FORGE_CTX_SOFT_TOKENS,
            "soft_ratio": FORGE_CTX_SOFT_RATIO,
            "hard_ratio": FORGE_CTX_HARD_RATIO,
            "keep_recent_turns": FORGE_CTX_KEEP_RECENT_TURNS,
            "trunc_tool_result_chars": FORGE_CTX_TRUNC_TOOL_RESULT_CHARS,
            "counters": dict(_ctx_budget_counters),
            "last": dict(_ctx_budget_last),
        },
        "routing": {
            "allow_unknown_model_fallback": FORGE_ALLOW_UNKNOWN_MODEL_FALLBACK,
        },
        "serialize_local_ports": FORGE_SERIALIZE_LOCAL_PORTS,
    })


@app.get("/_forge/health")
async def forge_health():
    return JSONResponse({"status": "ok", "active": await tracker.active_count()})


# ============================================================
# 主入口
# ============================================================
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_gateway(request: Request, path: str):
    if request.method == "GET":
        return JSONResponse({"status": "ok", "proxy": "v9.0-patched"})

    body = await request.body()
    try:
        data = json.loads(body) if body else {}
    except Exception:
        data = {}

    norm = "/" + path.strip("/")

    # ── 硬约束1：count_tokens 永不进入模型推理，且在路由/ensure_server之前处理 ──
    if norm.endswith("/messages/count_tokens"):
        est = _json_bytes(data) // FORGE_COUNT_TOKENS_DIVISOR if data else 1
        logger.info(f"🧮 count_tokens 估算 {est}（绕过模型推理）")
        return JSONResponse({"input_tokens": max(1, est)})

    is_anthropic = norm.endswith("/v1/messages") or norm.endswith("/messages")
    model_name = normalize_model_name(data.get("model", ""))
    wants_stream = bool(data.get("stream", False))
    request_id = uuid.uuid4().hex[:12]
	

    _record_request_event(
        "request_start",
        request_id,
        model=model_name,
        path=norm,
        stream=wants_stream,
        body_bytes=len(body),
        **_latest_user_message_summary(data if isinstance(data, dict) else {}),
    )

    # ---- Patch(addendum): 固定原始工具数，供后续 remote_full / tool_choice_none 的
    # 可观测性记录使用。必须在任何 tools 字段可能被本地分支改写之前取值。
    _orig_tools_raw = data.get("tools")
    original_tool_count = len(_orig_tools_raw) if isinstance(_orig_tools_raw, list) else 0

    remote_route = REMOTE_ROUTES.get(model_name)
    is_remote = remote_route is not None
    nim_sidecar_route = bool(remote_route and remote_route.get("api_key_optional"))
    target_port = None

    # ── 路由决策 ──
    if is_remote:
        api_key = os.environ.get(remote_route["api_key_env"], "")
        if not api_key and not remote_route.get("api_key_optional"):
            raise HTTPException(503, f"API key {remote_route['api_key_env']} empty")
        if not api_key and remote_route.get("api_key_optional"):
            api_key = "nim-proxy-local"
        # When NVIDIA routes are rewritten to the local NIM sidecar, the sidecar
        # owns per-key RPM/concurrency/cooldown. A second Smart Proxy RPM gate
        # keyed by NIM_PROXY_API_KEY would collapse multi-key capacity back to a
        # single global window, so skip rpm_guard for api_key_optional routes.
        if not remote_route.get("api_key_optional"):
            await rpm_guard.acquire(remote_route["api_key_env"])
        target_url = f"{remote_route['api_base']}/chat/completions"
        remote_model = remote_route["model"]
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        await tracker.start(request_id, model_name, remote_model, True)
    else:
        target_port = MODEL_TO_PORT.get(model_name)
        if target_port is None:
            if FORGE_ALLOW_UNKNOWN_MODEL_FALLBACK:
                target_port = 8080
                logger.warning(f"⚠️ 未知模型 '{model_name}' 回退到 8080（环境变量允许）")
            else:
                logger.error(f"❌ 未知模型 '{model_name}'，拒绝静默路由（文档 §3.3）")
                raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
        # Patch H: ensure_server 是阻塞同步函数，必须放线程池，否则冷启动期间整个事件循环被卡死
        if not await asyncio.to_thread(ensure_server, target_port):
            raise HTTPException(504, "Backend Timeout")
        active_servers[target_port] = time.time()
        target_url = f"http://127.0.0.1:{target_port}/v1/chat/completions"
        remote_model = REAL_ID_MAP.get(target_port, model_name)
        headers = {"Content-Type": "application/json"}
        await tracker.start(request_id, model_name, f"local:{target_port}", False)

    # ── 工具选择决策（本地 + 远程均支持，受开关控制）──
    # 本地：FORGE_TOOL_SELECTION_ENABLED；远程：FORGE_REMOTE_TOOL_SELECTION（默认开）。
    # 远程用专用本地选择器端口(FORGE_REMOTE_SELECTOR_PORT)，不碰远程 target_url。
    needs_deferred_tool_selection = False
    # 默认选择器端口：本地用 target_port，远程用专用本地选择器端口（延迟分支沿用）。
    stream_source_selector_port = target_port if not is_remote else FORGE_REMOTE_SELECTOR_PORT
    tool_selection_active = (not is_remote and FORGE_TOOL_SELECTION_ENABLED) or \
                            (is_remote and FORGE_REMOTE_TOOL_SELECTION)
    if is_anthropic and tool_selection_active:
        tool_choice_raw = data.get("tool_choice")
        if isinstance(tool_choice_raw, dict) and tool_choice_raw.get("type") == "none":
            # 本回合显式禁止工具：不转发 schema，避免无意义 prefill（文档 §9.5）
            data = dict(data)
            data["tools"] = []
        else:
            # 选择器端口：本地用 target_port，远程用专用本地选择器端口。
            selector_port = target_port if not is_remote else FORGE_REMOTE_SELECTOR_PORT
            tools_in = data.get("tools") or []
            large_tool_set = isinstance(tools_in, list) and len(tools_in) > FORGE_TOOL_SELECTION_THRESHOLD
            if wants_stream and large_tool_set:
                # 流式 + 大工具集：把选择推迟到生成器内部执行，以便用 ping 覆盖这段等待（Patch G）
                needs_deferred_tool_selection = True
                # 延迟选择需要 selector_port 在生成器闭包内可见——存到 stream_source_data 上下文
                stream_source_selector_port = selector_port
            else:
                data = await _apply_tool_selection(data, selector_port, remote_model)

    stream_source_data = data  # 供生成器闭包内的延迟工具选择使用

    # ── 构造 forward_payload ──
    if is_anthropic:
        msgs = _convert_anthropic_messages_to_openai(data.get("messages", []))
        sys_prompt = data.get("system", "")
        if sys_prompt:
            if isinstance(sys_prompt, list):
                sys_prompt = "\n".join(
                    b.get("text", "") if isinstance(b, dict) else str(b) for b in sys_prompt)
            msgs.insert(0, {"role": "system", "content": str(sys_prompt)})

        default_max = remote_route.get("max_tokens", 16384) if is_remote else FORGE_LOCAL_DEFAULT_MAX_TOKENS
        cap = FORGE_REMOTE_MAX_TOKENS_CAP if is_remote else FORGE_LOCAL_MAX_TOKENS_CAP

        forward_payload = {
            "model": remote_model,
            "messages": msgs,
            "temperature": data.get("temperature", 0.6),
            "top_p": data.get("top_p", 0.95),
            "stream": wants_stream,
            "max_tokens": _bounded_max_tokens(data.get("max_tokens", default_max), default_max, cap),
        }
        if data.get("stop_sequences"):
            forward_payload["stop"] = data.get("stop_sequences")

        tools = data.get("tools") or []
        tools_fwd = False
        if tools and not needs_deferred_tool_selection:
            should = (is_remote and FORGE_REMOTE_FORWARD_TOOLS) or \
                     ((not is_remote) and FORGE_LOCAL_FORWARD_TOOLS)
            if should:
                forward_payload["tools"] = _anthropic_tools_to_openai(
                    tools, sort_for_cache=FORGE_SORT_TOOLS_FOR_CACHE
                )
                tools_fwd = True
        if data.get("tool_choice") and tools_fwd:
            oc = _anthropic_tool_choice_to_openai(data.get("tool_choice"))
            if oc:
                forward_payload["tool_choice"] = oc
		
		# ---- Patch(addendum): 补齐 §18/§20.5/§9.5 要求的可观测性 ----
        # _apply_tool_selection() 只在"本地 + 非强制tool_choice"路径下被调用并写入
        # _last_reduction_info，导致远程全量转发、以及 tool_choice=none 显式关闭
        # 工具这两种分支此前完全不可观测（/_forge/status 拿不到 selection_mode）。
        # 这里只补记录，不改变任何转发行为。
        tool_choice_val = data.get("tool_choice")
        if is_remote:
            _record_reduction({
                "ts": time.time(),
                "original": original_tool_count,
                "final": len(tools) if tools_fwd else 0,
                "selected": sorted(
                    t.get("name", "") for t in tools if isinstance(t, dict)
                ) if tools_fwd else [],
                "mode": "remote_full" if tools_fwd else "remote_no_tools",
            })
        elif isinstance(tool_choice_val, dict) and tool_choice_val.get("type") == "none":
            _record_reduction({
                "ts": time.time(),
                "original": original_tool_count,
                "final": 0,
                "selected": [],
                "mode": "tool_choice_none",
            })
		
		# 补齐完毕
		
        logger.info(
            f"📏 [{request_id}] model={model_name} remote={is_remote} "
            f"deferred={needs_deferred_tool_selection} "
            f"tools_in_payload={len(forward_payload.get('tools', []))} body_bytes={len(body)}"
        )
    else:
        forward_payload = data.copy() if isinstance(data, dict) else {}
        forward_payload["model"] = remote_model
        forward_payload.setdefault("temperature", 0.6)
        forward_payload.setdefault("top_p", 0.95)
        forward_payload.setdefault("stream", False)
        cap = FORGE_REMOTE_MAX_TOKENS_CAP if is_remote else FORGE_LOCAL_MAX_TOKENS_CAP
        def_max = remote_route.get("max_tokens", 16384) if is_remote else FORGE_LOCAL_DEFAULT_MAX_TOKENS
        forward_payload["max_tokens"] = _bounded_max_tokens(
            forward_payload.get("max_tokens", def_max), def_max, cap)

    # ── 上下文预算 guard：转发前估算 messages token 数，防上游超长 400 ──
    # 400 不在 RETRYABLE_STATUS_CODES 内，重试无效；故在源头拦截。
    # 达 SOFT(80%) 结构化裁剪历史，达 HARD(95%) 裁剪后仍超限则拒绝并提示 /compact。
    _ctx_action, _ctx_est_before, _ctx_est_after, _ctx_hint = _apply_context_budget(forward_payload)
    _ctx_budget_counters[_ctx_action] = _ctx_budget_counters.get(_ctx_action, 0) + 1
    _ctx_budget_last.update(
        {"action": _ctx_action, "est_before": _ctx_est_before, "est_after": _ctx_est_after}
    )
    if _ctx_action == "rejected":
        # 裁剪后仍超 HARD：直接拒绝，避免 400 透传 + 无意义重试
        logger.error(
            f"🛑 [{request_id}] context budget rejected: "
            f"{_ctx_est_before}→{_ctx_est_after}/{FORGE_CTX_MAX_TOKENS} tokens"
        )
        raise HTTPException(
            status_code=400,
            detail={
                "type": "context_too_large",
                "message": _ctx_hint,
                "est_tokens": _ctx_est_after,
                "max_context_tokens": FORGE_CTX_MAX_TOKENS,
            },
        )
    if _ctx_action == "compacted":
        logger.warning(
            f"🗜️ [{request_id}] context budget compacted: "
            f"{_ctx_est_before}→{_ctx_est_after}/{FORGE_CTX_MAX_TOKENS} tokens"
        )
        # 把提示注入 system message（Anthropic 客户端会显示给用户），不破坏对话结构
        _compact_hint_msg = {
            "role": "system",
            "content": _ctx_hint,
        }
        msgs_now = forward_payload.get("messages")
        if isinstance(msgs_now, list):
            forward_payload["messages"] = [_compact_hint_msg] + msgs_now

    auto_ctx_too_large, auto_ctx_est = _auto_continue_context_too_large(forward_payload)
    if auto_ctx_too_large:
        notice_text = (
            "上下文接近超限，请新开会话"
            f"（estimated={auto_ctx_est}, limit={FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS}）。"
        )
        _auto_continue_counters["blocked_by_context"] += 1
        _record_request_event("request_context_limit", request_id, estimated_tokens=auto_ctx_est, limit=FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS)
        await tracker.finish(request_id, success=False)
        await tracker.remove(request_id)
        if is_anthropic:
            if wants_stream:
                async def context_limit_event_stream():
                    msg_id = f"msg_{uuid.uuid4().hex}"
                    yield _anthropic_sse("message_start", {
                        "type": "message_start",
                        "message": {
                            "id": msg_id, "type": "message", "role": "assistant", "model": model_name,
                            "content": [], "stop_reason": None, "stop_sequence": None,
                            "usage": {"input_tokens": int(auto_ctx_est), "output_tokens": 0},
                        },
                    })
                    yield _anthropic_sse("content_block_start", {
                        "type": "content_block_start", "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    })
                    yield _anthropic_sse("content_block_delta", {
                        "type": "content_block_delta", "index": 0,
                        "delta": {"type": "text_delta", "text": notice_text},
                    })
                    yield _anthropic_sse("content_block_stop", {"type": "content_block_stop", "index": 0})
                    yield _anthropic_sse("message_delta", {
                        "type": "message_delta",
                        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": max(1, len(notice_text) // 4)},
                    })
                    yield _anthropic_sse("message_stop", {"type": "message_stop"})
                return StreamingResponse(context_limit_event_stream(), media_type="text/event-stream")
            return JSONResponse({
                "id": f"msg_{uuid.uuid4().hex}",
                "type": "message",
                "role": "assistant",
                "model": model_name,
                "content": [{"type": "text", "text": notice_text}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": int(auto_ctx_est), "output_tokens": max(1, len(notice_text) // 4)},
            })
        raise HTTPException(status_code=400, detail=notice_text)

    # ============ 流式响应 ============
    if is_anthropic and forward_payload.get("stream"):
        await tracker.update(request_id, status="connecting")

        async def anthropic_event_stream():
            msg_id = f"msg_{uuid.uuid4().hex}"
            est_in = max(1, _json_bytes(stream_source_data.get("messages", [])) // 4)
            yield _anthropic_sse("message_start", {
                "type": "message_start",
                "message": {
                    "id": msg_id, "type": "message", "role": "assistant", "model": model_name,
                    "content": [], "stop_reason": None, "stop_sequence": None,
                    "usage": {"input_tokens": est_in, "output_tokens": 0},
                },
            })

            # ── 延迟工具选择：全程用 ping 覆盖，避免冷启动期间客户端裸等（Patch G）──
            if needs_deferred_tool_selection:
                # 选择器端口：本地用 target_port，远程用专用本地选择器端口（决策时存入）。
                deferred_selector_port = stream_source_selector_port
                async for kind, payload in _run_with_ping(
                    _apply_tool_selection(stream_source_data, deferred_selector_port, remote_model),
                    FORGE_STREAM_PING_INTERVAL_SECONDS,
                ):
                    if kind == "ping":
                        yield _anthropic_sse("ping", {"type": "ping"})
                        await tracker.heartbeat(request_id, 0)
                    elif kind == "exception":
                        logger.warning(f"⚠️ 阶段1工具选择异常（理论上已被内部兜底吸收）: {payload}")
                    elif kind == "result":
                        resolved = payload
                        r_tools = resolved.get("tools") or []
                        if r_tools:
                            forward_payload["tools"] = _anthropic_tools_to_openai(
                                r_tools, sort_for_cache=FORGE_SORT_TOOLS_FOR_CACHE
                            )
                            rc = resolved.get("tool_choice")
                            if rc:
                                oc = _anthropic_tool_choice_to_openai(rc)
                                if oc:
                                    forward_payload["tool_choice"] = oc

            raw_lines = []
            tool_calls_data = {}
            emitted_text = False
            text_content = ""
            finish_reason = None
            usage_output = 0
            stream_error = None

            port_ctx = _local_port_guard(target_port) if (not is_remote) else _NullContext()
            stream_context_too_large, stream_context_est = _auto_continue_context_too_large(forward_payload)
            stream_auto_continue = bool(
                nim_sidecar_route
                and FORGE_AUTO_CONTINUE_ON_API_ERROR
                and FORGE_AUTO_CONTINUE_MAX_ATTEMPTS > 0
                and not stream_context_too_large
            )
            stream_attempts = (
                1 + FORGE_AUTO_CONTINUE_MAX_ATTEMPTS
                if stream_auto_continue
                else 1 if nim_sidecar_route else ((FORGE_STREAM_REMOTE_RETRY_COUNT + 1) if is_remote else 1)
            )
            stream_forward_payload = forward_payload

            try:
                for _stream_attempt in range(stream_attempts):
                    attempt_started_at = time.time()
                    last_real_output_at = time.time()
                    # 熔断前置：远程流式请求前检查冷却期，避免裸打上游加剧 429 风暴。
                    if is_remote:
                        cb_wait = await circuit_breaker.before_request()
                        if cb_wait > 0:
                            logger.warning(f"🛑 流式熔断冷却中，等待 {cb_wait:.1f}s（attempt {_stream_attempt + 1}/{stream_attempts}）")
                            # 冷却期间持续向客户端发 ping，保持连接不超时。
                            deadline = time.time() + min(cb_wait, _RETRY_AFTER_CAP_SECONDS)
                            while time.time() < deadline:
                                yield _anthropic_sse("ping", {"type": "ping"})
                                await asyncio.sleep(FORGE_STREAM_PING_INTERVAL_SECONDS)
                    queue = asyncio.Queue()
                    producer = asyncio.create_task(
                        _stream_line_producer(target_url, stream_forward_payload, headers, port_ctx, queue,
                                              is_remote=is_remote)
                    )
                    _stream_retry_pending = False

                    try:
                        await tracker.update(request_id, status="generating")

                        while True:
                            try:
                                kind, item = await asyncio.wait_for(
                                    queue.get(), timeout=FORGE_STREAM_PING_INTERVAL_SECONDS
                                )
                            except asyncio.TimeoutError:
                                no_real_output_elapsed = time.time() - (last_real_output_at if emitted_text else attempt_started_at)
                                no_output_timed_out = (
                                    FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS > 0
                                    and no_real_output_elapsed >= FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS
                                )
                                if no_output_timed_out and not tool_calls_data:
                                    if stream_auto_continue and _stream_attempt < stream_attempts - 1:
                                        wait = FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS
                                        _auto_continue_counters["attempts"] += 1
                                        if emitted_text and FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT:
                                            _auto_continue_counters["partial_replays"] += 1
                                            stream_forward_payload = _build_partial_continue_payload(forward_payload, text_content)
                                            reason = "partial_no_output_timeout"
                                        elif not emitted_text:
                                            _auto_continue_counters["no_output_replays"] += 1
                                            reason = "no_output_timeout"
                                        else:
                                            stream_error = {
                                                "message": "stream stalled after tool output; transparent replay disabled",
                                                "type": "NoOutputTimeout",
                                            }
                                            break
                                        _set_auto_continue_last(reason, wait, request_id)
                                        logger.warning(
                                            f"🔁 auto-continue: {reason}, no real output for "
                                            f"{no_real_output_elapsed:.1f}s, wait {wait:.1f}s then replay "
                                            f"({_stream_attempt + 2}/{stream_attempts})"
                                        )
                                        await asyncio.sleep(wait)
                                        _stream_retry_pending = True
                                        break
                                    stream_error = {
                                        "message": (
                                            f"Request timed out after {FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS:.0f}s "
                                            "without model text/tool output"
                                        ),
                                        "type": "NoOutputTimeout",
                                    }
                                    break
                                yield _anthropic_sse("ping", {"type": "ping"})
                                await tracker.heartbeat(request_id, 0)
                                continue

                            if kind == "eof":
                                break
                            if kind in ("http_error", "exception"):
                                # 连接期错误：可重试状态码且尚未发任何内容时，有限重试。
                                # 一旦 emitted_text/tool_calls_data 已有内容，绝不重试（文档 §12）。
                                # 读类异常（ReadTimeout/ReadError/RemoteProtocolError 等，常空 message）
                                # 在未发内容时同样退避重试——这是"空响应/turn 空挂 20 分钟"的真凶。
                                body_for_status = str((item or {}).get("body", "")) if isinstance(item, dict) else str(item)
                                pre_content_retry = (
                                    not emitted_text
                                    and not tool_calls_data
                                    and stream_auto_continue
                                    and _stream_attempt < stream_attempts - 1
                                    and (
                                        (kind == "http_error"
                                         and isinstance(item, dict)
                                         and _auto_continue_status_allowed(item.get("status"), body_for_status))
                                        or (kind == "exception"
                                            and isinstance(item, dict)
                                            and item.get("exc_type") in _STREAM_RETRYABLE_EXC_TYPES)
                                    )
                                )
                                partial_retry = (
                                    emitted_text
                                    and not tool_calls_data
                                    and FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT
                                    and stream_auto_continue
                                    and _stream_attempt < stream_attempts - 1
                                )
                                if pre_content_retry or partial_retry:
                                    if kind == "http_error":
                                        status = item.get("status")
                                        _retry_counters[str(status)] = _retry_counters.get(str(status), 0) + 1
                                        label = f"上游 {status}"
                                        wait = _retry_after_seconds_from_value(
                                            item.get("retry_after"),
                                            default=FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS,
                                            cap=FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS,
                                        )
                                        _auto_continue_counters["api_error_replays"] += 1
                                    else:  # exception（读类异常）
                                        label = f"读异常 {item.get('exc_type')}"
                                        wait = FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS
                                        _auto_continue_counters["timeout_replays"] += 1
                                    if partial_retry:
                                        stream_forward_payload = _build_partial_continue_payload(forward_payload, text_content)
                                        _auto_continue_counters["partial_replays"] += 1
                                        label = f"partial {label}"
                                    _auto_continue_counters["attempts"] += 1
                                    _set_auto_continue_last(label, wait, request_id)
                                    logger.warning(
                                        f"🔁 auto-continue: 流式{label}，"
                                        f"第 {_stream_attempt + 1}/{stream_attempts} 次，等待 {wait:.1f}s 后重放"
                                    )
                                    await asyncio.sleep(wait)
                                    _stream_retry_pending = True
                                    break
                                stream_error = item
                                break

                            line = item
                            raw_lines.append(line)
                            await tracker.heartbeat(request_id, len(line.encode("utf-8", "ignore")))
                            if not line.startswith("data:"):
                                continue
                            raw = line[5:].strip()
                            if raw == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(raw)
                            except Exception:
                                continue
                            if isinstance(chunk, dict) and chunk.get("error") and not chunk.get("choices"):
                                error_payload = chunk.get("error") or chunk
                                error_text = json.dumps(error_payload, ensure_ascii=False)
                                can_retry_error_payload = (
                                    not tool_calls_data
                                    and stream_auto_continue
                                    and _stream_attempt < stream_attempts - 1
                                    and not _is_context_limit_error_text(error_text)
                                )
                                if can_retry_error_payload:
                                    if emitted_text and FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT:
                                        stream_forward_payload = _build_partial_continue_payload(forward_payload, text_content)
                                        _auto_continue_counters["partial_replays"] += 1
                                        reason = "partial_sidecar_sse_error"
                                        wait_default = FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS
                                    else:
                                        reason = "sidecar_sse_error"
                                        wait_default = FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS
                                    wait = _retry_after_seconds_from_error_payload(
                                        error_payload,
                                        default=wait_default,
                                    )
                                    _auto_continue_counters["attempts"] += 1
                                    _auto_continue_counters["api_error_replays"] += 1
                                    _set_auto_continue_last(reason, wait, request_id)
                                    logger.warning(
                                        f"🔁 auto-continue: {reason}, "
                                        f"wait {wait:.1f}s then replay stream "
                                        f"({_stream_attempt + 2}/{stream_attempts})"
                                    )
                                    await asyncio.sleep(wait)
                                    _stream_retry_pending = True
                                    break
                                if _is_context_limit_error_text(error_text):
                                    _auto_continue_counters["blocked_by_context"] += 1
                                    error_payload = {
                                        "message": "上下文接近超限，请新开会话",
                                        "type": "context_limit",
                                    }
                                stream_error = error_payload
                                break

                            usage_chunk = chunk.get("usage")
                            if isinstance(usage_chunk, dict):
                                usage_output = usage_chunk.get("completion_tokens", usage_output)

                            for choice in chunk.get("choices", []):
                                fr = choice.get("finish_reason")
                                if fr:
                                    finish_reason = fr
                                delta = choice.get("delta", {}) or {}

                                text = delta.get("content")
                                if text:
                                    if not emitted_text:
                                        yield _anthropic_sse("content_block_start", {
                                            "type": "content_block_start", "index": 0,
                                            "content_block": {"type": "text", "text": ""},
                                        })
                                        emitted_text = True
                                    text_content += text
                                    last_real_output_at = time.time()
                                    yield _anthropic_sse("content_block_delta", {
                                        "type": "content_block_delta", "index": 0,
                                        "delta": {"type": "text_delta", "text": text},
                                    })

                                tc_list = delta.get("tool_calls")
                                if tc_list:
                                    last_real_output_at = time.time()
                                    for tc in tc_list:
                                        idx = tc.get("index", 0)
                                        func = tc.get("function", {}) or {}
                                        if idx not in tool_calls_data:
                                            raw_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                                            tool_calls_data[idx] = {
                                                "id": _to_anthropic_tool_id(raw_id),
                                                "name": "", "arguments": "",
                                            }
                                        entry = tool_calls_data[idx]
                                        if tc.get("id"):
                                            entry["id"] = _to_anthropic_tool_id(tc["id"])
                                        entry["name"] += str(func.get("name") or "")
                                        entry["arguments"] += str(func.get("arguments") or "")

                    finally:
                        if not producer.done():
                            producer.cancel()
                            with contextlib.suppress(asyncio.CancelledError):
                                await producer

                    if _stream_retry_pending:
                        # 清空本轮残留，进入下一次 for 迭代重新建连
                        raw_lines = []
                        continue
                    # 正常 eof、不可重试错误、或已发内容后断流：不再重试
                    break

                # for 循环结束：所有重试耗尽或正常退出。stream_error 收尾与 fallback 在此处理。
                if stream_error:
                    logger.error(f"❌ 后端流式错误: {stream_error}")
                    if not emitted_text and not tool_calls_data:
                        yield _anthropic_sse("error", {
                            "type": "error", "error": {"type": "api_error", "message": str(stream_error)},
                        })
                        await tracker.finish(request_id, success=False)
                        return
                    # 已经向客户端发送过内容：不允许透明重试，只能尽量收尾（文档 §12）
                    finish_reason = finish_reason or "error"

                # fallback：后端未走真正 SSE，返回一次性完整 JSON（文档 §11.6）
                if not emitted_text and not tool_calls_data and raw_lines and not stream_error:
                    merged = "\n".join(raw_lines).strip()
                    parsed = None
                    try:
                        parsed = json.loads(merged)
                    except Exception:
                        merged2 = "\n".join(
                            l[5:].strip() for l in raw_lines
                            if l.startswith("data:") and l[5:].strip() != "[DONE]"
                        )
                        try:
                            parsed = json.loads(merged2) if merged2 else None
                        except Exception:
                            parsed = None
                    if isinstance(parsed, dict):
                        usage_p = parsed.get("usage", {}) or {}
                        usage_output = usage_p.get("completion_tokens", usage_output)
                        for choice in parsed.get("choices", []):
                            msg = choice.get("message", {}) or {}
                            fr = choice.get("finish_reason")
                            if fr:
                                finish_reason = fr
                            if msg.get("content"):
                                text_content += str(msg["content"])
                            for i, tc in enumerate(msg.get("tool_calls") or []):
                                func = tc.get("function", {}) or {}
                                raw_id = tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                                tool_calls_data[i] = {
                                    "id": _to_anthropic_tool_id(raw_id),
                                    "name": func.get("name", ""),
                                    "arguments": func.get("arguments", "") or "",
                                }
                    if text_content and not emitted_text:
                        yield _anthropic_sse("content_block_start", {
                            "type": "content_block_start", "index": 0,
                            "content_block": {"type": "text", "text": ""},
                        })
                        yield _anthropic_sse("content_block_delta", {
                            "type": "content_block_delta", "index": 0,
                            "delta": {"type": "text_delta", "text": text_content},
                        })
                        emitted_text = True

                if emitted_text:
                    yield _anthropic_sse("content_block_stop", {"type": "content_block_stop", "index": 0})

                content_index = 1 if emitted_text else 0
                for idx in sorted(tool_calls_data.keys()):
                    tc = tool_calls_data[idx]
                    try:
                        arguments = json.loads(tc["arguments"] or "{}")
                    except Exception:
                        arguments = {"raw": tc["arguments"]}
                    yield _anthropic_sse("content_block_start", {
                        "type": "content_block_start", "index": content_index,
                        "content_block": {"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": {}},
                    })
                    yield _anthropic_sse("content_block_delta", {
                        "type": "content_block_delta", "index": content_index,
                        "delta": {"type": "input_json_delta", "partial_json": json.dumps(arguments, ensure_ascii=False)},
                    })
                    yield _anthropic_sse("content_block_stop", {"type": "content_block_stop", "index": content_index})
                    content_index += 1

                # usage 兜底估算（文档 §11.9）：后端不提供时不能永远为 0
                if usage_output <= 0:
                    approx_chars = len(text_content) + sum(
                        len(tc.get("arguments", "")) for tc in tool_calls_data.values()
                    )
                    if approx_chars > 0:
                        usage_output = max(1, approx_chars // 4)

                stop_reason = (
                    "tool_use" if (finish_reason == "tool_calls" or tool_calls_data)
                    else "max_tokens" if finish_reason == "length"
                    else "end_turn"
                )
                yield _anthropic_sse("message_delta", {
                    "type": "message_delta",
                    "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                    "usage": {"output_tokens": int(usage_output or 0)},
                })
                yield _anthropic_sse("message_stop", {"type": "message_stop"})

                _record_request_event(
                    "request_finish",
                    request_id,
                    success=True,
                    stream=True,
                    elapsed_s=round(time.time() - tracker.requests.get(request_id, {}).get("start", time.time()), 3) if hasattr(tracker, "requests") else 0,
                    output_chars=len(text_content),
                    stop_reason=stop_reason,
                )
                await tracker.finish(request_id, success=True)

            except asyncio.CancelledError:
                logger.warning(f"客户端断开连接: model={model_name}")
                _record_request_event("request_cancelled", request_id, stream=True, model=model_name)
                await tracker.finish(request_id, success=False)
                raise
            except Exception as exc:
                logger.error(f"❌ 流式请求异常: {exc}")
                _record_request_event("request_error", request_id, stream=True, error_type=type(exc).__name__, error=str(exc))
                await tracker.finish(request_id, success=False)
                yield _anthropic_sse("error", {"type": "error", "error": {"type": "api_error", "message": str(exc)}})
            finally:
                await asyncio.sleep(0.1)
                await tracker.remove(request_id)

        return StreamingResponse(
            anthropic_event_stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # ============ 非流式响应 ============
    resp, last_exception = await _forward_with_retries(
        target_url, forward_payload, headers, is_remote, target_port, handles_retries=nim_sidecar_route
    )

    if resp is None or resp.status_code != 200:
        logger.error(f"❌ 转发最终失败: {last_exception}")
        _record_request_event(
            "request_error",
            request_id,
            stream=False,
            status_code=getattr(resp, "status_code", None),
            error=str(last_exception),
        )
        await tracker.finish(request_id, success=False)
        await tracker.remove(request_id)
        if last_exception and "上下文接近超限" in str(last_exception) and is_anthropic:
            return JSONResponse({
                "id": f"msg_{uuid.uuid4().hex}", "type": "message", "role": "assistant",
                "model": model_name,
                "content": [{"type": "text", "text": "上下文接近超限，请新开会话"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": max(1, _json_bytes(forward_payload.get("messages", [])) // 4), "output_tokens": 8},
            })
        raise HTTPException(status_code=504, detail=f"Backend failed: {last_exception}")

    res_json = resp.json()

    if not is_anthropic:
        _record_request_event("request_finish", request_id, success=True, stream=False, output_chars=_json_bytes(res_json))
        await tracker.finish(request_id, success=True)
        await tracker.remove(request_id)
        return JSONResponse(res_json)

    choice = res_json.get("choices", [{}])[0]
    message = choice.get("message", {}) or {}
    usage = res_json.get("usage", {}) or {}
    openai_content = message.get("content") or ""
    openai_tool_calls = message.get("tool_calls")
    openai_finish = choice.get("finish_reason", "stop")

    anthropic_content = []
    if openai_content:
        anthropic_content.append({"type": "text", "text": str(openai_content)})
    if openai_tool_calls:
        anthropic_content.extend(_openai_tool_calls_to_anthropic(openai_tool_calls))

    if openai_finish == "tool_calls" or openai_tool_calls:
        stop_reason = "tool_use"
    elif openai_finish == "length":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"

    input_tokens = int(usage.get("prompt_tokens", 0) or 0)
    output_tokens = int(usage.get("completion_tokens", 0) or 0)

    # usage 兜底估算（文档 §11.9）
    if input_tokens <= 0:
        input_tokens = max(1, _json_bytes(forward_payload.get("messages", [])) // 4)
    if output_tokens <= 0:
        out_text = str(openai_content or "")
        out_text += "".join(
            (tc.get("function", {}) or {}).get("arguments", "")
            for tc in (openai_tool_calls or []) if isinstance(tc, dict)
        )
        if out_text:
            output_tokens = max(1, len(out_text) // 4)

    _record_request_event("request_finish", request_id, success=True, stream=False, output_chars=len(str(openai_content or "")), stop_reason=stop_reason)
    await tracker.finish(request_id, success=True)
    await tracker.remove(request_id)

    return JSONResponse({
        "id": f"msg_{uuid.uuid4().hex}", "type": "message", "role": "assistant",
        "model": model_name, "content": anthropic_content, "stop_reason": stop_reason,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")