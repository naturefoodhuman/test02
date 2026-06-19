#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 12:30:00

# FORGE 全量一键启动脚本 - 增强版 (Mac M1 Max 专用)

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 路径常量
FORGE_ROOT="/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
SERVER_DIR="/Users/naturist/LocalAI/servers"
LOG_DIR="$FORGE_ROOT/runtime/logs"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}🚀 正在启动 FORGE AI 项目孵化工厂 (全量服务)...${NC}"

# 精准检查函数：只检查正在监听的端口
is_listening() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN > /dev/null 2>&1
}

# 1. 启动 8080 (主大脑 - Qwen3.6-27B-MTPLX)
if is_listening 8080; then
    echo -e "${GREEN}✅ 8080 (主大脑) 已在运行${NC}"
else
    echo -e "${BLUE}🧠 启动 8080 (主大脑 - Qwen)...${NC}"
    nohup bash -c "cd $SERVER_DIR && uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080" > "$LOG_DIR/mtplx_8080.log" 2>&1 &
fi

# 2. 启动 8082 (评审 - Gemma4-MTPLX)
if is_listening 8082; then
    echo -e "${GREEN}✅ 8082 (评审模型) 已在运行${NC}"
else
    echo -e "${BLUE}🔍 启动 8082 (评审 - Gemma4)...${NC}"
    nohup bash -c "cd $SERVER_DIR && uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082" > "$LOG_DIR/mtplx_8082.log" 2>&1 &
fi

# 3. 启动 8084 (深度评审 - Qwopus-35B Llama-server)
if is_listening 8084; then
    echo -e "${GREEN}✅ 8084 (深度评审) 已在运行${NC}"
else
    echo -e "${BLUE}⚖️  启动 8084 (深度评审 - Qwopus)...${NC}"
    nohup llama-server \
      -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf \
      --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > "$LOG_DIR/llama_8084.log" 2>&1 &
fi

# 4. 启动 4000 (LiteLLM 网关)
if is_listening 4000; then
    echo -e "${GREEN}✅ 4000 (LiteLLM 网关) 已在运行${NC}"
else
    echo -e "${BLUE}📥 启动 4000 (LiteLLM 网关)...${NC}"
    nohup bash -c "cd $FORGE_ROOT && source .venv/bin/activate && bash _infra/start-litellm.sh 4000" > "$LOG_DIR/litellm.log" 2>&1 &
fi

# 5. 健康检查
echo -ne "${BLUE}⏳ 等待服务就绪...${NC}"
for i in {1..20}; do
    if curl -s http://localhost:4000/v1/models > /dev/null; then
        echo -e "${GREEN} OK!${NC}"
        echo -e "${GREEN}✨ 工厂心脏已开始跳动！${NC}"
        exit 0
    fi
    echo -n "."
    sleep 3
done

echo -e "${RED}\n❌ 网关启动超时，请检查 $LOG_DIR/litellm.log${NC}"
exit 1
