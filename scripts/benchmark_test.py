# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-19 19:30:00

import time
import argparse
from pathlib import Path
from peer_review.graph.execution import run_langgraph_review
from peer_review.platform.memory_store import MemoryStore

def run_benchmark(plans: list[str], case_query: str):
    root = Path(__file__).resolve().parents[1]
    memory = MemoryStore(root / "runtime" / "memory.db")
    
    results = []
    print(f"开始接近真实难度的完整测试...")
    print(f"测试案例: {case_query[:50]}...")
    
    for plan in plans:
        print(f"\n[测试方案: {plan}]")
        start_ts = time.time()
        try:
            state = run_langgraph_review(
                case_query,
                project_root=root,
                plan_id=plan,
                privacy_approved=True
            )
            elapsed = time.time() - start_ts
            divergence = state.get("divergence_score", 0.0)
            
            results.append({
                "plan": plan,
                "elapsed": elapsed,
                "divergence": divergence,
                "status": "SUCCESS"
            })
            print(f"✅ 完成: 耗时 {elapsed:.1f}s, 分歧度 {divergence}")
        except Exception as e:
            print(f"❌ 失败: {e}")
            results.append({"plan": plan, "status": "FAILED", "error": str(e)})
            
    # 输出简报
    print("\n" + "="*40)
    print("测试简报 (接近真实难度)")
    print("-" * 40)
    for res in results:
        if res["status"] == "SUCCESS":
            print(f"方案 {res['plan']:<15} | 耗时: {res['elapsed']:>5.1f}s | 分歧度: {res['divergence']}")
        else:
            print(f"方案 {res['plan']:<15} | 状态: 失败 ({res.get('error')})")
    print("="*40)

if __name__ == "__main__":
    plans_to_test = ["default", "high-quality", "all-local", "mtplx-hybrid"]
    # 模拟一个复杂债务案件
    complex_case = """
    【案件事实】债务人：王五，欠款：2,500,000元。
    【债务性质】民间借贷，涉及高利贷嫌疑。
    【当前阶段】已起诉但被告失联，法院公告送达中。
    【证据】借条（仅复印件）、银行流水（不全）、微信记录（对方未实名）。
    【情报】债务人在东南亚某地有疑似房产，但在国内无登记财产。
    请给出完整的追讨策略建议。
    """
    run_benchmark(plans_to_test, complex_case)
