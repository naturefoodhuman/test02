#!/bin/bash
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-20 16:45:00

# FORGE 智能启动脚本 v3.0 (自检并释放显存版)
# 职责：冷启动各端口模型进行可用性校验，成功后立即释放显存，实现“按需动态加载”基础。

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

FORGE_ROOT="/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
SERVER_DIR="/Users/naturist/LocalAI/servers"

echo -e "${BLUE}🚀 正在执行 FORGE 全量环境自检 (全端口冷启动校验)...${NC}"

# 精准检查函数
is_listening() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN > /dev/null 2>&1
}

# 校验并释放函数
check_and_unload() {
    local port=$1
    local name=$2
    local cmd=$3
    local kill_pattern=$4

    echo -e "${BLUE}📡 正在自检 $name (Port $port)...${NC}"
    
    # 1. 如果已运行，先停掉以进行纯净冷启动校验
    if is_listening "$port"; then
        pkill -f "$kill_pattern"
        sleep 2
    fi

    # 2. 启动
    eval "$cmd"
    
    # 3. 等待就绪
    echo -n "   ⏳ 加载权重中"
    SUCCESS=false
    for i in {1..40}; do
        if is_listening "$port"; then
            echo -e "${GREEN} OK!${NC}"
            SUCCESS=true
            break
        fi
        echo -n "."
        sleep 3
    done

    if [ "$SUCCESS" = true ]; then
        # 4. 校验通过，立即释放显存 (Unload)
        echo -e "${BLUE}   📥 校验通过，正在卸载 $name 以释放显存...${NC}"
        pkill -f "$kill_pattern"
        return 0
    else
        echo -e "${RED}\n❌ $name 自检失败，请检查相关日志。${NC}"
        return 1
    fi
}

# ── 执行自检序列 ──

# 1. Ollama (11434) - 这个作为基础守护进程，不卸载，但可以 unload 具体模型
if ! is_listening 11434; then
    echo -e "${BLUE}📡 启动 Ollama 守护进程...${NC}"
    ollama serve > /tmp/forge_ollama.log 2>&1 &
    sleep 3
fi

# 2. 主大脑 (8080) - MTPLX
check_and_unload 8080 "主大脑 (Qwen-MTPLX)" "cd $SERVER_DIR && nohup uv run mtplx quickstart --model Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality --port 8080 > /tmp/mtplx_8080.log 2>&1 &" "mtplx.*8080"

# 3. 评审模型 (8082) - MTPLX
check_and_unload 8082 "评审模型 (Gemma4-MTPLX)" "cd $SERVER_DIR && nohup uv run mtplx quickstart --model Youssofal/Gemma4-MTPLX-Optimized-Quality --port 8082 > /tmp/mtplx_8082.log 2>&1 &" "mtplx.*8082"

# 4. 深度评审 (8084) - Llama-server
check_and_unload 8084 "深度评审 (Qwopus-GGUF)" "nohup llama-server -m /Users/naturist/LocalAI/gguf-models/Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf --host 127.0.0.1 --port 8084 -c 65536 -ngl 99 -fa on --spec-type draft-mtp --spec-draft-n-max 2 > /tmp/llama_8084.log 2>&1 &" "llama-server.*8084"

# 5. 启动智能网关中继器 (4000) 与 核心网关 (4001)
if is_listening 4000; then pkill -f "uvicorn.*4000"; fi
if is_listening 4001; then pkill -f "litellm.*4001"; fi

echo -e "${BLUE}📥 启动核心网关 (4001)...${NC}"
cd "$FORGE_ROOT" && source .venv/bin/activate && nohup bash _infra/start-litellm.sh 4001 > /tmp/forge_litellm_4001.log 2>&1 &

# 等待核心网关就绪
for i in {1..10}; do
    if lsof -nP -iTCP:4001 -sTCP:LISTEN > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 核心网关 (4001) 已就绪${NC}"
        break
    fi
    sleep 1
done

echo -e "${BLUE}🚀 启动智能看门人 (4000)...${NC}"
nohup python3 _infra/smart_proxy.py > /tmp/forge_smart_proxy.log 2>&1 &

echo -e "${GREEN}✅ 环境自检与智能网关部署完成！${NC}"
echo -e "${BLUE}💡 系统现已准备好进行“按需加载”运行。${NC}"
