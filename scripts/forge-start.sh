#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-19 18:30:00

# FORGE 一键启动脚本 (Mac M1 Max 64G 优化版)

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 正在启动 FORGE AI 项目孵化工厂...${NC}"

# 1. Ollama 自检
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${RED}⚠️ Ollama 未启动，尝试拉起...${NC}"
    ollama serve &
    sleep 5
else
    echo -e "${GREEN}✅ Ollama 已在运行${NC}"
fi

# 2. 检查本地模型是否存在
echo -e "${BLUE}🔍 检查核心模型...${NC}"
REQUIRED_MODELS=("qwen2.5:7b" "deepseek-r1:32b" "bge-m3")
for model in "${REQUIRED_MODELS[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo -e "${RED}⚠️ 缺少模型 $model，请稍后手动运行 ollama pull $model${NC}"
    fi
done

# 3. 启动 LiteLLM 网关 (终端 B 模拟)
echo -e "${BLUE}📥 启动 LiteLLM 网关 (端口 4000)...${NC}"
bash _infra/start-litellm.sh &
sleep 3

# 4. 检查 VS Code 插件接入
echo -e "${BLUE}🛠️ Claude Code 接入提示：${NC}"
echo -e "请在 VS Code 终端设置环境变量："
echo -e "${GREEN}export OPENAI_BASE_URL=http://localhost:4000/v1${NC}"
echo -e "${GREEN}export OPENAI_API_KEY=sk-forge-local-anytoken${NC}"

# 5. 自检
echo -e "${BLUE}🧪 运行系统连通性自检...${NC}"
source .venv/bin/activate
python3 -c "import urllib.request; print('✅ 网关连通性:', '成功' if urllib.request.urlopen('http://localhost:4000/v1/models').getcode()==200 else '失败')"

echo -e "${GREEN}✨ FORGE 工厂已就绪！${NC}"
