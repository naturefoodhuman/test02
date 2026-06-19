#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 14:00:00

# FORGE 智能启动脚本 v2.0 (显存保护版)
# 职责：按方案所需模型串行拉起，防止 64G 内存 OOM。

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

FORGE_ROOT="/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
VRAM_LIMIT=52 # M1 Max 64G，保留 12G 给系统

echo -e "${BLUE}🚀 正在进入 FORGE 智能启动流程...${NC}"

# 1. 解析参数 (获取 --plan)
PLAN="default"
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --plan) PLAN="$2"; shift ;;
    esac
    shift
done

# 2. 获取所需模型及其显存 (从 models.yaml 简化匹配)
echo -e "${BLUE}🔍 正在分析方案: $PLAN ...${NC}"
# 这里我们根据 common plans 进行预设，未来可改为 python 脚本动态解析
declare -A NEEDED_PORTS
TOTAL_VRAM=0

if [ "$PLAN" == "mtplx-hybrid" ]; then
    NEEDED_PORTS[8080]=20
    NEEDED_PORTS[8082]=16
    TOTAL_VRAM=36
elif [ "$PLAN" == "all-local" ]; then
    NEEDED_PORTS[11434]=24 # Ollama 多模型混合
    TOTAL_VRAM=24
elif [ "$PLAN" == "deep-review" ]; then
    NEEDED_PORTS[8080]=20
    NEEDED_PORTS[8084]=36
    TOTAL_VRAM=56
fi

# 3. 显存红线检查
if [ $TOTAL_VRAM -gt $VRAM_LIMIT ]; then
    echo -e "${RED}❌ 警告：方案 $PLAN 预估占用 ${TOTAL_VRAM}GB，超过安全红线 ${VRAM_LIMIT}GB！${NC}"
    echo -e "${RED}防止死机，拒绝启动。请修改方案或手动降低模型规格。${NC}"
    exit 1
fi

# 4. 串行启动函数
start_service() {
    local port=$1
    local name=$2
    local cmd=$3
    
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name (Port $port) 已在运行${NC}"
    else
        echo -e "${BLUE}📡 正在拉起 $name (Port $port)...${NC}"
        eval "$cmd"
        # 串行等待该服务就绪再继续，防止瞬间爆内存/IO
        echo -n "⏳ 等待 $name 加载权重"
        for i in {1..30}; do
            if lsof -nP -iTCP:"$port" -sTCP:LISTEN > /dev/null 2>&1; then
                echo -e "${GREEN} OK!${NC}"
                return 0
            fi
            echo -n "."
            sleep 3
        done
        echo -e "${RED} 超时！${NC}"
        return 1
    fi
}

# 5. 执行启动序列
start_service 11434 "Ollama" "ollama serve > /tmp/forge_ollama.log 2>&1 &"

if [[ ${NEEDED_PORTS[8080]} ]]; then
    start_service 8080 "主大脑 (Qwen)" "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/mtplx_8080.log 2>&1 &"
fi

if [[ ${NEEDED_PORTS[8082]} ]]; then
    start_service 8082 "评审模型 (Gemma4)" "cd ~/LocalAI/servers && nohup uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/mtplx_8082.log 2>&1 &"
fi

if [[ ${NEEDED_PORTS[8084]} ]]; then
    start_service 8084 "深度评审 (Qwopus)" "nohup llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/llama_8084.log 2>&1 &"
fi

# 6. 最后拉起网关
start_service 4000 "LiteLLM 网关" "cd $FORGE_ROOT && source .venv/bin/activate && nohup bash _infra/start-litellm.sh 4000 > /tmp/litellm.log 2>&1 &"

echo -e "${GREEN}✨ 方案 $PLAN 启动成功！预估显存占用: ${TOTAL_VRAM}GB / ${VRAM_LIMIT}GB${NC}"
