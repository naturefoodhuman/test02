#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 23:45:00

"""
大规模搜索引擎风控压测与反爬特征诊断工具 (Risk Control Diagnostic Suite)

用途：
在本地 Mac 真实网络环境（直连或宿主机 Clash 分流代理）下，并发/逐一测试 SearXNG 支持的
核心搜索引擎的风控响应特征（如 CAPTCHA、429 限流、IP 封禁、空结果等），为反爬策略与
容错降级路由提供数据决策支持。

运行方式（需在开启 SearXNG 容器的 Mac 真机执行）：
python3 scripts/diagnostics/test_engine_risk_control.py --base-url http://127.0.0.1:8090
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Any
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("engine_risk_test")

ENGINES_TO_TEST = [
    "google",
    "duckduckgo",
    "brave",
    "startpage",
    "bing",
    "yahoo",
    "qwant",
    "wikipedia",
    "github",
    "arxiv",
    "stackoverflow"
]

TEST_QUERIES = [
    "python langgraph",
    "macos m1 max artificial intelligence",
    "deep learning mcp protocol"
]

class EngineTestResult:
    def __init__(self, engine: str):
        self.engine = engine
        self.total_queries = 0
        self.success_count = 0
        self.captcha_count = 0
        self.rate_limit_count = 0
        self.empty_count = 0
        self.error_count = 0
        self.avg_latency_ms = 0.0
        self.raw_errors: List[str] = []

    def status_summary(self) -> str:
        if self.captcha_count > 0:
            return "🔴 CRITICAL (CAPTCHA Blocked)"
        if self.rate_limit_count > 0:
            return "🟡 WARNING (429 Rate Limited)"
        if self.error_count > 0:
            return f"❌ ERROR ({self.raw_errors[0] if self.raw_errors else 'Unknown'})"
        if self.success_count == 0 or self.empty_count == self.total_queries:
            return "⚪ EMPTY (No results returned)"
        return "🟢 PASS (Stable & Healthy)"

async def test_single_engine(client: httpx.AsyncClient, engine: str, queries: List[str]) -> EngineTestResult:
    result = EngineTestResult(engine)
    latencies = []
    
    for q in queries:
        result.total_queries += 1
        start_time = time.perf_counter()
        params = {"q": q, "format": "json", "engines": engine, "limit": 5}
        
        try:
            resp = await client.get("/search", params=params, timeout=12.0)
            elapsed = (time.perf_counter() - start_time) * 1000
            latencies.append(elapsed)
            
            if resp.status_code == 429:
                result.rate_limit_count += 1
                result.raw_errors.append("HTTP 429 Too Many Requests")
                continue
            elif resp.status_code in (403, 503):
                result.captcha_count += 1
                result.raw_errors.append(f"HTTP {resp.status_code} Forbidden/Service Unavailable")
                continue
                
            data = resp.json()
            unresponsive = data.get("unresponsive_engines", [])
            
            # 检测 SearXNG 结构化报错
            engine_err = None
            for item in unresponsive:
                if isinstance(item, list) and len(item) >= 2 and item[0].lower() == engine.lower():
                    engine_err = str(item[1])
                    break
                elif engine.lower() in str(item).lower():
                    engine_err = str(item)
                    break
                    
            if engine_err:
                err_lower = engine_err.lower()
                if "captcha" in err_lower or "challenge" in err_lower or "bot" in err_lower:
                    result.captcha_count += 1
                    result.raw_errors.append(f"Upstream CAPTCHA: {engine_err}")
                elif "too many requests" in err_lower or "limit" in err_lower or "suspended" in err_lower:
                    result.rate_limit_count += 1
                    result.raw_errors.append(f"Upstream Suspended/Limit: {engine_err}")
                else:
                    result.error_count += 1
                    result.raw_errors.append(engine_err)
            else:
                res_list = data.get("results", [])
                if len(res_list) > 0:
                    result.success_count += 1
                else:
                    result.empty_count += 1
                    
        except httpx.TimeoutException:
            result.error_count += 1
            result.raw_errors.append("Request Timeout (>12s)")
        except Exception as e:
            result.error_count += 1
            result.raw_errors.append(f"Client Exception: {repr(e)}")
            
        await asyncio.sleep(0.5) # 请求间隔防连发限制

    if latencies:
        result.avg_latency_ms = sum(latencies) / len(latencies)
    return result

async def run_diagnostic(base_url: str):
    logger.info(f"🚀 开始搜索引擎风控大规模压测诊断，目标节点: {base_url}")
    logger.info(f"本次压测引擎池 ({len(ENGINES_TO_TEST)} 个): {ENGINES_TO_TEST}")
    
    async with httpx.AsyncClient(base_url=base_url, headers={"User-Agent": "Mozilla/5.0"}, trust_env=False) as client:
        # 先做一次 ping 测试
        try:
            ping_res = await client.get("/search", params={"q": "ping", "format": "json"}, timeout=5.0)
            if ping_res.status_code != 200:
                logger.error(f"❌ SearXNG 节点未响应正常状态码: {ping_res.status_code}")
                return
        except Exception as e:
            logger.error(f"❌ 无法连接至 SearXNG 服务 ({base_url})。请确认容器已启动: {e}")
            return

        tasks = [test_single_engine(client, eng, TEST_QUERIES) for eng in ENGINES_TO_TEST]
        results: List[EngineTestResult] = await asyncio.gather(*tasks)

    print("\n" + "="*85)
    print(f"{'搜索引擎 (Engine)':<18} | {'状态评估 (Risk Assessment)':<30} | {'成功率':<10} | {'平均耗时':<10}")
    print("="*85)
    
    stable_engines = []
    risky_engines = []
    
    for r in results:
        rate_str = f"{r.success_count}/{r.total_queries}"
        lat_str = f"{r.avg_latency_ms:.1f}ms" if r.avg_latency_ms > 0 else "-"
        print(f"{r.engine:<18} | {r.status_summary():<30} | {rate_str:<10} | {lat_str:<10}")
        if r.raw_errors:
            print(f"   ↳ 异常明细: {r.raw_errors[0]}")
            
        if r.success_count > 0 and r.captcha_count == 0 and r.rate_limit_count == 0:
            stable_engines.append(r.engine)
        else:
            risky_engines.append((r.engine, r.status_summary()))

    print("="*85)
    print("\n📊 【诊断决策与反爬建议总结】")
    print(f"1. 当前环境推荐白名单稳定引擎池 ({len(stable_engines)} 个): {stable_engines}")
    print(f"2. 高风险/已被封禁引擎 ({len(risky_engines)} 个): {[e[0] for e in risky_engines]}")
    print("3. 反爬策略落地优化指南：")
    print("   - 针对 CAPTCHA/429 引擎，建议在 settings.yml 中显式设置 disabled: true 或增大请求回避周期。")
    print("   - SearXNGProvider 查询链路已开启智能退避路由：若通用引擎报 CAPTCHA 导致空结果，自动重定向至稳定白名单池。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="搜索引擎风控诊断工具")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090", help="SearXNG 服务地址")
    args = parser.parse_args()
    
    asyncio.run(run_diagnostic(args.base_url))
