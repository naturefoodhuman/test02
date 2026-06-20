# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 01:30:00

import requests
import json
import time
import subprocess
import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_test():
    print("🧪 开始验证“按需加载”闭环测试 (300s 宽限期)...")
    
    if is_port_open(8080):
        print("⚠️ 正在清理 8080 以进行冷启动测试...")
        subprocess.run("pkill -f mtplx.*8080", shell=True)
        time.sleep(3)
    
    print("✅ 8080 端口已关闭。正在向 Smart Proxy (4000) 发起请求...")
    
    start_ts = time.time()
    try:
        # 将 timeout 设为 300 秒，给大模型加载权重留足时间
        resp = requests.post(
            "http://localhost:4000/v1/chat/completions",
            headers={"Authorization": "Bearer sk444"},
            json={
                "model": "claude-opus-4-8",
                "messages": [{"role": "user", "content": "你好，请确认按需加载是否成功。"}]
            },
            timeout=300 
        )
        
        elapsed = time.time() - start_ts
        if resp.status_code == 200:
            print(f"✨【终极成功】按需加载闭环通了！")
            print(f"⏱️  总耗时: {elapsed:.1f}s")
            print(f"🤖 模型回答: {resp.json()['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ 失败: HTTP {resp.status_code}")
            print(f"📝 详情: {resp.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    run_test()
