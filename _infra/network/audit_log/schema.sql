-- audit_log/schema.sql
-- 审计数据库 Schema（FORGE Network 增量）
-- 位置：_infra/network/audit_log/schema.sql
-- 使用：python _infra/network/scripts/init_audit_db.py

-- 工具调用审计（核心）
CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,               -- tool_call | tool_deny | mcp_schema_change
    server_id TEXT,
    tool_name TEXT,
    mode TEXT NOT NULL,                     -- coding | research | private
    decision TEXT NOT NULL,                 -- allow | deny | require_approval
    details TEXT NOT NULL,                  -- JSON
    trace_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_created ON tool_calls(created_at);
CREATE INDEX IF NOT EXISTS idx_tool_calls_server_tool ON tool_calls(server_id, tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_mode ON tool_calls(mode);

-- MCP Schema 变更记录（rug pull 检测）
CREATE TABLE IF NOT EXISTS mcp_schema_changes (
    id TEXT PRIMARY KEY,
    server_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    old_hash TEXT,
    new_hash TEXT NOT NULL,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    approved_by TEXT,
    approved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_schema_changes_server ON mcp_schema_changes(server_id);

-- 浏览器会话记录
CREATE TABLE IF NOT EXISTS browser_sessions (
    id TEXT PRIMARY KEY,
    profile_name TEXT NOT NULL,
    start_url TEXT,
    mode TEXT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT,
    status TEXT,                            -- active | expired | closed
    details TEXT                            -- JSON (last_snapshot 等)
);

CREATE INDEX IF NOT EXISTS idx_browser_sessions_profile ON browser_sessions(profile_name);

-- 浏览器高危操作记录
CREATE TABLE IF NOT EXISTS browser_actions (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES browser_sessions(id),
    action_type TEXT NOT NULL,              -- click | type | submit | navigate
    target TEXT,
    payload TEXT,                           -- 脱敏后
    risk_level TEXT,                        -- low | high
    approved BOOLEAN,
    approved_by TEXT,
    executed_at TEXT,
    details TEXT
);

-- Canary token 命中记录
CREATE TABLE IF NOT EXISTS canary_hits (
    id TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    source TEXT,                            -- search | extract | browser | privacy
    hit_location TEXT,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    details TEXT
);

-- 隐私检测事件（可选，与 Privacy Gateway 联动）
CREATE TABLE IF NOT EXISTS privacy_detections (
    id TEXT PRIMARY KEY,
    pii_type TEXT,
    count INTEGER,
    source_url TEXT,
    mode TEXT,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    details TEXT
);

-- 每日指标（轻量）
CREATE TABLE IF NOT EXISTS metrics_daily (
    date TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (date, metric_name)
);