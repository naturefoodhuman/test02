# test_smoke.py
import urllib.request
import sys

# 1. 检查 Ollama
print("🔍 1. 检查 Ollama 服务...")
try:
    urllib.request.urlopen('http://localhost:11434', timeout=3)
    print("   ✅ Ollama 服务在线")
except:
    print("   ❌ Ollama 服务未启动或无法连接。请先运行 'ollama serve'")
    sys.exit(1)

# 2. 测试 Agnt
print("\n🔍 2. 测试 Agno Agent 连接...")
try:
    from agno.agent import Agent
    from agno.models.ollama import Ollama
    
    # 创建一个临时测试 Agent
    agent = Agent(
        name="TestBot",
        model=Ollama(id="qwen3.6:35b-a3b-q8_0"),
        instructions=["请简短回答：测试成功。"]
    )
    
    print("   🚀 正在向模型发送请求 (这可能需要十几秒)...")
    resp = agent.run("你好")
    
    print(f"   🤖 Agent 回复: {resp.content}")
    print("\n🎉 **核心链路测试通过！Agno 与 Ollama 通信正常。**")
except Exception as e:
    print(f"   ❌ 失败: {e}")