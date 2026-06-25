#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
Risk-Control Diagnostic Suite v2 for SearXNG engines.

Enhancements:
1. CAPTCHA / WAF fingerprint detection from returned HTML.
2. Failure HTML snapshots under diagnostics/snapshots/.
3. Prometheus-compatible metrics export.
4. JSON report and SLO-oriented latency / success-rate summary.

Run on the user's Mac with SearXNG running:
python3 scripts/diagnostics/test_engine_risk_control.py --base-url http://127.0.0.1:8090 --export-prom
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("engine_risk_test")

SNAPSHOT_DIR = Path("diagnostics/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

CAPTCHA_FINGERPRINTS = {
    "cloudflare_turnstile": ["challenges.cloudflare.com/turnstile", "cf-turnstile", "__cf_chl_"],
    "cloudflare_managed": ["cf-mitigated", "cf-ray", "checking your browser", "ddos protection by cloudflare"],
    "google_recaptcha_v2": ["g-recaptcha", "recaptcha/api.js"],
    "google_recaptcha_v3": ["grecaptcha.execute", "recaptcha/enterprise.js"],
    "hcaptcha": ["hcaptcha.com", "h-captcha"],
    "google_sorry": ["/sorry/index", "unusual traffic from your computer"],
    "ddos_guard": ["ddos-guard.net", "ddg_"],
    "akamai_bot_manager": ["_abck", "ak_bmsc", "akam"],
    "perimeterx": ["_pxhd", "px-captcha", "perimeterx.net"],
    "datadome": ["datadome", "dd-captcha"],
    "imperva_incapsula": ["incap_ses", "incapsula"],
}

ENGINES_TO_TEST = [
    "bing",
    "duckduckgo",
    "google",
    "brave",
    "startpage",
    "qwant",
    "mojeek",
    "yahoo",
    "wikipedia",
    "github",
    "arxiv",
    "stackoverflow",
    "hackernews",
    "lobste.rs",
    "reddit",
]

TEST_QUERIES = ["python langgraph", "rust async programming", "openai benchmark arxiv"]


def fingerprint_html(html: str) -> List[str]:
    lower = html.lower()
    matches: List[str] = []
    for fp_name, keywords in CAPTCHA_FINGERPRINTS.items():
        if any(kw.lower() in lower for kw in keywords):
            matches.append(fp_name)
    return matches


def save_snapshot(engine: str, query: str, content: str, suffix: str = "html") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_q = "".join(c if c.isalnum() else "_" for c in query)[:30]
    h = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()[:8]
    fp = SNAPSHOT_DIR / f"{engine}_{safe_q}_{ts}_{h}.{suffix}"
    fp.write_text(content[:200000], encoding="utf-8", errors="ignore")
    return str(fp)


class EngineMetric:
    def __init__(self, engine: str):
        self.engine = engine
        self.attempts = 0
        self.successes = 0
        self.captchas = 0
        self.rate_limited = 0
        self.timeouts = 0
        self.errors = 0
        self.empty = 0
        self.latencies: List[float] = []
        self.detected_protections: Dict[str, int] = {}
        self.snapshots: List[str] = []
        self.errors_raw: List[str] = []

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts else 0.0

    @property
    def p50_ms(self) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        return s[len(s) // 2]

    @property
    def p95_ms(self) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        idx = min(len(s) - 1, int(len(s) * 0.95))
        return s[idx]

    def verdict(self) -> str:
        if self.captchas >= self.attempts and self.attempts:
            return "BLOCKED_ALWAYS_CAPTCHA"
        if self.captchas > 0:
            return f"PARTIAL_CAPTCHA_{self.captchas}_OF_{self.attempts}"
        if self.rate_limited > 0:
            return f"RATE_LIMITED_{self.rate_limited}"
        if self.timeouts > 0:
            return f"TIMEOUT_PRONE_{self.timeouts}"
        if self.success_rate >= 0.8:
            return "HEALTHY"
        if self.success_rate >= 0.3:
            return "UNSTABLE"
        return "BROKEN"


async def probe_engine(client: httpx.AsyncClient, engine: str, queries: List[str]) -> EngineMetric:
    m = EngineMetric(engine)
    for query in queries:
        m.attempts += 1
        t0 = time.perf_counter()
        try:
            resp = await client.get(
                "/search",
                params={"q": query, "format": "json", "engines": engine, "limit": 5},
                timeout=15.0,
            )
            m.latencies.append((time.perf_counter() - t0) * 1000)

            if resp.status_code >= 400:
                body = resp.text
                fps = fingerprint_html(body)
                if fps:
                    m.captchas += 1
                    for fp in fps:
                        m.detected_protections[fp] = m.detected_protections.get(fp, 0) + 1
                    m.snapshots.append(save_snapshot(engine, query, body))
                elif resp.status_code == 429:
                    m.rate_limited += 1
                else:
                    m.errors += 1
                m.errors_raw.append(f"HTTP {resp.status_code}")
                await asyncio.sleep(1.0)
                continue

            data = resp.json()
            unresponsive = data.get("unresponsive_engines", [])
            engine_err = None
            for item in unresponsive:
                if isinstance(item, list) and len(item) >= 2 and str(item[0]).lower() == engine.lower():
                    engine_err = str(item[1])
                    break

            if engine_err:
                err_l = engine_err.lower()
                m.errors_raw.append(engine_err)
                if any(k in err_l for k in ("captcha", "challenge", "bot", "turnstile")):
                    m.captchas += 1
                    try:
                        html_resp = await client.get("/search", params={"q": query, "engines": engine}, timeout=15.0)
                        fps = fingerprint_html(html_resp.text)
                        for fp in fps:
                            m.detected_protections[fp] = m.detected_protections.get(fp, 0) + 1
                        m.snapshots.append(save_snapshot(engine, query, html_resp.text))
                    except Exception:
                        pass
                elif any(k in err_l for k in ("too many", "limit", "suspended", "429", "rate")):
                    m.rate_limited += 1
                elif "timeout" in err_l:
                    m.timeouts += 1
                else:
                    m.errors += 1
            elif data.get("results"):
                m.successes += 1
            else:
                m.empty += 1
        except httpx.TimeoutException:
            m.timeouts += 1
            m.errors_raw.append("client timeout")
        except Exception as exc:
            m.errors += 1
            m.errors_raw.append(f"{type(exc).__name__}: {exc}")
        await asyncio.sleep(1.0)
    return m


def render_prometheus(metrics: List[EngineMetric]) -> str:
    lines = [
        "# HELP searxng_engine_success_rate Success rate per engine",
        "# TYPE searxng_engine_success_rate gauge",
    ]
    for m in metrics:
        lines.append(f'searxng_engine_success_rate{{engine="{m.engine}"}} {m.success_rate:.3f}')
    lines += [
        "# HELP searxng_engine_latency_p95_ms Engine P95 latency",
        "# TYPE searxng_engine_latency_p95_ms gauge",
    ]
    for m in metrics:
        lines.append(f'searxng_engine_latency_p95_ms{{engine="{m.engine}"}} {m.p95_ms:.1f}')
    lines += [
        "# HELP searxng_engine_captcha_count Captcha hits",
        "# TYPE searxng_engine_captcha_count counter",
    ]
    for m in metrics:
        lines.append(f'searxng_engine_captcha_count{{engine="{m.engine}"}} {m.captchas}')
    return "\n".join(lines)


async def main(base_url: str, export_prom: bool) -> None:
    logger.info("Risk-Control Diagnostic Suite v2 -> %s", base_url)
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"User-Agent": "Mozilla/5.0 (FORGE-Diag)"},
        trust_env=False,
    ) as client:
        try:
            ping = await client.get("/search", params={"q": "ping", "format": "json", "limit": 1}, timeout=8.0)
            if ping.status_code != 200:
                logger.error("SearXNG ping returned HTTP %s", ping.status_code)
                return
        except Exception as exc:
            logger.error("Cannot connect to SearXNG at %s: %s", base_url, exc)
            return
        metrics = await asyncio.gather(*[probe_engine(client, engine, TEST_QUERIES) for engine in ENGINES_TO_TEST])

    print("\n" + "=" * 110)
    print(f"{'Engine':<18}{'Verdict':<28}{'SR':<8}{'P50':<10}{'P95':<10}{'Protection':<30}")
    print("=" * 110)
    healthy, broken = [], []
    for m in metrics:
        protection = ",".join(m.detected_protections.keys()) or "-"
        print(
            f"{m.engine:<18}{m.verdict():<28}"
            f"{m.success_rate * 100:5.1f}%  {m.p50_ms:8.0f}ms{m.p95_ms:8.0f}ms  {protection[:28]:<30}"
        )
        if m.snapshots:
            print(f"   snapshots: {m.snapshots[0]}")
        if m.success_rate >= 0.5:
            healthy.append(m.engine)
        else:
            broken.append(m.engine)

    print("\n" + "=" * 110)
    print(f"Recommended healthy pool ({len(healthy)}): {healthy}")
    print(f"Avoid / circuit-break ({len(broken)}): {broken}")
    print("\nSuggested settings.yml engine config:")
    print("engines:")
    for m in metrics:
        disabled = "false" if m.success_rate >= 0.5 else "true"
        print(f"  - name: {m.engine}\n    disabled: {disabled}")

    Path("diagnostics").mkdir(exist_ok=True)
    if export_prom:
        Path("diagnostics/metrics.prom").write_text(render_prometheus(metrics), encoding="utf-8")
        print("\nPrometheus metrics -> diagnostics/metrics.prom")

    report = {
        "ts": datetime.now().isoformat(),
        "base_url": base_url,
        "engines": [
            {
                "name": m.engine,
                "verdict": m.verdict(),
                "success_rate": m.success_rate,
                "p50_ms": m.p50_ms,
                "p95_ms": m.p95_ms,
                "captchas": m.captchas,
                "rate_limited": m.rate_limited,
                "timeouts": m.timeouts,
                "errors": m.errors,
                "protections": m.detected_protections,
                "snapshots": m.snapshots,
                "errors_raw": m.errors_raw[:3],
            }
            for m in metrics
        ],
    }
    Path("diagnostics/report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("JSON report -> diagnostics/report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SearXNG engine risk-control diagnostic suite v2")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--export-prom", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.base_url, args.export_prom))
