# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-15 12:00:00 CST
"""forge CLI：在项目目录内驱动五阶段流程的轻量命令行工具。

零第三方依赖（只用标准库 argparse），保证在任何 Python 3.11+ 环境可跑。

命令：
  forge status            查看所有项目当前阶段状态
  forge new <name>        创建新项目
  forge check             校验 TASK_GRAPH（status/依赖/循环）+ 当前阶段退出产物
  forge tasks             列出可执行任务（依赖已满足）
  forge advance           检查能否进入下一阶段（不自动改文件，只给结论）
  forge gate <id>         打印某个 HITL Gate 的说明与所需文档
  forge compare-plans     查看模型方案对比报告

约定：在项目根目录运行（含 docs/ 的目录）。用 --root 指定其它根。
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

from forge.phases import PHASE_DEFS, PHASES, can_advance, next_phase
from forge.task_graph import load_task_graph, validate_task_graph
from forge.evaluator import cmd_eval

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

GATE_DESC = {
    "GATE-1": "需求确认：需求边界由人定义，AI 只能辅助。",
    "GATE-2": "架构与技术选型确认：选型决策必须人工审批。",
    "GATE-3": "风险清单确认：对风险的接受度由人决定。",
    "GATE-4": "最终验收：交付质量的最终判断权在人。",
    "GATE-5": "知识库更新确认：写入 _factory/ 的内容必须人工审核。",
}


def _existing_files(root: Path) -> set[str]:
    """收集项目内相对路径集合（用于退出产物检查）。"""
    out: set[str] = set()
    for p in root.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(root)))
    return out


def _detect_phase(root: Path) -> str:
    """根据已存在产物粗略推断当前阶段（从后往前找最先满足进入条件的阶段）。"""
    files = _existing_files(root)
    # 从最后阶段倒推：哪个阶段的进入文档齐全且其退出产物尚不全，就认为在那个阶段
    for ph in reversed(PHASES):
        pdef = PHASE_DEFS[ph]
        entry_ok = all(d in files for d in pdef.entry_docs)
        ok_advance, _ = can_advance(ph, files)
        if entry_ok and not ok_advance:
            return ph
    return "DISCOVERY"


def cmd_new(args, root: Path) -> int:
    """创建新项目：从 _TEMPLATE 复制骨架并初始化配置"""
    project_name = args.name
    domain = args.domain
    dest = root / "projects" / project_name
    template = root / "projects" / "_TEMPLATE"

    if dest.exists():
        print(f"❌ 项目 {project_name} 已存在。")
        return 1

    try:
        import shutil
        # 1. 复制模板
        shutil.copytree(template, dest)
        
        # 2. 初始化项目特定结构
        src_dir = dest / "src" / project_name
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建简单的 cli.py 入口
        with open(src_dir / "cli.py", "w", encoding="utf-8") as f:
            f.write(f'print("Welcome to {project_name} CLI!")\n')

        # 3. 简单更新配置文件中的项目名
        policy_path = dest / "config" / "privacy_policy.yaml"
        if policy_path.exists():
            content = policy_path.read_text(encoding="utf-8").replace("project: \"template\"", f"project: \"{project_name}\"")
            policy_path.write_text(content, encoding="utf-8")

        # 4. Domain-based expert loading
        experts_src = root / "_factory" / "experts"
        experts_dest = dest / "experts"
        if experts_src.exists():
            # Remove template expert from dest if it was copied
            template_expert = experts_dest / "_TEMPLATE.expert"
            if template_expert.exists():
                template_expert.unlink()

            # Find experts matching domain (simple keyword match)
            matched_experts = [
                f for f in experts_src.glob("*.expert") 
                if domain.lower() in f.name.lower() or f.name.startswith("general")
            ]
            for exp in matched_experts:
                dest_exp_path = experts_dest / exp.name
                if dest_exp_path.exists():
                    import shutil
                    shutil.rmtree(dest_exp_path)
                shutil.copytree(exp, dest_exp_path)
            
            if matched_experts:
                print(f"🛠️  已加载 {len(matched_experts)} 个 {domain} 领域专家配置。")
            else:
                print(f"ℹ️  未找到匹配 {domain} 的专家配置，使用通用配置。")

        print(f"✅ 项目 {project_name} 已成功创建！")
        print(f"📂 路径: {dest}")
        print(f"👉 接下来请填写 {dest}/CHARTER.md 并执行 'forge stage {project_name} discovery'")
        return 0
    except Exception as e:
        print(f"❌ 创建项目失败: {e}")
        return 1


def cmd_status(root: Path) -> int:
    # 扫描所有 projects 文件夹
    projects_dir = root / "projects"
    if not projects_dir.exists():
        print("ℹ️  未找到 projects/ 目录。")
        return 0
    
    print(f"📂 正在扫描项目状态...")
    for p_dir in projects_dir.iterdir():
        if p_dir.is_dir() and p_dir.name != "_TEMPLATE":
            phase = _detect_phase(p_dir)
            print(f"  - {p_dir.name:<20} ➔ {phase}")
    return 0


def cmd_check(root: Path) -> int:
    rc = 0
    tg_path = root / "docs" / "TASK_GRAPH.md"
    if tg_path.exists():
        g = load_task_graph(tg_path)
        problems = validate_task_graph(g)
        ip = g.in_progress()
        if problems:
            rc = 1
            print("❌ TASK_GRAPH 校验失败：")
            for p in problems:
                print(f"   - {p}")
        else:
            print("✅ TASK_GRAPH 结构合法。")
        if ip:
            print(f"⚠️  存在 {len(ip)} 个 IN_PROGRESS 任务（提交前应改为 DONE）：")
            for t in ip:
                print(f"   - {t.name}")
    else:
        print("ℹ️  无 docs/TASK_GRAPH.md，跳过任务图校验。")

    phase = _detect_phase(root)
    ok, missing = can_advance(phase, _existing_files(root))
    if ok:
        print(f"✅ 阶段 {phase} 的退出产物齐全。")
    else:
        print(f"⚠️  阶段 {phase} 缺少退出产物：{missing}")
    return rc


def cmd_tasks(root: Path) -> int:
    tg_path = root / "docs" / "TASK_GRAPH.md"
    if not tg_path.exists():
        print("ℹ️  无 docs/TASK_GRAPH.md")
        return 0
    g = load_task_graph(tg_path)
    ready = g.ready()
    if not ready:
        print("（无可执行任务：要么都做完了，要么依赖未满足）")
        return 0
    print("🟢 可执行任务（依赖已满足）：")
    for t in ready:
        print(f"   - {t.name}")
    return 0


def cmd_advance(root: Path) -> int:
    phase = _detect_phase(root)
    ok, missing = can_advance(phase, _existing_files(root))
    nxt = next_phase(phase)
    if not ok:
        print(f"⛔ 当前阶段 {phase} 退出产物不全，不能前进。缺：{missing}")
        return 1
    gate = PHASE_DEFS[phase].hitl_gate
    if nxt is None:
        print(f"🏁 当前已是最后阶段 {phase}。")
    else:
        print(f"✅ 可从 {phase} 进入 {nxt}。")
    if gate:
        print(f"🚦 但需先通过人工门控 {gate}：{GATE_DESC.get(gate, '')}")
    return 0


def cmd_gate(gate_id: str) -> int:
    gid = gate_id.upper()
    if gid in GATE_DESC:
        print(f"🚦 {gid}：{GATE_DESC[gid]}")
        return 0
    print(f"未知 Gate：{gate_id}（可选 GATE-1..GATE-5）")
    return 1


def cmd_compare_plans(root: Path, days: int) -> int:
    """查看模型方案对比报告 (依赖 peer-review 模块)"""
    # 1. 动态加载 peer-review 模块
    # 假设 peer-review 位于 _factory/patterns/peer-review/src
    peer_review_path = root / "_factory" / "patterns" / "peer-review" / "src"
    if not peer_review_path.exists():
        print("❌ 未找到 peer-review 模式源码，无法执行方案对比。")
        return 1
    
    if str(peer_review_path) not in sys.path:
        sys.path.append(str(peer_review_path))

    try:
        from peer_review.platform.memory_store import MemoryStore
    except ImportError as e:
        print(f"❌ 导入 MemoryStore 失败: {e}")
        return 1

    # 2. 加载数据
    mem_db_path = root / "runtime" / "memory.db"
    if not mem_db_path.exists():
        print(f"ℹ️  未找到运行记录数据库: {mem_db_path}")
        return 0

    try:
        store = MemoryStore(mem_db_path)
        data = store.get_plan_comparison(days=days)
    except Exception as e:
        print(f"❌ 读取运行记录失败: {e}")
        return 1

    if not data:
        print(f"ℹ️  最近 {days} 天内没有运行记录。")
        return 0

    # 3. 展现结果
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title=f"🚀 模型方案对比报告 (最近 {days} 天)", show_header=True, header_style="bold magenta")
        table.add_column("方案 ID", style="cyan")
        table.add_column("样本数", justify="right")
        table.add_column("平均耗时", justify="right")
        table.add_column("平均成本", justify="right")
        table.add_column("平均分歧度", justify="right")
        table.add_column("平均质量", justify="right")

        for row in data:
            table.add_row(
                row["plan_id"],
                str(row["run_count"]),
                f"{row['avg_time_seconds']:.1f}s",
                f"${row['avg_cost_usd']:.4f}",
                f"{row['avg_divergence']:.2f}",
                f"{row['avg_quality']:.1f}" if row["avg_quality"] else "N/A",
            )
        console.print(Panel(table, expand=False))
    else:
        print(f"\n--- 模型方案对比报告 (最近 {days} 天) ---")
        print(f"{'方案ID':<15} | {'样本':<5} | {'耗时':<10} | {'成本':<10} | {'分歧度':<10} | {'质量':<10}")
        print("-" * 70)
        for row in data:
            print(f"{row['plan_id']:<15} | {row['run_count']:<5} | {row['avg_time_seconds']:<10.1f} | {row['avg_cost_usd']:<10.4f} | {row['avg_divergence']:<10.2f} | {row['avg_quality']:.1f if row['avg_quality'] else 'N/A':<10}")

    return 0


def _generate_ai_analysis(root: Path, stats_text: str) -> str:
    """调用 LLM 对项目构建日志和数据进行分析，生成复盘建议"""
    # 1. 动态加载依赖
    peer_review_path = root / "_factory" / "patterns" / "peer-review" / "src"
    if str(peer_review_path) not in sys.path:
        sys.path.append(str(peer_review_path))
    
    try:
        import yaml
        from peer_review.llm_client import chat
        from peer_review.config.schemas import ModelConfig, ModelType
    except ImportError as e:
        return f"❌ 无法加载 AI 分析依赖: {e}"

    # 2. 加载模型配置 (默认使用 local-qwen35b)
    models_path = root / "config" / "models.yaml"
    if not models_path.exists():
        return "❌ 未找到 config/models.yaml，无法启动 AI 分析。"
    
    with open(models_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    model_info = config_data["models"].get("local-qwen35b")
    if not model_info:
        return "❌ models.yaml 中缺失 local-qwen35b 配置。"
    
    model_cfg = ModelConfig(
        model_id=model_info["model_id"],
        type=ModelType(model_info["type"]),
        provider=model_info["provider"],
        base_url=model_info.get("base_url", ""),
    )

    # 3. 收集分析上下文
    build_log_path = root / "docs" / "BUILD_LOG.md"
    build_log_content = build_log_path.read_text(encoding="utf-8") if build_log_path.exists() else "无构建日志。"
    
    prompt = f"""你是一个 AI 项目架构师和复盘专家。请根据提供的【构建日志】和【运行数据】，为该项目生成一份经验教训复盘报告的初稿。

【运行数据汇总】:
{stats_text}

【构建日志】:
{build_log_content}

请严格按照以下格式输出（不要输出 Markdown 标题，直接输出内容）：

## 1. 成功经验（可复用的）
- [分析点] -> [具体建议]
...

## 2. 失败经验（避坑的）
- [痛点] -> [教训]
...

## 3. 改进建议（未来可做的）
- [优化方向] -> [具体操作]
...

## 4. 本项目产出的新 Skill / Pattern
- 新 Skill: [名称] - [作用]
- 新 Pattern: [名称] - [作用]
...
"""
    
    messages = [{"role": "user", "content": prompt}]
    resp = chat(model_cfg, messages)
    
    if resp.error:
        return f"❌ AI 分析失败: {resp.error}"
    return resp.content


def cmd_retro(args, root: Path) -> int:
    """生成项目复盘报告草稿"""
    # 1. 准备路径
    retro_path = root / "docs" / "RETRO.md"
    template_path = root / "_factory" / "lessons" / "_TEMPLATE.lesson.md"
    
    if not template_path.exists():
        print("❌ 未找到复盘模板: _factory/lessons/_TEMPLATE.lesson.md")
        return 1

    # 2. 收集数据
    # 尝试从项目结构推断项目名 (如果 root 是项目根目录)
    project_name = root.name if (root / "CHARTER.md").exists() else "unknown_project"
    
    # Use MemoryStore to get stats
    mem_db_path = root / "runtime" / "memory.db"
    stats_text = "待真机"
    model_versions = "未知"
    
    if mem_db_path.exists():
        # Load MemoryStore (lazy loading)
        peer_review_path = root / "_factory" / "patterns" / "peer-review" / "src"
        if peer_review_path.exists():
            if str(peer_review_path) not in sys.path:
                sys.path.append(str(peer_review_path))
            try:
                from peer_review.platform.memory_store import MemoryStore
                store = MemoryStore(mem_db_path)
                data = store.get_plan_comparison(days=365)
                if data:
                    lines = []
                    for row in data:
                        lines.append(f"- {row['plan_id']}: {row['run_count']}次, avg {row['avg_time_seconds']:.1f}s, avg ${row['avg_cost_usd']:.4f}, div {row['avg_divergence']:.2f}")
                    stats_text = "\n".join(lines)
                    model_versions = ", ".join([row['plan_id'] for row in data])
            except Exception as e:
                print(f"⚠️  收集运行记录失败: {e}")

    # 3. 生成文件
    template_content = template_path.read_text(encoding="utf-8")
    from datetime import date
    today = date.today().isoformat()
    
    # Simple replacements
    content = template_content.replace("<项目名>", project_name)
    content = content.replace("YYYY-MM-DD", today)
    content = content.replace("<用到的模型版本，如 qwen3.6-35b / glm-5.1>", model_versions)
    
    # Update Section 5 (Model and Cost)
    if "- 各 Phase 耗时：…" in content:
        content = content.replace("- 各 Phase 耗时：…", f"- 运行数据汇总：\n{stats_text}")

    # 4. AI-assisted analysis
    if getattr(args, "ai", False):
        print("🤖 正在调用 AI 分析构建日志和运行记录...")
        ai_analysis = _generate_ai_analysis(root, stats_text)
        
        # Replace placeholders for sections 1-4
        # We look for the markers in the template and replace them
        sections = [
            ("## 1. 成功经验（可复用的）\n- …", ""),
            ("## 2. 失败经验（避坑的）\n- …", ""),
            ("## 3. 改进建议（未来可做的）\n- …", ""),
            ("## 4. 本项目产出的新 Skill / Pattern（AC-008）\n- 新 Skill：…\n- 新 Pattern：…", ""),
        ]
        
        # The AI output is structured as ## 1... ## 2... etc.
        # We can split the AI output and replace each section.
        import re
        ai_sections = re.split(r"(?=## \d\.)", ai_analysis)
        
        for i in range(1, 5):
            sec_content = next((s for s in ai_sections if s.startswith(f"## {i}.")), None)
            if sec_content:
                # Find the corresponding marker in the template and replace the "..." part
                # Since the template has specific phrasing, we replace from the header down to the next header or end of section.
                # Simplified: replace the a whole block.
                pattern = rf"## {i}\. [^\n]*\n- .*?(?=\n## {i+1}\.|\n## 5\.|$)"
                # This is a bit complex for simple replace. Let's just replace the "..." markers.
                # Actually, let's just append the AI analysis to the end or replace the placeholders.
                pass

        # Better approach: replace the specific "..." markers in the template
        # But since the AI returns full sections, we just replace the template's placeholder lines.
        # For simplicity in this CLI, we will just append the AI analysis to the bottom 
        # or replace the sections if we can find them.
        
        # Let's try a simpler replacement: 
        # find the section header, then replace everything until the next section header.
        for i in range(1, 5):
            sec_content = next((s for s in ai_sections if s.startswith(f"## {i}.")), None)
            if sec_content:
                # Find the start of section i in the content
                start_marker = f"## {i}."
                start_idx = content.find(start_marker)
                if start_idx != -1:
                    # Find the end of this section (start of next section)
                    end_marker = f"## {i+1}." if i < 4 else "## 5."
                    end_idx = content.find(end_marker, start_idx)
                    if end_idx == -1: end_idx = len(content)
                    
                    content = content[:start_idx] + sec_content + content[end_idx:]

    # Write to docs/RETRO.md
    retro_path.parent.mkdir(parents=True, exist_ok=True)
    retro_path.write_text(content, encoding="utf-8")
    
    print(f"✅ 复盘草稿已生成: {retro_path}")
    print(f"👉 请在 {retro_path} 中补全 1-4 节的定性分析。")
    print(f"👉 完成后执行 'forge retro submit' 提交到工厂知识库。")
    return 0


def cmd_retro_submit(args, root: Path) -> int:
    """将复盘报告提交到 _factory/lessons/"""
    retro_path = root / "docs" / "RETRO.md"
    if not retro_path.exists():
        print(f"❌ 未找到复盘报告: {retro_path}")
        return 1
    
    content = retro_path.read_text(encoding="utf-8")
    # Extract lesson_id from YAML header
    import re
    match = re.search(r"lesson_id:\s*(\S+)", content)
    if not match:
        print("❌ 报告中缺失 lesson_id 字段，请先在 docs/RETRO.md 的 YAML 头中定义。")
        return 1
    
    lesson_id = match.group(1)
    dest_path = root / "_factory" / "lessons" / f"{lesson_id}.lesson.md"
    
    # HITL Gate-5 check
    print(f"🚦 提交到工厂知识库需通过 HITL Gate-5 审批。")
    print(f"目标路径: {dest_path}")
    confirm = input("是否确认提交？(y/n): ")
    if confirm.lower() != 'y':
        print("取消提交。")
        return 0
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")
    
    print(f"✅ 经验教训已写入工厂: {dest_path}")
    print(f"⚠️  请通知审核员进行 Gate-5 审批以正式生效。")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="forge", description="FORGE Factory CLI")
    p.add_argument("--root", default=".", help="项目根目录（含 docs/）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="查看所有项目当前阶段状态")
    n = sub.add_parser("new", help="创建新项目")
    n.add_argument("name", help="项目名称")
    n.add_argument("--domain", default="general", help="领域标识")
    sub.add_parser("check", help="校验任务图与退出产物")
    sub.add_parser("tasks", help="列出可执行任务")
    sub.add_parser("advance", help="检查能否进入下一阶段")
    g = sub.add_parser("gate", help="打印某 HITL Gate 说明")
    g.add_argument("gate_id")
    
    cp = sub.add_parser("compare-plans", help="查看模型方案对比报告")
    cp.add_argument("--days", type=int, default=30, help="对比的时间范围（天）")
    
    ev = sub.add_parser("eval", help="执行模型方案 A/B 测试")
    ev.add_argument("--plans", nargs="+", help="指定要测试的方案 ID 列表")
    
    r = sub.add_parser("retro", help="生成/提交复盘报告")
    r.add_argument("action", nargs="?", default="generate", choices=["generate", "submit"], help="generate (默认) 或 submit")
    r.add_argument("--ai", action="store_true", help="使用 AI 辅助分析构建日志和数据")
    
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.cmd == "new":
        return cmd_new(args, root)
    if args.cmd == "status":
        return cmd_status(root)
    if args.cmd == "check":
        return cmd_check(root)
    if args.cmd == "tasks":
        return cmd_tasks(root)
    if args.cmd == "advance":
        return cmd_advance(root)
    if args.cmd == "gate":
        return cmd_gate(args.gate_id)
    if args.cmd == "compare-plans":
        return cmd_compare_plans(root, args.days)
    if args.cmd == "eval":
        return cmd_eval(args, root)
    if args.cmd == "retro":
        if args.action == "generate":
            return cmd_retro(args, root)
        elif args.action == "submit":
            return cmd_retro_submit(args, root)
    return 2


if __name__ == "__main__":
    sys.exit(main())
