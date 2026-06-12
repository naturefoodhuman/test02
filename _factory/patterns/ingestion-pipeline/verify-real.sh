#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
#
# ============================================================================
# Ingestion 层 · 真机验证脚本（第13轮，老板在 Mac 上跑）
# 沙箱没有 MinerU/FunASR/你的真实文件，所以真实解析效果必须真机验证。
# 用法：
#   1) 把要测的真实资料(合同PDF/借据图片/通话录音)放到一个目录，如 ~/forge_test_data
#   2) bash _factory/patterns/ingestion-pipeline/verify-real.sh ~/forge_test_data
# ============================================================================
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 找到项目根（含 _infra 的目录），把产物放项目内 runtime/，不污染用户根目录
PROJECT_ROOT="$(cd "$HERE/../../.." && pwd)"
RUNTIME_DIR="$PROJECT_ROOT/runtime/ingestion"
# 默认：测试数据和输出都放项目内 runtime/（可被 .gitignore 忽略），不再用 ~ 根目录
DATA_DIR="${1:-$RUNTIME_DIR/test_data}"
OUT_DIR="${2:-$RUNTIME_DIR/out}"

echo "================ Ingestion 真机验证 ================"
echo "资料目录: $DATA_DIR"
echo "输出目录: $OUT_DIR"
echo ""

# 1) 检查增强库
echo "【1/3】检查增强库（缺失会降级，不影响核心流程）"
check_lib() { python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" 2>/dev/null \
  && echo "  ✅ $1 已装" || echo "  ⚠️ $1 未装 → 该类型会降级。安装：$2"; }
check_lib markitdown "pip install 'markitdown[all]'（MIT，多格式：Office/图片/PDF；务必带[all]否则 docx/pptx/xlsx 会失败）"
check_lib pypdf "pip install pypdf（PDF 纯文本降级）"
check_lib mineru "见 MinerU 官方文档（中文复杂版面 PDF/图片首选，模型较大）"
check_lib funasr "pip install funasr（通话录音转写+说话人分离，中文最强）"
echo ""

# 2) 准备数据目录
if [ ! -d "$DATA_DIR" ]; then
  echo "【2/3】资料目录不存在，自动创建并放一个示例文本：$DATA_DIR"
  mkdir -p "$DATA_DIR"
  printf '# 借款示例\n\n张三于2024年1月借款5万元，约定半年还清。\n' > "$DATA_DIR/示例借条.md"
  echo "  → 已放入 示例借条.md。建议你再放入真实的 合同.pdf / 借据.jpg / 通话.wav 后重跑。"
else
  echo "【2/3】资料目录已存在，包含文件："
  ls -1 "$DATA_DIR" | sed 's/^/  · /'
fi
echo ""

# 3) 跑 ingestion
echo "【3/3】运行 Ingestion（PYTHONPATH=src）"
cd "$HERE"
PYTHONPATH=src python -m ingestion.cli "$DATA_DIR" -o "$OUT_DIR" -v
echo ""
echo "✅ 完成。请打开 $OUT_DIR 查看每个文件的 .md(结构化) 和 .json(机器可读)。"
echo "   若 PDF/图片/录音显示『降级』，按上面【1/3】提示装对应库后重跑即可看到真实解析效果。"
