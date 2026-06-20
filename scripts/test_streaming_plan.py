#!/usr/bin/env python3
"""
流式压测脚本 v2.0（使用 Smart Proxy 流式版）
"""
import sys
import os
from pathlib import Path
import time

# 强制使用流式 Smart Proxy
os.environ["FORGE_SMART_PROXY"] = "streaming"

sys.path.insert(0, str(Path(__file__).parent.parent / "_factory/patterns/peer-review/src"))

from peer_review.graph.execution import run_langgraph_review

def main():
    case = """【案件事实】债务人：王五，欠款：2,500,000元。【债务性质】民间借贷，涉及高利贷嫌疑。"""

    print("开始流式单方案测试 (default) ...")
    start = time.time()

    result = run_langgraph_review(
        case,
        project_root=Path.cwd(),
        plan_id="default",
        privacy_approved=True,
    )

    elapsed = time.time() - start
    print(f"\n=== 测试完成 (耗时 {elapsed:.1f}s) ===")
    print(f"最终共识: {result.get('consensus', '无')[:300]}...")
    print(f"分歧度: {result.get('divergence_score')}")
    print(f"模型使用: {result.get('models_used')}")
    print(f"错误: {result.get('error', '无')}")

if __name__ == "__main__":
    main()