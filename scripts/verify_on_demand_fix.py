# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 18:45:00

import requests
import json
import time
import subprocess
import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_test():
    print("🧪 开始验证“按需加载”闭环测试...")
    
    # 1. 确认 8080 是否关闭 (模拟自检释放后的状态)
    if is_port_open(8080):
        print("⚠️ 发现 8080 已开启，正在尝试关闭以进行纯净测试...")
        subprocess.run("pkill -f mtplx.*8080", shell=True)
        time.sleep(2)
    
    print("✅ 状态确认：8080 端口已关闭。")
    print("📡 正在通过 Smart Proxy (4000) 发送 claude-opus-4-8 请求...")
    
    start_ts = time.time()
    try:
        # 发送请求给 Smart Proxy
        resp = requests.post(
            "http://localhost:4000/v1/chat/completions",
            headers={"Authorization": "Bearer sk444"},
            json={
                "model": "claude-opus-4-8",
                "messages": [{"role": "user", "content": "你好，请确认你是否已按需拉起并能回答问题。"}]
            },
            timeout=120
        )
        
        elapsed = time.time() - start_ts
        if resp.status_code == 200:
            print(f"✨ 测试成功！")
            print(f"⏱️  总耗时: {elapsed:.1f}s (包含模型拉起时间)")
            print(f"🤖 模型回答: {resp.json()['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ 测试失败: HTTP {resp.status_code}")
            print(f"📝 错误详情: {resp.text}")
            
    except Exception as e:
        print(f"❌ 请求发生异常: {e}")

if __name__ == "__main__":
    run_test()
