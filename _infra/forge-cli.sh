#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
#
# ============================================================================
# FORGE Factory · Manual Gate 辅助工具（境外模型手动接入，满足 C1 / FR-005）
# 用法：source ~/forge/_infra/forge-cli.sh
# 命令：forge_gate_input <gate>  |  forge_gate_output <gate>  |  forge_gate_skip <gate> <原因>
#       gate ∈ {discovery, spec, security}
# 设计原则：输入/输出文档格式固定，使"用哪个境外模型"对后续流程无影响（FR-005-2）。
# ============================================================================

# 生成 Manual Gate 输入文档并复制到剪贴板（macOS 用 pbcopy）
forge_gate_input() {
  local gate_id="${1:-discovery}"
  local er_dir="docs/external-review"
  local template_file="${er_dir}/_INPUT_TEMPLATE.md"
  local output_file="${er_dir}/${gate_id}-input.md"

  mkdir -p "$er_dir"
  if [ ! -f "$template_file" ]; then
    echo "❌ 找不到模板文件: $template_file（应由项目脚手架生成）"
    return 1
  fi

  case "$gate_id" in
    discovery)
      echo "📋 生成 Discovery Gate 输入文档..."
      { echo "# Discovery 评审请求（境外模型）"; echo ""; head -100 docs/DISCOVERY.md 2>/dev/null; } > "$output_file"
      ;;
    spec)
      echo "📋 生成 Spec Gate 输入文档..."
      { echo "# 架构方案评审请求"; echo ""; head -150 docs/SPEC.md 2>/dev/null; } > "$output_file"
      ;;
    security)
      echo "📋 生成 Security Gate 输入文档..."
      { echo "# 安全审查评审请求"; echo ""; cat docs/harden/SECURITY_REVIEW.md 2>/dev/null; } > "$output_file"
      ;;
    *)
      echo "❌ 未知 gate: $gate_id（支持 discovery / spec / security）"
      return 1
      ;;
  esac

  # 复制到剪贴板（macOS）；非 macOS 则跳过
  if command -v pbcopy >/dev/null 2>&1; then
    cat "$output_file" | pbcopy
    echo "✅ 已复制到剪贴板 → 粘贴到 ChatGPT/Claude 网页端"
  else
    echo "ℹ️  非 macOS，未复制剪贴板。请手动打开 $output_file 复制内容。"
  fi
  echo "📁 输入文档已保存到: $output_file"
}

# 保存 Manual Gate 输出结果（把网页端回答写回本地，满足 FR-005-3）
forge_gate_output() {
  local gate_id="${1:-discovery}"
  local er_dir="docs/external-review"
  local output_file="${er_dir}/${gate_id}-review.md"

  mkdir -p "$er_dir"
  echo "📥 请将 ChatGPT/Claude 的回答粘贴下方，输入完成后按 Ctrl+D："
  {
    echo "---"
    echo "# External Review: ${gate_id}"
    echo "# Generated: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S') CST"
    echo ""
    cat
  } >> "$output_file"
  echo "✅ 已保存到: $output_file"
}

# 带原因记录的跳过（不静默消失，RETRO 时可见，满足"反馈回流有记录"）
forge_gate_skip() {
  local gate_id="${1:-discovery}"
  local reason="${2:-未提供原因}"
  local er_dir="docs/external-review"
  local skip_file="${er_dir}/${gate_id}-skipped.md"

  mkdir -p "$er_dir"
  {
    echo "# Gate Skipped: ${gate_id}"
    echo "# Time: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S') CST"
    echo "# Reason: ${reason}"
  } > "$skip_file"
  echo "⚠️  Gate ${gate_id} 已跳过，原因已记录至 ${skip_file}"
  echo "    此记录将在 RETRO Phase 被审查。"
}

echo "✅ forge-cli loaded. Commands: forge_gate_input, forge_gate_output, forge_gate_skip"
