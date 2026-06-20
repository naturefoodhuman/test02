# test_full.py
import sys
from pathlib import Path

# 确保能导入 peer_review 模块
sys.path.insert(0, str(Path.cwd() / "_factory/patterns/peer-review/src"))

from peer_review.orchestrator import build_review_team, PeerReviewOrchestrator

try:
    experts_dir = Path("_factory/experts")
    if not experts_dir.exists():
        print("❌ 找不到专家目录，请在项目根目录下运行此脚本")
        sys.exit(1)

    print("1. 加载专家团队 (这将自动构建 ChromaDB 索引)...")
    primary, reviewers = build_review_team(experts_dir)
    print(f"   ✅ 主专家: {primary.name}")
    print(f"   ✅ 评审专家: {[r.name for r in reviewers]}")

    orch = PeerReviewOrchestrator(primary, reviewers)
    
    query = "张三欠我 5 万，只有微信转账记录，没有借条，对方现在失联了，我该怎么办？"
    print(f"\n2. 开始评审案件: '{query[:20]}...'")
    
    # 运行 Peer-Review
    result = orch.run_review(query)
    
    print("\n" + "="*50)
    print("🏁 评审最终结果:")
    print(result)
    print("="*50)

except Exception as e:
    print(f"\n❌ 全流程测试失败: {e}")
    import traceback
    traceback.print_exc()
    
    if "未找到主专家" in str(e):
        print("\n💡 提示: 请检查 debt-lawyer.expert/expert.yaml，确保顶层包含 'role: primary'。")