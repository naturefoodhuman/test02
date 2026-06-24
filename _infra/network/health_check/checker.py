# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:20:00 CST

"""
Health Checker（FORGE Network 增量）

当前实现：
- 验证核心配置是否可加载
- 报告基本状态
- 预留服务探针扩展点（SearXNG / Crawl4AI / Ollama 等）

用法示例：
    from _infra.network.health_check.checker import check_health
    report = check_health()
    print(report["status"])
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List

from ..config_loader import load_network_config, NetworkConfigError
from ..exceptions import ConfigError


@dataclass
class HealthReport:
    status: str                    # "healthy" | "degraded" | "unhealthy"
    checks: Dict[str, Any]
    errors: List[str]
    version: str = "0.1.0-incr"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


import httpx
import asyncio
import subprocess
from ..search.searxng_client import SearXNGProvider
from ..extract.crawl4ai_client import Crawl4AIProvider

def check_config() -> Dict[str, Any]:
    """检查 network 配置是否可加载"""
    try:
        cfg = load_network_config()
        return {
            "name": "config",
            "status": "ok",
            "details": {
                "version": cfg.version,
                "searxng_url": cfg.search.searxng.base_url,
                "crawl4ai_url": cfg.extract.crawl4ai.base_url,
            }
        }
    except (NetworkConfigError, Exception) as e:
        return {
            "name": "config",
            "status": "fail",
            "error": str(e)
        }

async def check_searxng(cfg) -> Dict[str, Any]:
    try:
        async with SearXNGProvider(config=cfg.search.searxng) as provider:
            ok = await provider.health_check()
            return {
                "name": "searxng",
                "status": "ok" if ok else "fail",
                "details": {"url": cfg.search.searxng.base_url}
            }
    except Exception as e:
        return {"name": "searxng", "status": "fail", "error": str(e)}

async def check_crawl4ai(cfg) -> Dict[str, Any]:
    try:
        async with Crawl4AIProvider(config=cfg.extract.crawl4ai) as provider:
            ok = await provider.health_check()
            return {
                "name": "crawl4ai",
                "status": "ok" if ok else "fail",
                "details": {"url": cfg.extract.crawl4ai.base_url}
            }
    except Exception as e:
        return {"name": "crawl4ai", "status": "fail", "error": str(e)}

async def check_ollama(cfg) -> Dict[str, Any]:
    try:
        # Check if ollama is running by calling list or ps
        process = await asyncio.create_subprocess_exec(
            "ollama", "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return {"name": "ollama", "status": "ok"}
        else:
            return {"name": "ollama", "status": "fail", "error": stderr.decode()}
    except Exception as e:
        return {"name": "ollama", "status": "fail", "error": str(e)}

def check_health() -> HealthReport:
    """执行基础健康检查"""
    checks = []
    errors = []

    # 1. Config Check (Sync)
    config_check = check_config()
    checks.append(config_check)
    if config_check["status"] != "ok":
        errors.append(config_check.get("error", "config load failed"))
        return HealthReport(status="unhealthy", checks={"config": config_check}, errors=errors)

    cfg = load_network_config()

    # 2. Async Checks
    async def run_async_checks():
        return await asyncio.gather(
            check_searxng(cfg),
            check_crawl4ai(cfg),
            check_ollama(cfg)
        )

    async_results = asyncio.run(run_async_checks())
    for res in async_results:
        checks.append(res)
        if res["status"] != "ok":
            errors.append(f"{res['name']} check failed: {res.get('error', 'unknown error')}")

    if not errors:
        status = "healthy"
    elif any(c["status"] == "ok" for c in checks if c["name"] != "config"):
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthReport(
        status=status,
        checks={c["name"]: c for c in checks},
        errors=errors,
    )


def print_health_report(report: HealthReport) -> None:
    """简单打印报告（CLI 友好）"""
    print(f"Network Health: {report.status.upper()}")
    for name, check in report.checks.items():
        emoji = "✅" if check.get("status") == "ok" else "❌"
        print(f"  {emoji} {name}: {check.get('status')}")
        if "error" in check:
            print(f"     error: {check['error']}")
    if report.errors:
        print(f"\nErrors: {len(report.errors)}")
