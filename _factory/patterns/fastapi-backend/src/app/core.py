# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""纯业务逻辑层（无 Web 框架依赖，便于独立单测）。

设计理由：把核心逻辑与框架解耦，使单测无需启动 HTTP 服务即可运行——
这让本 Pattern 的核心测试在任何环境（含无 fastapi 的沙箱）都能跑通。
"""
from __future__ import annotations


def build_greeting(name: str | None) -> str:
    """根据姓名生成问候语（面向用户输出强制中文，符合需求 8.3）。

    Args:
        name: 用户姓名；为 None 或空白时使用默认称呼。

    Returns:
        中文问候语字符串。
    """
    # 关键决策：空值归一化为默认称呼，避免下游出现 "你好，None"
    cleaned = (name or "").strip()
    who = cleaned if cleaned else "朋友"
    return f"你好，{who}！欢迎使用 FORGE Factory。"


def health_payload(version: str) -> dict[str, str]:
    """构造健康检查响应体。

    Args:
        version: 应用版本号。

    Returns:
        含状态与版本的字典。
    """
    return {"status": "ok", "version": version}
