#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 10:15:00

# FORGE 一键启动脚本 (Mac M1 Max 64G 深度定制版)
# 职责：按顺序拉起所有本地模型服务、网关，并进行可用性检测。

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 正在启动 FORGE AI 项目孵化工厂 (全量模型服务)...${NC}"

# 函数：检查端口是否占用
check_port() {
    lsof -i:"$1" > /dev/null 2>&1
}

# 1. Ollama 自检 (11434)
if ! check_port 11434; then
    echo -e "${BLUE}📡 启动 Ollama...${NC}"
    ollama serve > /tmp/forge_ollama.log 2>&1 &
    sleep 3
fi

# 2. 启动主大脑 (8080) - MTPLX (Qwen3.6-27B)
if ! check_port 8080; then
    echo -e "${BLUE}🧠 启动主大脑 (MTPLX 8080)...${NC}"
    # 切换到服务器目录并启动
    (cd ~/LocalAI/servers && uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/forge_mtplx_8080.log 2>&1) &
fi

# 3. 启动评审模型 (8082) - MTPLX (Gemma4)
if ! check_port 8082; then
    echo -e "${BLUE}🔍 启动评审模型 (MTPLX 8082)...${NC}"
    (cd ~/LocalAI/servers && uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/forge_mtplx_8082.log 2>&1) &
fi

# 4. 启动深度评审模型 (8084) - Llama-server (Qwopus)
if ! check_port 8084; then
    echo -e "${BLUE}⚖️ 启动深度评审 (Llama-server 8084)...${NC}"
    llama-server \
      -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf \
      --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/forge_llama_8084.log 2>&1 &
fi

# 5. 启动 LiteLLM 网关 (4000)
if ! check_port 4000; then
    echo -e "${BLUE}📥 启动 LiteLLM 网关 (4000)...${NC}"
    # 确保在项目根目录并激活 venv
    FORGE_ROOT="/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
    (cd "$FORGE_ROOT" && source .venv/bin/activate && bash _infra/start-litellm.sh 4000 > /tmp/forge_litellm.log 2>&1) &
fi

# 6. 综合健康检查循环
echo -ne "${BLUE}⏳ 等待所有服务就绪...${NC}"
PORTS=(11434 8080 8082 8084 4000)
MAX_RETRIES=60
RETRY_COUNT=0

while true; do
    ALL_UP=true
    for port in "${PORTS[@]}"; do
        if ! check_port "$port"; then
            ALL_UP=false
            break
        fi
    done
    
    if [ "$ALL_UP" = true ]; then
        # 额外测试网关 API 可用性
        if curl -s http://localhost:4000/v1/models > /dev/null; then
            echo -e "${GREEN} OK!${NC}"
            break
        fi
    fi
    
    echo -ne "."
    sleep 2
    ((RETRY_COUNT++))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}\n❌ 服务启动超时或端口冲突，请检查 /tmp/forge_*.log${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ 全部本地模型服务器 (8080, 8082, 8084) 已启动${NC}"
echo -e "${GREEN}✅ LiteLLM 网关 (4000) 已就绪${NC}"
echo -e "${BLUE}🛠️  Claude Code (CLI) 接入提示：${NC}"
echo -e "   已在 ~/.zshrc 配置别名，现在可以直接运行 ${GREEN}claude${NC}"
echo -e "   注意：如果仍然报错，请确保已运行 ${GREEN}source ~/.zshrc${NC}"
