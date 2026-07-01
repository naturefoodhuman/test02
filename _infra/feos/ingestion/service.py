# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ExternalResponse, ParsedClaim, ParsedResponse, Recommendation
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.repositories import ResponseRepository
from _infra.feos.storage import sha256_text

from .claim_extractor import extract_claims
from .markdown_parser import parse_markdown_sections
from .recommendation_extractor import extract_recommendations
from .risk_extractor import extract_risks
from .assumption_extractor import extract_assumptions
from .patch_extractor import extract_patches


class ResponseIngestionService:
    def __init__(self, repository: ResponseRepository, id_generator: FEOSIdGenerator | None = None):
        self.repository = repository
        self.ids = id_generator or FEOSIdGenerator()

    def import_text(self, case_id: str, text: str, session_id: str = "manual", provider: str = "clipboard") -> ExternalResponse:
        response = ExternalResponse(id=self.ids.response_id(), case_id=case_id, session_id=session_id, raw_ref="", content_hash=sha256_text(text), provider=provider)
        raw_path = self.repository.put_text(case_id, f"{response.id}_raw", text, ".md")
        response.raw_ref = str(raw_path.relative_to(self.repository.workspace.root))
        self.repository.put_yaml(case_id, response.id, response.to_dict())
        return response

    def parse_response(self, response: ExternalResponse) -> ParsedResponse:
        raw_path = self.repository.workspace.root / response.raw_ref
        text = raw_path.read_text(encoding="utf-8")
        parsed = parse_markdown_sections(text)
        claims = [ParsedClaim(id=self.ids.next("claim"), text=t) for t in extract_claims(parsed)]
        recs = [Recommendation(id=self.ids.next("rec"), text=t) for t in extract_recommendations(parsed)]
        pr = ParsedResponse(id=self.ids.next("parsed"), case_id=response.case_id, response_id=response.id, claims=claims, recommendations=recs, assumptions=extract_assumptions(parsed), risks=extract_risks(parsed))
        data = pr.to_dict()
        data["patches"] = extract_patches(text)
        data["parse_warnings"] = parsed.get("warnings", [])
        self.repository.put_yaml(response.case_id, f"{response.id}_parsed", data)
        return pr
