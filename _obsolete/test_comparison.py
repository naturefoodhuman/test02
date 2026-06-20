# test_comparison.py
"""🔥 任务 C: 本地 vs 云端 模型评审质量对比测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "_factory/patterns/peer-review/src"))

from peer_review.orchestrator import build_review_team, PeerReviewOrchestrator

# 测试用例
TEST_CASE = """
张三欠我 5 万，只有微信转账记录，没有借条。对方现在失联了，但我听说他最近买了一辆新车挂在朋友名下。请评估风险并给出具体执行方案。
"""

MODELS_TO_TEST = [
    ("local/primary", "本地模型 (Qwen 3.6 35B)"),
    # ("cloud/glm-primary", "云端模型 (GLM-5)"), # 如果你想测云端，取消注释并填入 Key
]

def run_comparison():
    print("🔍 开始加载专家团队...")
    try:
        primary, reviewers = build_review_team(Path("_factory/experts"))
    except Exception as e:
        print(f"❌ 团队加载失败: {e}")
        return

    for model_id, model_desc in MODELS_TO_TEST:
        print(f"\n{'='*60}")
        print(f"🚀 正在使用 {model_desc} [{model_id}] 进行评审...")
        print(f"{'='*60}")
        
        try:
            orch = PeerReviewOrchestrator(primary, reviewers, model_override=model_id)
            result = orch.run_review(TEST_CASE)
            print(f"\n📄 评审报告 ({model_desc}):")
            print(result[:1000] + "..." if len(result) > 1000 else result)
        except Exception as e:
            print(f"❌ {model_desc} 评审失败: {e}")

if __name__ == "__main__":
    run_comparison()