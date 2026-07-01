# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json

from _infra.feos import cli


def test_cli_create_status_list_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FEOS_HOME", str(tmp_path / "feos"))
    code = cli.main(["create", "--title", "T", "--user-goal", "debug", "--json"])
    assert code == 0
    created = json.loads(capsys.readouterr().out)
    case_id = created["id"]

    assert cli.main(["status", case_id, "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["status"] == "Created"

    assert cli.main(["list", "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["id"] == case_id
