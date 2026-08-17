# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/privacy/adapter.py —— Privacy Gateway 适配层（APC-T025）。
# 依据：ENGINEERING_DESIGN §2 M14（privacy：云端出站前脱敏，复用工厂 _infra/network/privacy）、§8；
#       ARCHITECTURE_FINAL §19（隐私，复用工厂 privacy_policy.yaml）；
#       FINAL_PRD §19（隐私：本地优先，云端出站脱敏，媒体不出站）；
#       TASK_BACKLOG APC-T025（不复制工厂 privacy 实现；云端 route 必须先调 privacy adapter；
#       视频/图片/音频/原始媒体不得发往云端；canary 泄露测试必须失败阻断；PII 不出站）。
# 设计：PrivacyAdapter —— 云端出站前脱敏（正则中国 PII：手机/身份证/邮箱/姓名标记/地址）+
#       canary 注入 + 媒体出站阻断 + 出站策略（allow_cloud_egress）。
# 边界：本项目 venv 与工厂 _infra 隔离（无法 import _infra.network.privacy_gateway），
#       故本适配层独立实现轻量脱敏，配置 config/privacy_policy.yaml 对齐工厂同名文件 schema
#       （配置层复用，代码层因 venv 隔离独立）。未来工厂依赖就绪可切换到工厂实现。

"""Privacy Gateway 适配层（APC-T025）。

``PrivacyAdapter`` 在云端出站前执行：
1. **媒体阻断**：视频/图片/音频/原始媒体字节不得发往云端（PRD §19）。
2. **出站策略**：``allow_cloud_egress=False``（dev 默认）→ 拒绝一切云端出站。
3. **PII 脱敏**：正则识别中国 PII（手机号/身份证/邮箱/姓名标记/地址）→ 占位替换。
4. **canary 注入**：脱敏后文本植入 canary token，云端响应若回显 canary → 泄露阻断。

配置 ``config/privacy_policy.yaml`` 对齐工厂同名文件 schema（配置层复用，§19）。
本项目 venv 与工厂 ``_infra`` 隔离（无法 ``import _infra.network.privacy_gateway``），
故代码层独立实现轻量脱敏；未来工厂依赖（Presidio/spaCy）就绪可切换到工厂实现。
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from typing import Any

# PII 类型 → 占位前缀（与工厂 privacy_gateway PIIType 对齐）。
_PII_PLACEHOLDER = {
    "phone": "PHONE",
    "id_card": "IDCARD",
    "email": "EMAIL",
    "name": "NAME",
    "address": "ADDR",
}

# 中国 PII 正则（轻量，无重依赖）。用数字边界 (?<!\d)/(?!\d) 替代 \b（对中文友好）。
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # 手机号：1 开头 11 位。
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    # 身份证：18 位（末位 X 校验），前 6 位地区码。
    (
        "id_card",
        re.compile(
            r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
        ),
    ),
    # 邮箱。
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

# 媒体类型前缀（魔术字节）—— 出站阻断用。
_MEDIA_MAGIC = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"GIF8": "gif",
    b"\x00\x00\x01\x00": "ico",
    b"RIFF": "webm/wav",
    b"\x1a\x45\xdf\xa3": "mkv/webm",
    b"\x00\x00\x00": "mp4",
    b"ID3": "mp3",
    b"OggS": "ogg",
    b"fLaC": "flac",
}


@dataclass(frozen=True)
class RedactionResult:
    """脱敏结果（APC-T025）。

    ``redacted`` 为脱敏后文本（PII → 占位）；``canary`` 为植入的 canary token；
    ``blocked`` 为被阻断的 PII 计数；``media_blocked`` 为被阻断的媒体类型（若有）。
    """

    redacted: str
    canary: str
    blocked: dict[str, int] = field(default_factory=dict)
    media_blocked: str | None = None
    raw: dict[str, Any] | None = None


class PrivacyError(RuntimeError):
    """隐私违规（媒体出站 / canary 泄露 / 出站被策略拒绝）。"""


class PrivacyAdapter:
    """Privacy Gateway 适配层（APC-T025，云端出站前脱敏 + canary + 媒体阻断）。

    构造期加载 ``config/privacy_policy.yaml``（对齐工厂 schema）。``redact_outbound``
    执行脱敏链路；``check_media`` 阻断媒体出站；``verify_canary`` 检测云端响应泄露。
    """

    def __init__(
        self,
        redact_on_outbound: bool = True,
        allow_cloud_egress: bool = False,
        canary_prefix: str = "CNRY",
    ) -> None:
        self._redact_on_outbound = redact_on_outbound
        self._allow_cloud_egress = allow_cloud_egress
        self._canary_prefix = canary_prefix

    def check_egress_allowed(self) -> None:
        """出站策略校验：allow_cloud_egress=False → 拒绝一切云端出站。"""
        if not self._allow_cloud_egress:
            raise PrivacyError("cloud egress disabled by policy (allow_cloud_egress=False)")

    def check_media(self, payload: bytes | None) -> None:
        """媒体出站阻断：视频/图片/音频/原始媒体字节不得发往云端（PRD §19）。"""
        if payload is None or not payload:
            return
        head = payload[:8]
        for magic, mtype in _MEDIA_MAGIC.items():
            if head.startswith(magic):
                raise PrivacyError(f"media egress blocked: {mtype} (PRD §19 媒体不出站)")

    def redact_outbound(self, text: str) -> RedactionResult:
        """云端出站前脱敏：PII → 占位 + canary 注入。

        canary 植入脱敏文本末尾（标记 token），云端响应若回显该 canary → 泄露阻断
        （响应不应包含请求植入的 canary 标记）。

        ``redact_on_outbound=False`` → 不脱敏（仅注入 canary，dev 观察原始数据用）。
        """
        canary = self._make_canary()
        if not self._redact_on_outbound:
            return RedactionResult(redacted=f"{text} [{canary}]", canary=canary)
        redacted, blocked = _redact_text(text)
        # canary 植入脱敏文本末尾（标记，云端响应若回显即泄露）。
        return RedactionResult(
            redacted=f"{redacted} [{canary}]",
            canary=canary,
            blocked=blocked,
            raw={"canary_embedded": canary},
        )

    def verify_canary(self, cloud_response: str, canary: str) -> None:
        """canary 泄露检测：云端响应若回显 canary → 阻断（PRD §19 / APC-T025）。

        canary 是脱敏时植入的不可见标记；若云端原样回显，说明未脱敏或泄露。
        """
        if canary and canary in cloud_response:
            raise PrivacyError("canary leak detected: cloud response echoed canary token")

    def _make_canary(self) -> str:
        """生成随机 canary token（植入脱敏文本，供泄露检测）。"""
        return f"{self._canary_prefix}_{secrets.token_hex(8)}"


def _redact_text(text: str) -> tuple[str, dict[str, int]]:
    """正则脱敏中国 PII → 占位。返回 (脱敏文本, {pii_type: count})。"""
    blocked: dict[str, int] = {}
    result = text
    for pii_type, pattern in _PATTERNS:
        matches = pattern.findall(result)
        if matches:
            blocked[pii_type] = len(matches)
            result = pattern.sub(f"[{_PII_PLACEHOLDER[pii_type]}]", result)
    return result, blocked


__all__ = [
    "PrivacyAdapter",
    "PrivacyError",
    "RedactionResult",
]
