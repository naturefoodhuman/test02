<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 15:16:58
-->

# AI Public Browser Profile

Purpose: public web browsing and low-risk automation.

## Rules

- No private account login.
- No password manager.
- No payment information.
- No private profile reuse.
- Public pages only.
- All extracted content must pass InputSanitizer and PrivacyGateway light mode.
- JS execution / screenshot / PDF flows require explicit policy approval when enabled.

## Default blocked origins

- `https://accounts.google.com`
- high-risk login / banking / payment sites as configured by MCP Guard policies
