# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import re

from _infra.feos.ports.policy import PrivacyDetection, RedactionResult

SECRET_PATTERNS = [
    ("api_key", re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9_\-]{8,})")),
    ("secret", re.compile(r"(?i)(secret\s*[=:]\s*)([^\s]+)")),
    ("token", re.compile(r"(?i)(token\s*[=:]\s*)([^\s]+)")),
    ("password", re.compile(r"(?i)(password\s*[=:]\s*)([^\s]+)")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
]


class RegexRedactor:
    def redact(self, text: str) -> RedactionResult:
        if "AI_CANARY_DO_NOT_LEAK" in text:
            return RedactionResult(blocked=True, text="", reason="canary token detected")  # type: ignore[call-arg]
        detections = []
        replacements = {}
        redacted = text
        idx = 1
        for kind, pattern in SECRET_PATTERNS:
            def repl(match):
                nonlocal idx
                placeholder = f"<<{kind.upper()}_{idx}>>"
                idx += 1
                detections.append(PrivacyDetection(type=kind, value_preview=match.group(0)[:24]))
                replacements[placeholder] = match.group(0)
                if match.lastindex and match.lastindex >= 2:
                    return match.group(1) + placeholder
                return placeholder
            redacted = pattern.sub(repl, redacted)
        return RedactionResult(blocked=False, text=redacted, detections=detections, replacements=replacements)
