#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 03:40:00 CST
"""端到端评审验证脚本

用法：
  # 真实 LLM 环境（需先启动 Ollama + LiteLLM 网关）
  python3 scripts/e2e_review_test.py --project-root /home/user/project

  # 沙箱/CI 模拟模式（不依赖外部模型）
  python3 scripts/e2e_review_test.py --mock

输出：
  - 终端打印节点进度与最终结果
  - 结果写入 runtime/e2e_review_<timestamp>.md
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _mock_chat(model_cfg, messages, *, privacy_context=None):
    from peer_review.llm_client import LLMResponse

    return LLMResponse(
        content=f"[模拟 {model_cfg.display_name} 回复，模型 ID: {model_cfg.model_id}]",
        model=model_cfg.model_id,
    )


def run_test(project_root: Path, use_mock: bool, plan_id: str) -> dict:
    from peer_review.llm_client import LLMResponse
    from peer_review.orchestrator import run_langgraph_review

    if use_mock:
        #  monkeypatch 底层调用，模拟 LLM 响应
        import peer_review.llm_client as llm_client

        def mock_gateway(model_name, messages, timeout=120):
            return LLMResponse(
                content=f"[模拟 API {model_name} 回复]",
                model=model_name,
            )

        def mock_ollama(model_cfg, messages):
            return LLMResponse(
                content=f"[模拟本地 {model_cfg.display_name} 回复]",
                model=model_cfg.model_id,
            )

        llm_client._call_litellm_gateway = mock_gateway
        llm_client._call_ollama_direct = mock_ollama

    case = "张三欠李四50000元，有借条，约定2024年7月1日还款，至今未还。"
    start = time.time()
    result = run_langgraph_review(
        case,
        project_root=project_root,
        plan_id=plan_id,
        data_fields={"debtor_name": "张三", "amount": 50000},
        privacy_endpoint="chinese_api",
        privacy_approved=True,
    )
    elapsed = time.time() - start
    result["elapsed_seconds"] = elapsed
    return result


def save_report(result: dict, plan_id: str, project_root: Path, use_mock: bool) -> Path:
    out_dir = project_root / "runtime"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"e2e_review_{plan_id}_{ts}.md"

    lines = [
        f"# E2E 评审验证报告 — {plan_id}",
        "",
        f"- **时间**：{datetime.now().isoformat()}",
        f"- **模式**：{'模拟' if use_mock else '真实 LLM'}",
        f"- **方案**：{plan_id}",
        f"- **总耗时**：{result['elapsed_seconds']:.2f}s",
        f"- **线程 ID**：{result.get('thread_id', 'N/A')}",
        f"- **分歧度**：{result.get('divergence_score', 0)}",
        f"- **是否触发人工审核**：{result.get('requires_human', False)}",
        "",
        "## 主专家分析",
        "",
        result.get("primary_analysis", "（无）"),
        "",
        "## 最终汇总结论",
        "",
        result.get("consensus", "（无）"),
        "",
        "## 各评审独立意见",
        "",
    ]
    for i, (role, opinion) in enumerate(zip(result.get("reviewer_roles", []), result.get("reviewer_opinions", [])), 1):
        lines.extend([f"### 评审{i} [{role}]", "", opinion, ""])

    lines.extend([
        "## 模型使用记录",
        "",
        "| 节点 | 模型 |",
        "|------|------|",
    ])
    for node, model in (result.get("models_used") or {}).items():
        lines.append(f"| {node} | {model} |")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="端到端评审验证")
    parser.add_argument("--project-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--plan", default="default")
    parser.add_argument("--mock", action="store_true", help="使用模拟 LLM 响应")
    args = parser.parse_args()

    print(f"🔍 启动 E2E 评审验证（方案：{args.plan}，模拟：{args.mock}）")
    result = run_test(args.project_root, args.mock, args.plan)
    out_path = save_report(result, args.plan, args.project_root, args.mock)

    print("\n" + "=" * 60)
    print("【主专家分析】")
    print(result.get("primary_analysis", "（无）")[:300])
    print("\n【最终汇总结论】")
    print(result.get("consensus", "（无）")[:300])
    print(f"\n✅ 报告已保存：{out_path}")
    print(f"⏱ 总耗时：{result['elapsed_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
