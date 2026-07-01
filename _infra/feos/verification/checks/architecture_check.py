# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationCheckResult


class ArchitectureCheck:
    check_id = "architecture"
    fatal = False

    def run(self, parsed: ParsedResponse, context=None):
        risky = any("新框架" in rec.text or "新数据库" in rec.text for rec in parsed.recommendations)
        return VerificationCheckResult(check_id=self.check_id, status="warning" if risky else "passed", summary="architecture change requires ADR" if risky else "architecture ok")
