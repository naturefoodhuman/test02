# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 00:15:00

import requests
import time
import sys
import os

# 确保能加载 llm_client 里的拉起逻辑
FORGE_ROOT = "/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
sys.path.append(os.path.join(FORGE_ROOT, "_factory/patterns/peer-review/src"))
from peer_review.llm_client import _ensure_server_running

def test_direct():
    print("🎯 开始执行【模型直连】压力测试 (绕过所有网关)...")
    target_url = "http://localhost:8080/v1/chat/completions"
    
    # 1. 触发拉起
    _ensure_server_running("http://localhost:8080/v1")
    
    # 2. 发送原始请求
    print(f"📡 正在向 {target_url} 发送原生请求...")
    payload = {
        "model": "Qwen3.6-27B-MTPLX-Optimized-Quality",
        "messages": [{"role": "user", "content": "你好，请做个自我介绍。"}],
        "temperature": 0.7
    }
    
    try:
        start_ts = time.time()
        # 使用原生 requests，不带 stream
        resp = requests.post(target_url, json=payload, timeout=180)
        elapsed = time.time() - start_ts
        
        if resp.status_code == 200:
            print(f"✅ 直连测试成功！耗时: {elapsed:.1f}s")
            print(f"🤖 模型响应: {resp.json()['choices'][0]['message']['content'][:200]}...")
        else:
            print(f"❌ 直连测试失败: HTTP {resp.status_code}")
            print(f"📝 响应正文: {resp.text}")
    except Exception as e:
        print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    test_direct()
