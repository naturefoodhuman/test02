<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 17:20:00
-->

# Diagnostics Scripts

This directory contains historical or ad-hoc diagnostic scripts that are not part
of the primary happy-path operations.

Current primary operations live at:

- `scripts/health-check.sh`
- `scripts/backup.sh`
- `scripts/switch-mode.sh`
- `scripts/run_playwright_action.py`
- `scripts/hooks/pre_tool_use.sh`
- `_infra/network/scripts/`

Before using any diagnostic script here, verify it still matches the current
architecture and configuration.
