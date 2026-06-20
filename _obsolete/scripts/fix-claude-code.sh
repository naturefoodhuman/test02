#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 10:45:00

# Claude Code 终极连通性修复脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛠️  开始修复 Claude Code 连通性...${NC}"

# 1. 清理 ~/.zshrc 中的冗余
sed -i '' '/ANTHROPIC_BASE_URL/d' ~/.zshrc
sed -i '' '/OPENAI_BASE_URL/d' ~/.zshrc
sed -i '' '/CLAUDE_CODE_BASE_URL/d' ~/.zshrc
sed -i '' '/alias claude/d' ~/.zshrc

# 2. 创建配置目录
mkdir -p ~/.claude

# 3. 写入核心配置文件 (按老板提供的最佳实践)
cat << 'EOF' > ~/.claude/settings.json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-forge-local-anytoken",
    "ANTHROPIC_API_KEY": "sk-forge-local-anytoken",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "API_TIMEOUT_MS": "3000000"
  }
}
EOF

# 4. 验证
if [ -f ~/.claude/settings.json ]; then
    echo -e "${GREEN}✅ ~/.claude/settings.json 创建成功！${NC}"
else
    echo -e "${RED}❌ 创建失败，请检查权限。${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 正在重启 LiteLLM 网关...${NC}"
pkill -f litellm
sleep 2
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
source .venv/bin/activate
bash _infra/start-litellm.sh 4000 > /tmp/forge_litellm.log 2>&1 &

echo -e "${GREEN}✨ 修复完成！请重新打开终端或运行 source ~/.zshrc${NC}"
echo -e "${GREEN}现在输入 'claude' 试试看！${NC}"
