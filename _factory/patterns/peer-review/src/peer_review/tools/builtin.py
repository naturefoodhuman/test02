# 创建时间（北京时间）：2026-07-09 17:05:00
"""内置工具集

提供常用的 Agent 工具：
- file_read: 读取文件内容
- file_write: 写入文件
- shell_exec: 执行 shell 命令 (受限模式)
- list_directory: 列出目录内容
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from peer_review.tools.registry import ToolRegistry


def _file_read(path: str, encoding: str = "utf-8") -> dict:
    """读取文件内容"""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"文件不存在: {p}"}
    if not p.is_file():
        return {"error": f"不是文件: {p}"}
    content = p.read_text(encoding=encoding)
    return {"path": str(p), "size": len(content), "content": content}


def _file_write(path: str, content: str, encoding: str = "utf-8") -> dict:
    """写入文件"""
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    return {"path": str(p), "size": len(content), "status": "written"}


def _shell_exec(command: str, timeout: int = 30, cwd: str | None = None) -> dict:
    """执行 shell 命令 (受限模式)"""
    # 安全黑名单
    dangerous = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if=/dev/zero"]
    for d in dangerous:
        if d in command:
            return {"error": f"命令被安全策略拦截: {d}"}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return {
            "stdout": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout,
            "stderr": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"命令超时 ({timeout}s)"}
    except Exception as e:
        return {"error": str(e)}


def _list_directory(path: str = ".", max_items: int = 50) -> dict:
    """列出目录内容"""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"目录不存在: {p}"}
    if not p.is_dir():
        return {"error": f"不是目录: {p}"}
    items = []
    for i, item in enumerate(sorted(p.iterdir())):
        if i >= max_items:
            items.append(f"... (还有更多，共 {len(list(p.iterdir()))} 项)")
            break
        items.append({
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
        })
    return {"path": str(p), "items": items}


def register_builtins(registry: "ToolRegistry") -> None:
    """注册所有内置工具到 registry"""

    registry.register(
        name="file_read",
        schema={
            "name": "file_read",
            "description": "读取指定路径的文件内容。支持文本文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径 (支持 ~ 展开)"},
                    "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
                },
                "required": ["path"],
            },
        },
        handler=_file_read,
    )

    registry.register(
        name="file_write",
        schema={
            "name": "file_write",
            "description": "将内容写入指定路径的文件。自动创建父目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的文本内容"},
                    "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
                },
                "required": ["path", "content"],
            },
        },
        handler=_file_write,
    )

    registry.register(
        name="shell_exec",
        schema={
            "name": "shell_exec",
            "description": "在本地执行 shell 命令并返回结果。有安全黑名单和时间限制。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 shell 命令"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认 30", "default": 30},
                    "cwd": {"type": "string", "description": "工作目录，默认当前目录"},
                },
                "required": ["command"],
            },
        },
        handler=_shell_exec,
    )

    registry.register(
        name="list_directory",
        schema={
            "name": "list_directory",
            "description": "列出指定目录下的文件和子目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径，默认当前目录", "default": "."},
                    "max_items": {"type": "integer", "description": "最多返回条目数，默认 50", "default": 50},
                },
                "required": [],
            },
        },
        handler=_list_directory,
    )