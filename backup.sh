#!/usr/bin/env bash
# backup.sh - 数据备份脚本
# 每日自动备份 SQLite + ChromaDB 到 runtime/backups/

set -euo pipefail

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKUP_DIR="runtime/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/runtime-${DATE}.tar.gz"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo -e "${GREEN}📦 开始备份 runtime/ 目录...${NC}"

# 排除备份目录本身和 chroma_data (体积大、可重建)
tar -czf "${BACKUP_FILE}" \
    --exclude='runtime/backups' \
    --exclude='runtime/chroma_data' \
    --exclude='runtime/__pycache__' \
    runtime/ 2>/dev/null || {
    echo -e "${RED}❌ 备份失败${NC}"
    exit 1
}

# 显示备份信息
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo -e "${GREEN}✅ 备份完成: ${BACKUP_FILE} (${BACKUP_SIZE})${NC}"

# 保留最近 30 个备份，删除旧的
echo -e "${GREEN}🧹 清理 30 天前的旧备份...${NC}"
find "${BACKUP_DIR}" -name "runtime-*.tar.gz" -type f -mtime +30 -delete 2>/dev/null || true
REMAINING=$(ls -1 "${BACKUP_DIR}"/runtime-*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}📁 当前保留备份数: ${REMAINING}${NC}"

# 同时备份 debt.db 单独文件（便于快速恢复）
if [ -f "runtime/debt.db" ]; then
    cp "runtime/debt.db" "${BACKUP_DIR}/debt-${DATE}.db"
    echo -e "${GREEN}✅ debt.db 单独备份完成${NC}"
fi

# 如果存在 memory.db 也备份
if [ -f "runtime/memory.db" ]; then
    cp "runtime/memory.db" "${BACKUP_DIR}/memory-${DATE}.db"
    echo -e "${GREEN}✅ memory.db 单独备份完成${NC}"
fi