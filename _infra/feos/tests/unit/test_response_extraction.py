# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.ingestion import ResponseIngestionService
from _infra.feos.repositories import ResponseRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml


def test_response_parse_extracts_claim_recommendation_risk_assumption_and_patch(tmp_path):
    text = """## Claims
Root cause is schema mismatch
## Recommendations
- Add result field
## Risks
- May break old callers
## Assumptions
- schema version is current
```diff
+ result: ok
```
"""
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    service = ResponseIngestionService(ResponseRepository(ws))
    response = service.import_text("case", text)
    parsed = service.parse_response(response)
    assert parsed.claims[0].text == "Root cause is schema mismatch"
    assert parsed.recommendations[0].text == "Add result field"
    saved = read_yaml(ws.root / "cases" / "case" / "response" / f"{response.id}_parsed.yaml")
    assert saved["risks"] == ["May break old callers"]
    assert saved["assumptions"] == ["schema version is current"]
    assert saved["patches"] == ["+ result: ok"]
