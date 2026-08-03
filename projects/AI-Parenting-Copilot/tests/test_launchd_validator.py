# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 23:20:00

"""launchd plist validation tests for APC-T054/T044."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.launchd_validator import validate_launchd_directory, validate_launchd_plist


def test_launchd_plists_are_valid_and_log_to_runtime_logs() -> None:
    results = validate_launchd_directory(Path("deploy/launchd"))

    assert {result.label for result in results} >= {
        "com.parenting.server",
        "com.parenting.fregata",
        "com.parenting.backup",
    }
    assert all(result.ok for result in results), results


def test_launchd_validator_rejects_tmp_logs(tmp_path: Path) -> None:
    bad = tmp_path / "bad.plist"
    bad.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>Label</key><string>com.parenting.bad</string>
  <key>ProgramArguments</key><array><string>/usr/bin/true</string></array>
  <key>StandardOutPath</key><string>/tmp/bad.out</string>
  <key>StandardErrorPath</key><string>/tmp/bad.err</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )

    result = validate_launchd_plist(bad)

    assert result.ok is False
    assert any("must not write to /tmp" in error for error in result.errors)
