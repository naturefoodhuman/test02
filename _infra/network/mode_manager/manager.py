# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:25:00 CST

"""
Mode Manager（FORGE Network 增量）

职责：
- 从 network.yaml 加载三模式（coding / research / private）
- 提供当前模式查询
- 简单策略检查（allowed_servers / denied_servers）

这是联网功能安全模式隔离的基础设施。
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Dict, List, Optional

from ..config_loader import load_network_config
from ..exceptions import ConfigError

ModeName = Literal["coding", "research", "private"]


class ModeManager:
    """三模式管理器"""

    def __init__(self, project_root: Path | None = None):
        cfg = load_network_config(project_root)
        self._profiles = cfg.mode_profiles
        self._current_mode: ModeName = "research"  # 默认 Research 模式

    @property
    def current_mode(self) -> ModeName:
        return self._current_mode

    def set_mode(self, mode: ModeName) -> None:
        if mode not in ("coding", "research", "private"):
            raise ConfigError(f"Invalid mode: {mode}")
        self._current_mode = mode

    def get_allowed_servers(self, mode: Optional[ModeName] = None) -> List[str]:
        m = mode or self._current_mode
        profile = getattr(self._profiles, m, None)
        if not profile:
            return []
        return profile.allowed_servers

    def get_denied_servers(self, mode: Optional[ModeName] = None) -> List[str]:
        m = mode or self._current_mode
        profile = getattr(self._profiles, m, None)
        if not profile:
            return []
        return profile.denied_servers

    def is_server_allowed(self, server: str, mode: Optional[ModeName] = None) -> bool:
        m = mode or self._current_mode
        allowed = self.get_allowed_servers(m)
        denied = self.get_denied_servers(m)

        if denied and server in denied:
            return False
        if allowed and server not in allowed:
            return False
        return True

    def get_mode_profile(self, mode: Optional[ModeName] = None) -> Dict:
        m = mode or self._current_mode
        profile = getattr(self._profiles, m, None)
        if not profile:
            return {}
        return {
            "mode": m,
            "allowed_servers": profile.allowed_servers,
            "denied_servers": profile.denied_servers,
        }


def get_mode_manager() -> ModeManager:
    """便捷工厂"""
    return ModeManager()
