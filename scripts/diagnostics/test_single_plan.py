#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 17:20:00
__test__ = False  # pytest: diagnostic script, not a test module
"""简化版单方案测试脚本（带超长超时）"""
import sys
import os
from pathlib import Path

# 设置更长的超时
os.environ["HTTPX_TIMEOUT"] = "600"

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_factory/patterns/peer-review/src"))

from peer_review.graph.execution import run_langgraph_review

def main():
    case = """【案件事实】债务人：王五，欠款：2,500,000元。【债务性质】民间借贷，涉及高利贷嫌疑。【当前阶段】已起诉但被告失联。"""
    
    print("开始单方案测试 (default)...")
    result = run_langgraph_review(
        case, 
        project_root=Path.cwd(), 
        plan_id="default", 
        privacy_approved=True
    )
    
    print("\n=== 测试结果 ===")
    print(f"最终共识: {result.get('consensus', '无')[:200]}...")
    print(f"分歧度: {result.get('divergence_score')}")
    print(f"模型使用: {result.get('models_used')}")
    print(f"耗时: {result.get('total_time')}s")
    print(f"错误: {result.get('error', '无')}")

if __name__ == "__main__":
    main()
