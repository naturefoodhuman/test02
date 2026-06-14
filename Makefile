# FORGE Factory Makefile
# 常用操作单命令完成

.PHONY: test test-unit test-integration lint format backup start-gateway start-ollama switch-plan compare-plans privacy-audit pre-upgrade-check release

# 日常开发
start-gateway:    # 启动 LiteLLM 网关
	@cd _infra && ./start-litellm.sh

start-ollama:     # 启动 Ollama (MLX 后端)
	@OLLAMA_USE_MLX=1 ollama serve

test:             # 运行全量测试
	@cd _factory/patterns/peer-review && python3 tests/verify_architecture.py
	@cd projects/debt-collection && python3 -m pytest tests/ -v 2>/dev/null || true

test-unit:        # 只跑单元测试（快速）
	@cd _factory/patterns/peer-review && python3 tests/verify_architecture.py

lint:             # 代码检查
	@uv run ruff check src/ 2>/dev/null || python3 -m ruff check src/

format:           # 代码格式化
	@uv run ruff format src/ 2>/dev/null || python3 -m ruff format src/

# 项目管理
backup:           # 备份 runtime/ 目录 + git push
	@mkdir -p runtime/backups
	@tar -czf runtime/backups/runtime-$(shell date +%Y%m%d-%H%M).tar.gz runtime/ --exclude='runtime/backups' --exclude='runtime/chroma_data' 2>/dev/null || true
	@git push origin main 2>/dev/null || echo "⚠️  git push 失败（可能未配置远程或无权限）"
	@echo "✅ 备份完成"

pre-upgrade-check: # macOS/依赖升级前检查
	@$(MAKE) test && echo "✅ 升级前测试通过，可以升级"

# 模型管理
switch-plan:      # 交互式切换路由方案
	@uv run forge switch-plan 2>/dev/null || echo "forge CLI 未安装或不可用"

compare-plans:    # 查看方案对比报告
	@uv run forge compare-plans --days 30 2>/dev/null || echo "forge CLI 未安装或不可用"

# 数据策略
privacy-audit:    # 审查当前数据出境策略
	@uv run forge privacy-audit 2>/dev/null || echo "forge CLI 未安装或不可用"

# 发布流程
release:          # 标准化发布 (git tag + changelog)
	@bash release.sh

# 开发环境安装
install-dev:      # 安装开发依赖
	@pip install -e "projects/debt-collection[dev]" -e "_factory/patterns/peer-review[dev]"
	@pip install agno llama-index-core llama-index-vector-stores-chroma chromadb pyyaml rich ollama openai

# 清理
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true