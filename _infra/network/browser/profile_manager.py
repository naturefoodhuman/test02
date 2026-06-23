# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:16:58

"""Browser profile manager (E7-C3-S1-T1).

Manages AI-Public / AI-Private profile metadata and local directory creation.
It reads browser profile definitions from config/network.yaml but also supports
explicit root override for tests and local workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Mapping

from _infra.network.config_loader import load_network_config
from _infra.network.config_loader.schemas import NetworkConfig, ProfileConfig


@dataclass(frozen=True)
class BrowserProfile:
    name: str
    user_data_dir: Path
    blocked_origins: list[str] = field(default_factory=list)
    allowed_domains: list[str] = field(default_factory=list)
    remote_debugging_port: int | None = None


class ProfileManager:
    """Load and materialize browser profiles."""

    def __init__(self, config: NetworkConfig | None = None, profile_root: str | Path | None = None):
        self.config = config or load_network_config()
        self.profile_root = Path(profile_root) if profile_root is not None else None

    @staticmethod
    def _expand_path(path: str) -> Path:
        return Path(os.path.expandvars(os.path.expanduser(path)))

    def _profile_to_dataclass(self, name: str, cfg: ProfileConfig) -> BrowserProfile:
        user_data_dir = self._expand_path(cfg.user_data_dir)
        if self.profile_root is not None:
            user_data_dir = self.profile_root / name.replace("_", "-")
        return BrowserProfile(
            name=name,
            user_data_dir=user_data_dir,
            blocked_origins=list(cfg.blocked_origins),
            allowed_domains=list(cfg.allowed_domains),
            remote_debugging_port=cfg.remote_debugging_port,
        )

    def list_profiles(self) -> list[str]:
        return sorted(self.config.browser.profiles.keys())

    def get_profile(self, name: str) -> BrowserProfile:
        profiles = self.config.browser.profiles
        if name not in profiles:
            raise KeyError(f"Unknown browser profile: {name}")
        return self._profile_to_dataclass(name, profiles[name])

    def ensure_profile_dir(self, name: str) -> Path:
        profile = self.get_profile(name)
        profile.user_data_dir.mkdir(parents=True, exist_ok=True)
        return profile.user_data_dir

    def ensure_all_profile_dirs(self) -> Mapping[str, Path]:
        return {name: self.ensure_profile_dir(name) for name in self.list_profiles()}


__all__ = ["BrowserProfile", "ProfileManager"]
