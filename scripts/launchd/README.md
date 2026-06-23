<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 16:35:00
-->

# launchd jobs for FORGE Network

This directory contains macOS launchd job templates.

## Jobs

- `com.network-agent.health.plist`
  - runs `scripts/health-check.sh` every 5 minutes
  - appends logs to `runtime/logs/launchd-health.log`
- `com.network-agent.mcp-scan.plist`
  - runs `_infra/network/scripts/scan_mcp.sh --lockfile config/mcp_lockfile.yaml`
  - schedule: every Sunday at 03:00
  - appends logs to `runtime/logs/launchd-mcp-scan.log`

## Install

Terminal A:

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
# no virtualenv required
mkdir -p ~/Library/LaunchAgents runtime/logs
cp scripts/launchd/com.network-agent.health.plist ~/Library/LaunchAgents/
cp scripts/launchd/com.network-agent.mcp-scan.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.network-agent.health.plist
launchctl load ~/Library/LaunchAgents/com.network-agent.mcp-scan.plist
```

Expected:

```text
launchctl exits 0; logs appear under runtime/logs/launchd-*.log after scheduled runs.
```

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.network-agent.health.plist || true
launchctl unload ~/Library/LaunchAgents/com.network-agent.mcp-scan.plist || true
rm ~/Library/LaunchAgents/com.network-agent.health.plist
rm ~/Library/LaunchAgents/com.network-agent.mcp-scan.plist
```
