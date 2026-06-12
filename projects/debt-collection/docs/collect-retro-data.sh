#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 03:00:00 CST
#
# ============================================================================
# RETRO 真机数据一键收集（保姆级，遵守规则 R3）
# 作用：把"BUILD测试/安全自检/GLM策略/本地策略"结果统一收集到文件，老板 push 给 Agent 分析。
#
# 【怎么用】（逐步）：
#   终端A：cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
#          source ~/.venv/bin/activate
#          bash _infra/start-litellm.sh          # 起 GLM 网关，保持开着(留在终端A)
#   终端B（新开窗口）：
#          cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
#          source ~/.venv/bin/activate
#          bash projects/debt-collection/docs/collect-retro-data.sh
#   跑完 → git add/commit/push（脚本结尾会提示命令）→ 告诉 Agent "push 好了"
# ============================================================================
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJ="$ROOT/projects/debt-collection"
OUT="$ROOT/runtime/retro-data"     # 收集到这里（runtime 已 gitignore，但本脚本会单独把汇总文件放可提交处）
SHARE="$ROOT/retro-data-share"     # 这个目录用于 push 给 Agent（不含敏感真实案件，仅测试数据）
mkdir -p "$OUT" "$SHARE"
DB="$OUT/retro_demo.db"            # 用演示数据，不碰你的真实案件库
rm -f "$DB"

cd "$PROJ" || exit 1
export PYTHONPATH=src

echo "================ RETRO 数据收集 ================"

echo "【1/5】BUILD 测试" | tee "$SHARE/01_pytest.txt"
python -m pytest -q 2>&1 | tee -a "$SHARE/01_pytest.txt"

echo "【2/5】HARDEN 安全自检" | tee "$SHARE/02_security_scan.txt"
bash docs/harden/security_scan.sh 2>&1 | tee -a "$SHARE/02_security_scan.txt"

echo "【3/5】准备演示债务+情报（用假数据，不碰真实案件）"
python -m debt.cli --db "$DB" add "演示债务人" 50000 --due 2025-01-01 --region 浙江杭州 --evidence "借条,转账记录" >/dev/null
python -m debt.cli --db "$DB" intel 1 "债务人当选村支书" --source 朋友 >/dev/null
echo "  已准备。"

echo "【4/5】GLM 策略报告（需终端A 网关开着）" | tee "$SHARE/03_strategy_glm.txt"
python -m debt.cli --db "$DB" report 1 --model cloud/glm-primary 2>&1 | tee -a "$SHARE/03_strategy_glm.txt"

echo "【5/5】本地模型策略报告（对比用，需 ollama 在跑）" | tee "$SHARE/04_strategy_local.txt"
python -m debt.cli --db "$DB" report 1 --model local/primary 2>&1 | tee -a "$SHARE/04_strategy_local.txt"

rm -f "$DB"   # 删演示数据
echo ""
echo "✅ 收集完成，文件在：$SHARE"
echo ""
echo "【下一步】把结果 push 给 Agent 分析（终端B 继续执行）："
echo "  cd $ROOT"
echo "  git add retro-data-share/"
echo "  git commit -m 'retro data from real machine'"
echo "  git push"
echo "然后告诉 Agent：push 好了。"
echo ""
echo "⚠️ 这些是演示数据，不含你的真实案件隐私，可安全 push。"
