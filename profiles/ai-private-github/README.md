<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 14:55:00
-->

# AI Private GitHub Profile

Purpose: read-only private GitHub access for approved repositories.

## Allowed domains

- `github.com`
- `gist.github.com`

## Manual login flow

1. Start the isolated profile:
   ```bash
   _infra/network/scripts/start_private_chrome.sh ai-private-github 9222
   ```
2. Human manually logs into GitHub.
3. Do not save passwords.
4. Do not add payment methods.
5. Keep extensions disabled.

## Agent rules

- Read-only snapshot / text extraction by default.
- No posting, commenting, deleting, editing profile, or sending messages without
  explicit human approval.
- Never read cookies, localStorage, sessionStorage, tokens, SSH keys or payment data.
- Pipe extracted content through PrivacyGateway full mode.
