# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 16:00:00 CST
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from llm_telemetry.telemetry import LLMEvent, log_event, summarize, track  # noqa: E402


def test_track_writes_event(tmp_path):
    log = tmp_path / "e.jsonl"
    with track("t1", "m1", show_timer=False, log_path=log) as box:
        box["output_chars"] = 10
    assert log.exists()
    assert '"event": "t1"' in log.read_text(encoding="utf-8")


def test_track_records_failure(tmp_path):
    log = tmp_path / "e.jsonl"
    try:
        with track("t2", "m1", show_timer=False, log_path=log):
            raise ValueError("boom")
    except ValueError:
        pass
    s = summarize(log)
    assert s["by_model"]["m1"]["ok"] == 0


def test_summarize_multi(tmp_path):
    log = tmp_path / "e.jsonl"
    for m in ["a", "a", "b"]:
        with track("e", m, show_timer=False, log_path=log):
            pass
    s = summarize(log)
    assert s["total"] == 3
    assert s["by_model"]["a"]["count"] == 2
