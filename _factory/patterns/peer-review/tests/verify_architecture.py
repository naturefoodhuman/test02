# verify_architecture.py
# 用于验证 Agno + LlamaIndex + ChromaDB 重构环境是否就绪
import sys
import importlib

REQUIRED_PACKAGES = [
    "agno",
    "llama_index.core",
    "chromadb",
    "rich",
    "pydantic",
    "yaml",
    "ollama",
]

def check_dependencies():
    print("🔍 开始检查重构所需的依赖库...")
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg} 已安装")
        except ImportError:
            print(f"❌ 缺少依赖：{pkg}")
            print(f"   请运行: uv pip install {pkg}")
            return False
    return True

def check_orchestrator_imports():
    print("\n🔍 检查 orchestrator.py 能否正常导入...")
    try:
        # 这里的 import 会触发 orchestrator.py 内部的语法检查和模块导入
        from peer_review.orchestrator import ExpertConfig, load_expert_config
        print("✅ orchestrator 模块加载成功，Agno 语法检查通过。")
        return True
    except SyntaxError as e:
        print(f"❌ orchestrator.py 存在语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入 orchestrator 失败: {e}")
        return False

if __name__ == "__main__":
    # 确保当前路径在 sys.path 中
    sys.path.insert(0, "./src")
    
    if check_dependencies() and check_orchestrator_imports():
        print("\n🎉 **环境验证通过！** 可以开始运行 Peer-Review 流程。")
        sys.exit(0)
    else:
        print("\n💥 **环境验证失败**，请修复上述报错后再试。")
        sys.exit(1)
