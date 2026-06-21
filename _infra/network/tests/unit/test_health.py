# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:22:00 CST

"""单元测试：Health Checker"""

from _infra.network.health_check.checker import check_health, HealthReport


def test_check_health_runs():
    report = check_health()
    assert isinstance(report, HealthReport)
    assert report.status in ("healthy", "degraded", "unhealthy")
    assert "config" in report.checks


def test_print_health(capsys):
    from _infra.network.health_check.checker import print_health_report
    report = check_health()
    print_health_report(report)
    captured = capsys.readouterr()
    assert "Network Health" in captured.out
