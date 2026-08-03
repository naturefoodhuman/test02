# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 11:05:00

"""Rule review packet tests for APC-T022/T023 production-review handoff."""

from __future__ import annotations

from pathlib import Path

from server.app.rule_engine.review_packet import build_rule_review_packet, write_rule_review_packet


def test_rule_review_packet_contains_hashes_blockers_and_golden_results() -> None:
    packet = build_rule_review_packet(Path("."))

    domains = {pack.domain for pack in packet.pack_summaries}
    assert {"vaccine", "growth", "medication", "triage", "thresholds"}.issubset(domains)
    assert packet.review_status == "pending_human_review"
    assert any("official CN immunization" in blocker for blocker in packet.blockers)
    assert any("full WHO LMS" in blocker for blocker in packet.blockers)
    assert all(len(pack.hash) == 64 for pack in packet.pack_summaries)
    assert packet.golden_cases
    assert all(case.passed for case in packet.golden_cases)
    assert any(case.domain == "vaccine" for case in packet.golden_cases)
    assert any(case.domain == "growth" for case in packet.golden_cases)


def test_rule_review_packet_writes_json_and_markdown(tmp_path: Path) -> None:
    packet = build_rule_review_packet(Path("."))
    json_path, md_path = write_rule_review_packet(packet, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    markdown = md_path.read_text(encoding="utf-8")
    assert "Rule Review Packet" in markdown
    assert "pending_human_review" in markdown
    assert "Requires human review: `true`" in markdown
