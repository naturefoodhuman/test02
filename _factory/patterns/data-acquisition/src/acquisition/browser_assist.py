# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:40:00 CST
"""FB-6 L2：浏览器辅助取数（人在环 human-in-the-loop）。

理念（落实老板硬约束：账号安全 > 数据、不暴力绕过）：
- 用 browser-use（接 GLM via LiteLLM 网关）打开官方查询页、自动填查询词；
- **遇验证码 / 登录 / 风控 → 暂停，把控制权交还给人**，由老板手动完成；
- 人工完成后继续抓取结果，结构化归档。
- 全程 headless=False（显示真实浏览器窗口），便于人工随时接管。

沙箱无 browser-use → 本模块优雅降级：返回"需真机+需装库"的明确指引，不报死。
真机：pip install browser-use playwright && playwright install chromium
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from acquisition.models import QueryResult
from acquisition.sources_registry import OfficialSource


def _lib_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@dataclass
class BrowserAssistConfig:
    """L2 浏览器辅助配置。"""

    # 走 LiteLLM 本地网关的 GLM（不直连，复用工厂统一网关）
    llm_base_url: str = "http://localhost:4000/v1"
    llm_model: str = "cloud/glm-primary"
    llm_api_key: str = "sk-forge-local-anytoken"  # LiteLLM 网关用，任意非空
    headless: bool = False          # 必须 False：人工要能看到并接管
    pause_on_captcha: bool = True   # 遇验证码/登录暂停等人工（核心安全约束）
    max_steps: int = 25


def l2_available() -> bool:
    """L2 是否可用（browser-use 已安装）。"""
    return _lib_available("browser_use")


def build_query_instruction(source: OfficialSource, subject_name: str) -> str:
    """为某官方渠道生成给浏览器 Agent 的中文任务指令（含人在环约束）。"""
    return (
        f"打开 {source.base_url} ，查询对象「{subject_name}」的：{', '.join(source.query_for)}。\n"
        f"操作提示：{source.how_to}\n"
        "重要规则（必须遵守）：\n"
        "1. 绝对不要尝试自动破解/绕过任何验证码、滑块或登录；\n"
        "2. 遇到验证码、登录、实名、短信验证时，立即停止操作并明确告诉用户『请手动完成验证/登录，完成后回复继续』；\n"
        "3. 不要输入或猜测任何账号密码；\n"
        "4. 全程使用中文向用户说明你在做什么。\n"
        "查询到结果后，提取关键信息（是否在册、案号、标的金额、执行法院、状态等）并用中文结构化输出。"
    )


def run_l2_query(
    source: OfficialSource,
    subject_name: str,
    config: BrowserAssistConfig | None = None,
) -> QueryResult:
    """用 browser-use 半自动查询某官方渠道（人在环）。

    沙箱/未装库时返回降级 QueryResult（found=False + 指引）。
    真机装库后才真正驱动浏览器。

    Args:
        source: 官方数据源。
        subject_name: 查询对象。
        config: L2 配置。

    Returns:
        QueryResult（真机为实际结果；降级时 summary 含安装指引）。
    """
    cfg = config or BrowserAssistConfig()

    if not l2_available():
        return QueryResult(
            source_key=source.key,
            subject_name=subject_name,
            found=False,
            summary=(
                "L2 浏览器辅助未启用：需真机安装 browser-use。\n"
                "安装：pip install browser-use playwright && playwright install chromium\n"
                "并确保 LiteLLM 网关在 localhost:4000 运行（GLM 驱动）。\n"
                f"届时将自动打开 {source.base_url} 辅助查询「{subject_name}」，遇验证码/登录会暂停等你手动完成。"
            ),
            source_url=source.base_url,
        )

    # ── 真机执行路径（沙箱不会进入这里）──
    try:
        import asyncio

        from browser_use import Agent, Browser  # type: ignore
        from browser_use.llm import ChatOpenAI  # type: ignore

        llm = ChatOpenAI(model=cfg.llm_model, base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)
        browser = Browser(headless=cfg.headless)  # 显示窗口，人工可接管
        instruction = build_query_instruction(source, subject_name)

        async def _run() -> str:
            agent = Agent(task=instruction, llm=llm, browser=browser,
                          use_vision=False, max_steps=cfg.max_steps)
            history = await agent.run()
            return history.final_result() or ""

        text = asyncio.run(_run())
        return QueryResult(
            source_key=source.key,
            subject_name=subject_name,
            found=bool(text),
            summary=text[:500],
            raw_excerpt=text,
            source_url=source.base_url,
        )
    except Exception as e:  # noqa: BLE001
        return QueryResult(
            source_key=source.key,
            subject_name=subject_name,
            found=False,
            summary=f"L2 执行出错：{e}（检查 browser-use/playwright 安装与 LiteLLM 网关）",
            source_url=source.base_url,
        )
