# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json

from _infra.feos.models import ContextPackage, EscalationPackage


class JSONRenderer:
    renderer_id = "api_json"

    def render(self, package: EscalationPackage, context: ContextPackage) -> str:
        return json.dumps({"package": package.to_dict(), "context": context.to_dict()}, ensure_ascii=False, indent=2)
