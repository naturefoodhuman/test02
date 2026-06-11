# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
"""取数层数据模型：查询目标、查询任务、查询结果。"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import json


class SubjectType(str, Enum):
    """查询对象类型。"""

    PERSON = "person"      # 自然人
    COMPANY = "company"    # 企业


@dataclass
class Subject:
    """查询对象（债务人）。"""

    name: str
    subject_type: SubjectType = SubjectType.PERSON
    id_number: str = ""       # 身份证号/统一社会信用代码（脱敏存储，敏感）
    aliases: list[str] = field(default_factory=list)
    region: str = ""          # 地域，辅助同名辨别
    note: str = ""


@dataclass
class QueryTask:
    """一条待查任务（取数清单的一项）。"""

    source_key: str
    source_name: str
    base_url: str
    access_mode: str
    risk: str
    query_for: list[str]
    how_to: str
    needs_captcha: bool
    needs_login: bool
    status: str = "TODO"      # TODO / DONE / SKIPPED
    note: str = ""


@dataclass
class QueryResult:
    """一条查询结果（人工/半自动取回后结构化归档）。"""

    source_key: str
    subject_name: str
    found: bool                       # 是否查到记录
    summary: str = ""                 # 关键发现摘要
    raw_excerpt: str = ""             # 原文摘录（证据）
    fields: dict[str, Any] = field(default_factory=dict)  # 结构化字段
    captured_at: str = ""
    source_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryPlan:
    """针对某个 Subject 的完整取数计划。"""

    subject: Subject
    tasks: list[QueryTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["subject"]["subject_type"] = self.subject.subject_type.value
        return d

    def to_json(self, *, ensure_ascii: bool = False, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

    def to_checklist_md(self) -> str:
        """渲染成人话的『待查清单』Markdown。"""
        s = self.subject
        lines = [
            f"# 取数待查清单：{s.name}",
            "",
            f"- 对象类型：{'企业' if s.subject_type == SubjectType.COMPANY else '自然人'}",
            f"- 地域（辅助辨别同名）：{s.region or '（未填）'}",
            "",
            "> ⚠️ 合规与账号安全：以下均为官方公开渠道。遇验证码/登录请**你手动完成**，",
            "> 系统不暴力绕过、不替你登录第三方账号（保护账号安全、符合 ToS）。",
            "",
        ]
        for i, t in enumerate(self.tasks, 1):
            flags = []
            if t.needs_captcha:
                flags.append("需验证码")
            if t.needs_login:
                flags.append("需登录")
            flag_str = f"（{'/'.join(flags)}）" if flags else ""
            lines += [
                f"## {i}. {t.source_name} {flag_str}",
                f"- 入口：{t.base_url}",
                f"- 能查：{', '.join(t.query_for)}",
                f"- 怎么查：{t.how_to}",
                f"- 风险：{t.risk}  ·  取数模式：{t.access_mode}",
                f"- 状态：{t.status}",
                "",
            ]
        return "\n".join(lines)
