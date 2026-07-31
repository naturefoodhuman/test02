"""
scripts/diagnostics/verify_ssd_session_cache.py

对应交接文档 §20.13：SSD Session Cache 重启恢复验收。
本脚本会重启 8080 端口的 MTPLX 进程，属于破坏性操作，不会被
verify_smart_proxy.py 或常规 CI 流程自动调用。

直接访问 8080（bypass smart_proxy），因为 MTPLX 原生的
cached_tokens/cache_source 字段目前不经过 smart_proxy 转发进
Anthropic 响应体（参见交接文档 §4.3 的原始实验方式）。

运行方式（必须显式加 --destructive 才会真正执行）：
    python3 scripts/diagnostics/verify_ssd_session_cache.py --destructive
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _infra.model_runtime import build_command, get_kill_pattern, get_server_config  # noqa: E402

PORT = 8080


def _is_listening(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _ssd_cache_dir() -> Path:
    cfg = get_server_config(PORT)
    args = cfg.get("extra_args", [])
    for i, a in enumerate(args):
        if a == "--ssd-session-cache-dir" and i + 1 < len(args):
            return Path(args[i + 1])
    raise RuntimeError("未在 config/model_runtime.yaml 中找到 8080 的 ssd-session-cache-dir")


def _build_stable_payload():
    filler = "这是用于验证 SSD Session Cache 的稳定前缀内容。" * 60
    return {
        "model": "mtplx-qwen36-27b-optimized-quality",
        "messages": [{"role": "user", "content": filler + " 请回复 OK。"}],
        "max_tokens": 8,
        "stream": False,
    }


def _send_direct(payload):
    t0 = time.time()
    r = httpx.post(f"http://127.0.0.1:{PORT}/v1/chat/completions", json=payload, timeout=300.0)
    elapsed = time.time() - t0
    r.raise_for_status()
    body = r.json()
    stats = body.get("usage", {}) or body.get("stats", {}) or {}
    return elapsed, body, stats


def _start_8080():
    subprocess.Popen(build_command(PORT), shell=True)
    for _ in range(60):
        if _is_listening(PORT):
            time.sleep(3)
            return True
        time.sleep(2)
    return False


def _restart_8080():
    pattern = get_kill_pattern(PORT)
    print(f"🔻 停止 8080 (pattern={pattern}) ...")
    subprocess.run(["pkill", "-9", "-f", pattern])
    for _ in range(20):
        if not _is_listening(PORT):
            break
        time.sleep(0.5)
    print(f"🚀 重新拉起 8080: {build_command(PORT)}")
    return _start_8080()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destructive", action="store_true",
                         help="必须显式指定才会真正重启 8080 端口的模型")
    args = parser.parse_args()

    if not args.destructive:
        print("⚠️ 这是破坏性测试（会重启 8080 模型）。请加 --destructive 参数确认执行。")
        sys.exit(1)

    if not _is_listening(PORT):
        print("⚠️ 8080 当前未运行，正在启动...")
        if not _start_8080():
            print("❌ 8080 启动失败")
            sys.exit(1)

    cache_dir = _ssd_cache_dir()
    print(f"📁 SSD 缓存目录: {cache_dir}")

    payload = _build_stable_payload()

    print("① 发送首次稳定 payload（预期冷 prefill，较慢）...")
    elapsed1, _, stats1 = _send_direct(payload)
    print(f"   耗时 {elapsed1:.2f}s, stats={stats1}")

    print("② 等待异步 snapshot 落盘 (10s)...")
    time.sleep(10)

    if not cache_dir.exists() or not any(cache_dir.iterdir()):
        print(f"❌ 未在 {cache_dir} 发现任何缓存文件，SSD Session Cache 可能未生效")
        sys.exit(2)
    print(f"✅ SSD 缓存目录中发现 {len(list(cache_dir.iterdir()))} 个文件/条目")

    print("③ 重启 8080 ...")
    if not _restart_8080():
        print("❌ 8080 重启失败")
        sys.exit(3)

    print("④ 重启后原样重复相同 payload...")
    elapsed2, _, stats2 = _send_direct(payload)
    print(f"   耗时 {elapsed2:.2f}s, stats={stats2}")

    cached_tokens = stats2.get("cached_tokens", stats2.get("prompt_cache_hit_tokens", 0))
    cache_source = stats2.get("cache_source", stats2.get("cache_type", ""))
    print(f"cached_tokens={cached_tokens} cache_source={cache_source}")

    if cached_tokens and cached_tokens > 0:
        print("✅ SSD Session Cache 重启恢复验证通过")
    else:
        print(
            "⚠️ 未在标准 usage/stats 字段中直接观测到 cached_tokens。\n"
            "   请对照 MTPLX 自身日志（/tmp/mtplx_8080.log）人工确认是否出现\n"
            "   ssd_cache_hit / cache_source=ssd 等字样——不同 MTPLX 版本暴露这些\n"
            "   统计字段的名称和位置可能不同（文档 §14.3 也说明部分参数格式未从\n"
            "   help 输出中确认，不能凭空假设）。"
        )
        print(f"   耗时对比：cold(重启前)={elapsed1:.2f}s, warm-after-restart={elapsed2:.2f}s")
        if elapsed2 < elapsed1 * 0.5:
            print("   ⏱️ 至少从耗时上看，重启后仍显著快于首次冷启动，间接支持 SSD 缓存生效。")


if __name__ == "__main__":
    main()