#!/usr/bin/env bash
# release.sh - 标准化发布流程
# 用法: ./release.sh [patch|minor|major] "发布说明"

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认版本类型
VERSION_TYPE="${1:-patch}"
RELEASE_NOTE="${2:-常规更新}"

# 获取当前版本 (从任意 pyproject.toml)
CURRENT_VERSION=$(grep '^version = ' projects/debt-collection/pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
if [ -z "$CURRENT_VERSION" ]; then
    CURRENT_VERSION=$(grep '^version = ' _factory/patterns/peer-review/pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
fi

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}❌ 无法获取当前版本号${NC}"
    exit 1
fi

echo -e "${GREEN}当前版本: ${CURRENT_VERSION}${NC}"

# 计算新版本
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
case "$VERSION_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo -e "${RED}❌ 无效的版本类型: $VERSION_TYPE (支持: patch|minor|major)${NC}"
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo -e "${GREEN}新版本: ${NEW_VERSION}${NC}"

# 确认
echo -e "${YELLOW}发布说明: ${RELEASE_NOTE}${NC}"
read -p "确认发布 v${NEW_VERSION}? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 运行测试
echo -e "${GREEN}🧪 运行测试...${NC}"
if ! python3 -m pytest _factory/patterns/peer-review/tests/verify_architecture.py -v; then
    echo -e "${RED}❌ 测试失败，中止发布${NC}"
    exit 1
fi

# 更新版本号到所有 pyproject.toml
echo -e "${GREEN}📝 更新版本号...${NC}"
sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" projects/debt-collection/pyproject.toml
sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" _factory/patterns/peer-review/pyproject.toml

# 更新 CHANGELOG.md
echo -e "${GREEN}📝 更新 CHANGELOG...${NC}"
DATE=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [${NEW_VERSION}] - ${DATE}\n\n### Changed\n- ${RELEASE_NOTE}\n"
# 在 CHANGELOG.md 的第一个 ## 之前插入
sed -i "1s/^/${CHANGELOG_ENTRY}\n/" docs/CHANGELOG.md 2>/dev/null || echo "${CHANGELOG_ENTRY}" > docs/CHANGELOG.md

# Git 提交和打标签
echo -e "${GREEN}📦 Git 提交和打标签...${NC}"
git add projects/debt-collection/pyproject.toml _factory/patterns/peer-review/pyproject.toml docs/CHANGELOG.md
git commit -m "chore: release v${NEW_VERSION}

${RELEASE_NOTE}"
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}

${RELEASE_NOTE}"

echo -e "${GREEN}✅ 发布完成: v${NEW_VERSION}${NC}"
echo -e "${YELLOW}💡 请运行: git push origin main --tags${NC}"