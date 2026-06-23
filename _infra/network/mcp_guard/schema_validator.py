# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-23 10:42:00

"""
MCP tool schema hash validation (E2-C3-S1-T1).

Purpose:
- Canonicalize MCP tool schemas and compute stable SHA256 hashes.
- Store pinned hashes in ``config/mcp_lockfile.yaml``.
- Detect schema mutation / rug pull and record changes in ``runtime/audit.db``
  table ``mcp_schema_changes``.
- Raise ``MCPSchemaChangedError`` when a previously pinned schema changes.

This module does not implement transport-specific MCP calls. It accepts the
``tools/list`` response object (or list of tool objects) so future MCP clients /
PreToolUse hooks can reuse the same validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping
import uuid

import yaml

from ..exceptions import MCPSchemaChangedError, NetworkConfigError


@dataclass(frozen=True)
class ToolSchemaPin:
    """Pinned schema hash metadata for one MCP tool."""

    server_id: str
    tool_name: str
    schema_hash: str
    pinned_at: str


@dataclass(frozen=True)
class ToolSchemaValidationResult:
    """Validation result for one MCP tool schema."""

    server_id: str
    tool_name: str
    schema_hash: str
    status: str  # pinned | unchanged


def canonicalize_schema(schema: Mapping[str, Any]) -> str:
    """Return canonical JSON for stable hashing."""
    return json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_schema_hash(schema: Mapping[str, Any]) -> str:
    """Compute SHA256 hash for a JSON-schema-like mapping."""
    return hashlib.sha256(canonicalize_schema(schema).encode("utf-8")).hexdigest()


class SchemaHashStore:
    """YAML-backed schema hash store inside config/mcp_lockfile.yaml."""

    def __init__(self, lockfile_path: str | Path = "config/mcp_lockfile.yaml"):
        self.lockfile_path = Path(lockfile_path)

    def _load(self) -> dict[str, Any]:
        if not self.lockfile_path.exists():
            return {"version": "1.0", "servers": {}}
        data = yaml.safe_load(self.lockfile_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise NetworkConfigError(f"Invalid MCP lockfile structure: {self.lockfile_path}")
        data.setdefault("version", "1.0")
        data.setdefault("servers", {})
        return data

    def _save(self, data: Mapping[str, Any]) -> None:
        self.lockfile_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode\n"
            "# 创建时间（北京时间）：2026-06-23 10:42:00\n\n"
        )
        self.lockfile_path.write_text(
            header + yaml.safe_dump(dict(data), allow_unicode=True, sort_keys=True),
            encoding="utf-8",
        )

    def get_hash(self, server_id: str, tool_name: str) -> str | None:
        data = self._load()
        server = data.get("servers", {}).get(server_id, {})
        tools = server.get("tools", {}) if isinstance(server, Mapping) else {}
        tool = tools.get(tool_name, {}) if isinstance(tools, Mapping) else {}
        value = tool.get("schema_hash") if isinstance(tool, Mapping) else None
        return str(value) if value else None

    def set_hash(self, server_id: str, tool_name: str, schema_hash: str) -> ToolSchemaPin:
        data = self._load()
        servers = data.setdefault("servers", {})
        server = servers.setdefault(server_id, {})
        if not isinstance(server, dict):
            server = {}
            servers[server_id] = server
        tools = server.setdefault("tools", {})
        pinned_at = datetime.now(timezone.utc).isoformat()
        tools[tool_name] = {
            "schema_hash": schema_hash,
            "pinned_at": pinned_at,
        }
        self._save(data)
        return ToolSchemaPin(
            server_id=server_id,
            tool_name=tool_name,
            schema_hash=schema_hash,
            pinned_at=pinned_at,
        )


class MCPToolSchemaValidator:
    """Validate MCP tool schemas against pinned hashes."""

    def __init__(
        self,
        lockfile_path: str | Path = "config/mcp_lockfile.yaml",
        audit_db_path: str | Path = "runtime/audit.db",
    ):
        self.store = SchemaHashStore(lockfile_path)
        self.audit_db_path = Path(audit_db_path)

    @staticmethod
    def extract_tool_schemas(tools_list_response: Any) -> dict[str, Mapping[str, Any]]:
        """Extract {tool_name: schema} from MCP tools/list response."""
        if isinstance(tools_list_response, Mapping):
            tools = tools_list_response.get("tools", [])
        else:
            tools = tools_list_response

        if not isinstance(tools, list):
            raise ValueError("MCP tools/list response must contain a tools list")

        result: dict[str, Mapping[str, Any]] = {}
        for tool in tools:
            if not isinstance(tool, Mapping):
                continue
            name = tool.get("name")
            if not name:
                continue
            schema = tool.get("inputSchema") or tool.get("input_schema") or tool.get("schema") or {}
            if not isinstance(schema, Mapping):
                schema = {}
            # Include selected metadata that can affect tool semantics, not only inputSchema.
            canonical_payload: dict[str, Any] = {
                "name": name,
                "description": tool.get("description", ""),
                "inputSchema": dict(schema),
            }
            result[str(name)] = canonical_payload
        return result

    def record_schema(self, server_id: str, tool_name: str, schema: Mapping[str, Any]) -> ToolSchemaPin:
        """Pin or update a tool schema hash explicitly."""
        schema_hash = compute_schema_hash(schema)
        return self.store.set_hash(server_id, tool_name, schema_hash)

    def verify_schema(self, server_id: str, tool_name: str, schema: Mapping[str, Any]) -> ToolSchemaValidationResult:
        """
        Verify schema against pinned hash.

        First-seen schemas are pinned and reported as ``pinned``. Changed schemas
        are audited and rejected by raising MCPSchemaChangedError.
        """
        new_hash = compute_schema_hash(schema)
        old_hash = self.store.get_hash(server_id, tool_name)
        if old_hash is None:
            self.store.set_hash(server_id, tool_name, new_hash)
            return ToolSchemaValidationResult(server_id, tool_name, new_hash, "pinned")

        if old_hash != new_hash:
            self._record_schema_change(server_id, tool_name, old_hash, new_hash)
            raise MCPSchemaChangedError(
                server_id,
                old_hash,
                new_hash,
                tool_name=tool_name,
            )

        return ToolSchemaValidationResult(server_id, tool_name, new_hash, "unchanged")

    def verify_tools_list(self, server_id: str, tools_list_response: Any) -> list[ToolSchemaValidationResult]:
        """Verify every tool schema in a tools/list response."""
        schemas = self.extract_tool_schemas(tools_list_response)
        return [self.verify_schema(server_id, tool_name, schema) for tool_name, schema in schemas.items()]

    def _ensure_audit_table(self) -> None:
        self.audit_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mcp_schema_changes (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    old_hash TEXT,
                    new_hash TEXT NOT NULL,
                    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
                    approved_by TEXT,
                    approved_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_schema_changes_server ON mcp_schema_changes(server_id)")
            conn.commit()

    def _record_schema_change(self, server_id: str, tool_name: str, old_hash: str, new_hash: str) -> None:
        self._ensure_audit_table()
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute(
                """
                INSERT INTO mcp_schema_changes
                    (id, server_id, tool_name, old_hash, new_hash, detected_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    server_id,
                    tool_name,
                    old_hash,
                    new_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()


__all__ = [
    "MCPToolSchemaValidator",
    "SchemaHashStore",
    "ToolSchemaPin",
    "ToolSchemaValidationResult",
    "canonicalize_schema",
    "compute_schema_hash",
]
