# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""Forge Model Evaluator: 针对不同路由方案的 A/B 测试框架

职责：
- 加载 Gold Dataset
- 驱动多个 RoutingPlans 执行评审
- 采集 TPS, Latency, 质量分数
- 生成模型适合度报告
"""

from __future__ import annotations

import json
import time
import statistics
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any

# 动态加载 peer-review 模块
import sys
import os

# 确保能够导入 peer_review
# 假设运行路径在项目根目录，我们需要把 _factory/patterns/peer-review/src 加入 path
sys.path.append(os.path.abspath("_factory/patterns/peer-review/src"))

try:
    from peer_review.graph.execution import run_langgraph_review
    from peer_review.platform.routing_plan_engine import RoutingPlanEngine
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ 导入评审模块失败: {e}")
    print("👉 请运行 'uv pip install -e _factory/patterns/peer-review' 安装依赖。")
    IMPORT_SUCCESS = False

@dataclass
class EvalResult:
    plan_id: str
    case_id: str
    tft: float  # Time to First Token (simulated if not available)
    total_time: float
    tps: float
    quality_score: float
    divergence: float

class ModelEvaluator:
    def __init__(self, root: Path):
        self.root = root
        self.dataset_path = root / "_factory" / "evals" / "gold_dataset.json"
        # RoutingPlanEngine now takes project_root as a single argument
        self.routing_engine = RoutingPlanEngine(project_root=root)

    def load_dataset(self) -> list[dict]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_ab_test(self, plans: list[str]):
        dataset = self.load_dataset()
        all_results: list[EvalResult] = []

        for plan_id in plans:
            print(f"🚀 Testing Plan: {plan_id}")
            for case in dataset:
                print(f"  - Case {case['id']}...", end=" ", flush=True)
                
                start_time = time.perf_counter()
                
                # 模拟运行评审 (这里直接调用 run_langgraph_review)
                # 为了测试，我们构造一个简单的 case_context
                case_context = {
                    "case_id": case["id"],
                    "content": case["input"],
                    "metadata": {"category": case["category"]}
                }
                
                try:
                    # 真实 LangGraph + 真实 LLM 调用（MTPLX / Ollama 等）
                    # use_live=False 避免 Rich Live 干扰 eval 输出
                    result = run_langgraph_review(
                        case_context=case_context,
                        plan_id=plan_id,
                        use_live=False,
                        root=self.root
                    )
                    
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    
                    # 真实输出长度用于 TPS 估算
                    final_text = result.get("final_decision", "") or result.get("consensus", "")
                    output_len = len(final_text)
                    tps = output_len / duration if duration > 0 else 0
                    
                    # 质量评分：基于 gold_dataset expected_logic 的简单关键词启发式（真实场景下可替换为人工打分或 RAGAS）
                    score = 0.0
                    final_lower = final_text.lower()
                    for logic in case["expected_logic"]:
                        keywords = [w for w in logic.split() if len(w) > 1]
                        if any(k.lower() in final_lower for k in keywords):
                            score += 1.0
                    
                    quality_score = min(1.0, score / max(1, len(case["expected_logic"])))
                    divergence = result.get("divergence_score", 0.0)
                    models_used = result.get("models_used", {})

                    all_results.append(EvalResult(
                        plan_id=plan_id,
                        case_id=case["id"],
                        tft=duration * 0.1,
                        total_time=duration,
                        tps=tps,
                        quality_score=quality_score,
                        divergence=divergence
                    ))
                    model_summary = ", ".join(f"{k}:{v.split(':')[0] if ':' in v else v}" for k,v in models_used.items()) if models_used else "N/A"
                    print(f"✅ Score: {quality_score:.2f} | {duration:.1f}s | models: {model_summary}")
                except Exception as e:
                    print(f"❌ Error: {e}")

        return all_results

    def generate_report(self, results: list[EvalResult]):
        # 按方案分组计算平均值
        plans = set(r.plan_id for r in results)
        report = {}
        
        for pid in plans:
            p_res = [r for r in results if r.plan_id == pid]
            report[pid] = {
                "avg_time": statistics.mean([r.total_time for r in p_res]),
                "avg_tps": statistics.mean([r.tps for r in p_res]),
                "avg_quality": statistics.mean([r.quality_score for r in p_res]),
                "avg_divergence": statistics.mean([r.divergence for r in p_res]),
                "sample_count": len(p_res)
            }
        
        return report

def cmd_eval(args, root: Path):
    if not IMPORT_SUCCESS:
        print("⛔ 无法执行 eval：评审模块依赖缺失。")
        return 1
    evaluator = ModelEvaluator(root)
    # 获取所有可用的 plan_id
    plans = evaluator.routing_engine.get_available_plans()
    
    # 如果用户指定了 plans，则使用指定的
    test_plans = args.plans if args.plans else plans
    
    print(f"🧪 Starting A/B Test for plans: {test_plans}")
    results = evaluator.run_ab_test(test_plans)
    report = evaluator.generate_report(results)
    
    # 打印报告
    print("\n" + "="*50)
    print(f"{'Plan ID':<20} | {'Time':<8} | {'TPS':<8} | {'Qual':<8} | {'Div':<8}")
    print("-" * 50)
    for pid, metrics in report.items():
        print(f"{pid:<20} | {metrics['avg_time']:<8.2f} | {metrics['avg_tps']:<8.1f} | {metrics['avg_quality']:<8.2f} | {metrics['avg_divergence']:<8.2f}")
    print("="*50)
    
    # 保存到文件
    report_path = root / "runtime" / "model_eval_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"💾 Report saved to {report_path}")
    return 0
