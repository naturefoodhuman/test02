# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Built-in FEOS evidence collectors."""

from .adr_collector import ADRCollector
from .agent_plan_collector import AgentPlanCollector
from .architecture_collector import ArchitectureCollector
from .code_collector import CodeCollector
from .config_collector import ConfigCollector
from .dependency_collector import DependencyCollector
from .diff_collector import DiffCollector
from .environment_collector import EnvironmentCollector
from .git_collector import GitCollector
from .log_collector import LogCollector
from .previous_attempt_collector import PreviousAttemptCollector
from .runtime_collector import RuntimeCollector
from .stacktrace_collector import StackTraceCollector
from .test_collector import TestCollector
from .user_input_collector import UserInputCollector

__all__ = [
    "ADRCollector", "AgentPlanCollector", "ArchitectureCollector", "CodeCollector",
    "ConfigCollector", "DependencyCollector", "DiffCollector", "EnvironmentCollector",
    "GitCollector", "LogCollector", "PreviousAttemptCollector", "RuntimeCollector",
    "StackTraceCollector", "TestCollector", "UserInputCollector",
]
