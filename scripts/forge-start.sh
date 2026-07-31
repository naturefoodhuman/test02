
#!/bin/bash
# FORGE 智能启动脚本 v3.1 (自检并释放显存版 + SSD Cache 目录预建)
# 职责：冷启动各端口模型进行可用性校验，成功后立即释放显存，实现"按需动态加载"基础。

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

FORGE_ROOT="/Users/naturist/MusicProject/AI-Project-Incubation-Factory"
SERVER_DIR="/Users/naturist/LocalAI/servers"

# 确保 MTPLX SSD Session Cache 目录存在，避免因目录不存在导致启动失败（文档 §14.6）
mkdir -p "$HOME/.mtplx/session_cache/8080"
mkdir -p "$HOME/.mtplx/session_cache/8082"

echo -e "${BLUE}🚀 正在执行 FORGE 全量环境自检 (全端口冷启动校验)...${NC}"

# 精准检查函数
is_listening() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN > /dev/null 2>&1
}

# 按端口停止监听进程：比 pkill pattern 更可靠，避免旧 smart_proxy_streaming.py 占住 4000。
stop_listening_port() {
    local port=$1
    local pids
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -z "$pids" ]; then
        return 0
    fi
    echo -e "${BLUE}🧹 停止占用端口 $port 的进程: $pids${NC}"
    kill $pids 2>/dev/null || true
    for i in {1..20}; do
        if ! is_listening "$port"; then
            return 0
        fi
        sleep 0.2
    done
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "${BLUE}🧹 强制停止端口 $port 的残留进程: $pids${NC}"
        kill -9 $pids 2>/dev/null || true
    fi
}

model_command() {
    python3 "$FORGE_ROOT/_infra/model_runtime.py" command "$1"
}

model_kill_pattern() {
    python3 "$FORGE_ROOT/_infra/model_runtime.py" kill-pattern "$1"
}

load_ollama_runtime_env() {
    eval "$(python3 "$FORGE_ROOT/_infra/model_runtime.py" env-shell ollama)"
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
    load_ollama_runtime_env
    echo -e "${BLUE}   OLLAMA_FLASH_ATTENTION=${OLLAMA_FLASH_ATTENTION:-} OLLAMA_KV_CACHE_TYPE=${OLLAMA_KV_CACHE_TYPE:-}${NC}"
    ollama serve > /tmp/forge_ollama.log 2>&1 &
    sleep 3
fi

# 2. 主大脑 (8080) - MTPLX
check_and_unload 8080 "主大脑 (Qwen-MTPLX)" "$(model_command 8080)" "$(model_kill_pattern 8080)"

# 3. 评审模型 (8082) - MTPLX
check_and_unload 8082 "评审模型 (Gemma4-MTPLX)" "$(model_command 8082)" "$(model_kill_pattern 8082)"

# 4. 深度评审 (8084) - Llama-server
check_and_unload 8084 "深度评审 (Qwopus-GGUF)" "$(model_command 8084)" "$(model_kill_pattern 8084)"

# 5. 启动智能网关中继器 (4000) 与 核心网关 (4001)
stop_listening_port 4000
stop_listening_port 4001

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
echo -e "${BLUE}💡 系统现已准备好进行"按需加载"运行。${NC}"