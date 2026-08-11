# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
"""Alembic 迁移框架配置校验（APC-T003，不连 DB）。

验证 alembic.ini 可解析、env.py 可 import、script_location 与 versions 目录就位。
不执行真实迁移（无 DB 环境）。
"""

from __future__ import annotations

import ast
from pathlib import Path

from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_alembic_ini_exists_and_parseable():
    """alembic.ini 存在且 alembic 可解析。"""
    ini = PROJECT_ROOT / "alembic.ini"
    assert ini.exists(), "alembic.ini missing"
    cfg = Config(str(ini))
    assert cfg.get_main_option("script_location") == "server/migrations"


def test_migrations_env_syntax_valid():
    """migrations/env.py 语法可解析（不实际 import，避免触发 alembic context）。

    env.py 由 alembic CLI 注入 context 后执行；直接 import 会因无 context 抛错，
    故此处仅做 AST 语法校验，并断言关键符号存在。
    """
    env = PROJECT_ROOT / "server" / "migrations" / "env.py"
    assert env.exists(), "migrations/env.py missing"
    tree = ast.parse(env.read_text(encoding="utf-8"))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    funcs = {
        n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "run_migrations_offline" in funcs
    assert "run_migrations_online" in funcs
    assert "get_settings" in names
    assert "target_metadata" in names


def test_versions_dir_exists():
    """versions 目录存在（迁移文件存放点）。"""
    versions = PROJECT_ROOT / "server" / "migrations" / "versions"
    assert versions.is_dir()


def test_docker_compose_services_declared():
    """docker-compose.yml 声明 postgres/mosquitto/powersync 三服务（APC-T003 验收）。"""
    compose = PROJECT_ROOT / "deploy" / "docker-compose.yml"
    assert compose.exists(), "docker-compose.yml missing"
    text = compose.read_text(encoding="utf-8")
    for svc in ("postgres:", "mosquitto:", "powersync:"):
        assert svc in text, f"service {svc} missing in compose"


def test_mosquitto_config_exists():
    """mosquitto.conf 存在且监听 1883。"""
    conf = PROJECT_ROOT / "deploy" / "mosquitto" / "mosquitto.conf"
    assert conf.exists(), "mosquitto.conf missing"
    text = conf.read_text(encoding="utf-8")
    assert "listener 1883" in text


def test_powersync_config_exists():
    """PowerSync config 与 sync-rules 占位存在。"""
    for p in ("config/powersync/config.yaml", "config/powersync/sync-rules.yaml"):
        assert (PROJECT_ROOT / p).exists(), f"{p} missing"
