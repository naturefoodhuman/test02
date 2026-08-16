# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/registry.py —— RuleRegistry 规则注册与调度（APC-T018）。
# 依据：ENGINEERING_DESIGN §5.3、§13.2（新增 config/rules/<domain>/<pack>.yaml + Registry.register）；
#       TASK_BACKLOG APC-T018（RuleRegistry 能按 domain 调用 RuleModule）。
# 设计：RuleRegistry 按 domain 注册 RuleModule；evaluate(domain, input, ctx) 调对应模块。
#       插件化：新增规则域 = 实现 RuleModule + register，不改内核（开闭原则）。
# 边界：Registry 只调度，不实现规则（规则在 RuleModule）；未注册 domain 抛 KeyError。

"""RuleRegistry 规则注册与调度（APC-T018）。

架构（ENGINEERING_DESIGN §5.3 / §13.2）：``RuleRegistry`` 按 ``domain`` 注册
``RuleModule``；``evaluate(domain, input, ctx)`` 调对应模块。插件化——新增规则域
= 实现 ``RuleModule`` + ``register``，不改内核（开闭原则）。
"""

from __future__ import annotations

from .domain.models import RuleContext, RuleDomain, RuleInput, RuleModule, RuleResult


class RuleRegistry:
    """规则注册表（按 domain 注册/调用 RuleModule，APC-T018）。

    线程安全：单例注册在启动期完成（main 装配），运行期只读。测试可 new 独立实例。
    """

    def __init__(self) -> None:
        self._modules: dict[str, RuleModule] = {}

    def register(self, module: RuleModule) -> None:
        """注册 RuleModule（按 module.domain 索引）。重复注册覆盖（便于测试）。"""
        self._modules[module.domain] = module

    def get(self, domain: str) -> RuleModule:
        """取已注册 RuleModule；未注册抛 KeyError。"""
        try:
            return self._modules[domain]
        except KeyError as exc:
            raise KeyError(f"no RuleModule registered for domain={domain}") from exc

    def domains(self) -> list[str]:
        """已注册 domain 列表。"""
        return sorted(self._modules.keys())

    async def evaluate(self, domain: RuleDomain, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """按 domain 调用 RuleModule.evaluate（架构 §5.3）。"""
        module = self.get(domain)
        return await module.evaluate(input_, ctx)


__all__ = ["RuleRegistry"]
