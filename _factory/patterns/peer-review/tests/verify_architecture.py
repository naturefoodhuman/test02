# verify_architecture.py
# 用于验证 Peer-Review 重构环境是否就绪（v1.1.0 LangGraph + 平台层）
import sys
import importlib

REQUIRED_PACKAGES = [
    "agno",                       # 旧 Agno 实现仍保留兼容
    "llama_index.core",
    "chromadb",
    "rich",
    "pydantic",
    "yaml",
    "ollama",
    "langgraph",                  # LangGraph 1.0+
    "langgraph.checkpoint.sqlite",  # SqliteSaver
    "litellm",                    # LiteLLM 网关客户端
]

def check_dependencies():
    print("🔍 开始检查重构所需的依赖库...")
    all_ok = True
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg} 已安装")
        except ImportError:
            print(f"❌ 缺少依赖：{pkg}")
            print(f"   请运行: pip install {pkg}")
            all_ok = False
    return all_ok

def check_orchestrator_imports():
    print("\n🔍 检查 orchestrator.py 能否正常导入...")
    try:
        from peer_review.orchestrator import run_langgraph_review, build_review_team
        print("✅ orchestrator 模块加载成功，LangGraph 与 Agno 兼容入口均可用。")
        return True
    except SyntaxError as e:
        print(f"❌ orchestrator.py 存在语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入 orchestrator 失败: {e}")
        return False

def check_graph_imports():
    print("\n🔍 检查 LangGraph 图模块能否正常导入...")
    try:
        from peer_review.graph.review_graph import build_review_graph
        from peer_review.graph.state import ReviewState
        from peer_review.platform.routing_plan_engine import RoutingPlanEngine
        from peer_review.platform.data_privacy_gate import DataPrivacyGate
        from peer_review.platform.memory_store import MemoryStore
        from peer_review.platform.decision_engine import DecisionEngine
        from peer_review.platform.knowledge_hub import KnowledgeHub
        print("✅ LangGraph 图模块与平台层全部加载成功。")
        return True
    except Exception as e:
        print(f"❌ 导入图模块失败: {e}")
        return False

if __name__ == "__main__":
    # 确保当前路径在 sys.path 中
    sys.path.insert(0, "./src")
    
    if check_dependencies() and check_orchestrator_imports() and check_graph_imports():
        print("\n🎉 **环境验证通过！** 可以开始运行 Peer-Review 流程。")
        sys.exit(0)
    else:
        print("\n💥 **环境验证失败**，请修复上述报错后再试。")
        sys.exit(1)
