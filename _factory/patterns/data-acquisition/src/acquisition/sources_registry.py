# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
"""官方公开数据源注册表（L1 取数层核心）。

设计理由（基于第11/13轮调研事实）：
- 中国执行信息公开网/裁判文书网等官方渠道【需要验证码或登录】，不能暴力全自动直抓
  （会撞验证码 + 触发反爬 + 违反 ToS）。
- 因此 L1 取数层不做"暴力爬虫"，而是做"取数协调器"：
  维护每个官方渠道的【查询方法元数据 + 直达 URL 模板 + 风控等级】，
  生成"待查清单"，由人工/半自动(L2)完成查询，再把结果结构化归档。
- 这样合规、不封号、且真正帮到用户（满足老板"落地成功率优先 + 账号安全"）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AccessMode(str, Enum):
    """取数模式（对应三层方案）。"""

    L1_PUBLIC = "L1_public"        # 公开渠道，可生成直达查询链接（仍可能有验证码→人工过）
    L2_HUMAN_LOOP = "L2_human"     # 半自动：浏览器辅助打开，遇验证码/登录停下等人工
    L3_ACCOUNT = "L3_account"      # 账号自动抓（默认关闭，需逐次授权，本注册表不默认启用）


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class OfficialSource:
    """一个官方数据源的查询元数据。"""

    key: str
    name: str
    base_url: str
    access_mode: AccessMode
    risk: RiskLevel
    needs_captcha: bool            # 是否有图形/行为验证码
    needs_login: bool              # 是否需要登录/实名
    query_for: list[str] = field(default_factory=list)   # 能查什么
    how_to: str = ""               # 人话操作说明
    query_url_tip: str = ""        # 直达/查询入口提示


# ── L1 官方公开数据源注册表（讨债核心，均为低风险公开渠道）──
OFFICIAL_SOURCES: dict[str, OfficialSource] = {
    "zxgk": OfficialSource(
        key="zxgk",
        name="中国执行信息公开网",
        base_url="http://zxgk.court.gov.cn/",
        access_mode=AccessMode.L2_HUMAN_LOOP,   # 有图形验证码→人在环
        risk=RiskLevel.LOW,
        needs_captcha=True,
        needs_login=False,
        query_for=["失信被执行人", "限制高消费", "被执行人信息", "终本案件", "财产处置/司法拍卖"],
        how_to=(
            "打开网站 → 选『失信被执行人』或『综合查询被执行人』→ 输入对方姓名/身份证号 "
            "→ 输入图形验证码 → 查询 → 点『查看』看详情（执行法院、标的金额、执行状态）。"
        ),
        query_url_tip="首页四个入口：失信被执行人 / 限制消费人员 / 被执行人信息 / 综合查询",
    ),
    "wenshu": OfficialSource(
        key="wenshu",
        name="中国裁判文书网",
        base_url="https://wenshu.court.gov.cn/",
        access_mode=AccessMode.L2_HUMAN_LOOP,   # 需注册登录+可能验证码
        risk=RiskLevel.MEDIUM,
        needs_captcha=True,
        needs_login=True,
        query_for=["涉诉历史", "判决文书", "既往纠纷", "文书中披露的财产线索"],
        how_to=(
            "注册登录并实名 → 搜索框输入对方姓名 → 查涉诉案件文书（他告别人/别人告他都能看）。"
            "⚠️ 注意同名辨别，结合身份证号/地域确认。"
        ),
        query_url_tip="需登录后搜索；建议走 L2 人在环，登录与验证码由你手动完成。",
    ),
    "gsxt": OfficialSource(
        key="gsxt",
        name="国家企业信用信息公示系统",
        base_url="https://www.gsxt.gov.cn/",
        access_mode=AccessMode.L2_HUMAN_LOOP,   # 有滑块验证码
        risk=RiskLevel.LOW,
        needs_captcha=True,
        needs_login=False,
        query_for=["工商登记", "股东结构", "对外投资", "经营异常", "行政处罚"],
        how_to=(
            "打开网站 → 输入企业名称/统一社会信用代码 → 过滑块验证 → 查工商信息、股东、对外投资。"
            "若债务人是公司法定代表人/股东，可顺藤摸瓜。"
        ),
        query_url_tip="按企业名称或统一社会信用代码查询。",
    ),
    "flk": OfficialSource(
        key="flk",
        name="国家法律法规数据库",
        base_url="https://flk.npc.gov.cn/",
        access_mode=AccessMode.L1_PUBLIC,       # 纯公开，无验证码
        risk=RiskLevel.LOW,
        needs_captcha=False,
        needs_login=False,
        query_for=["民法典", "民事诉讼法", "诉讼时效", "司法解释"],
        how_to="搜索法条名称/关键词，核对法律条文原文，防止策略报告引用错误法条。",
        query_url_tip="策略报告引用法条时，回溯到这里核对原文。",
    ),
}


def get_source(key: str) -> OfficialSource | None:
    """按 key 取数据源。"""
    return OFFICIAL_SOURCES.get(key)


def list_sources(max_risk: RiskLevel | None = None) -> list[OfficialSource]:
    """列出数据源，可按最大风险过滤。"""
    order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
    out = list(OFFICIAL_SOURCES.values())
    if max_risk is not None:
        out = [s for s in out if order[s.risk] <= order[max_risk]]
    return out
