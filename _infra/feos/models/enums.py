# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS global enums."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String enum with readable repr / YAML-friendly values."""

    def __str__(self) -> str:
        return self.value


class CaseStatus(StrEnum):
    DRAFT = "Draft"
    CREATED = "Created"
    COLLECTING_EVIDENCE = "CollectingEvidence"
    GRAPH_BUILDING = "GraphBuilding"
    INVESTIGATING = "Investigating"
    POLICY_CHECKING = "PolicyChecking"
    CONTEXT_COMPILING = "ContextCompiling"
    PACKAGE_GENERATED = "PackageGenerated"
    WAITING_HUMAN_EXPORT = "WaitingHumanExport"
    WAITING_EXTERNAL_RESPONSE = "WaitingExternalResponse"
    RESPONSE_IMPORTED = "ResponseImported"
    PARSING_RESPONSE = "ParsingResponse"
    VERIFYING = "Verifying"
    PLANNING_EXECUTION = "PlanningExecution"
    EXECUTING = "Executing"
    EVALUATING_OUTCOME = "EvaluatingOutcome"
    RESOLVED = "Resolved"
    UNRESOLVED = "Unresolved"
    ABANDONED = "Abandoned"
    DISTILLING_KNOWLEDGE = "DistillingKnowledge"
    ARCHIVED = "Archived"


ARCHITECTURE_CASE_STATUSES = [status.value for status in CaseStatus]


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseCategory(StrEnum):
    BUG = "bug"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REFACTOR = "refactor"
    MCP_ISSUE = "mcp_issue"
    UNKNOWN = "unknown"


class EvidenceType(StrEnum):
    STACK_TRACE = "stack_trace"
    FAILING_TEST = "failing_test"
    GIT_DIFF = "git_diff"
    TOOL_CALL_TRACE = "tool_call_trace"
    MCP_CALL_TRACE = "mcp_call_trace"
    CONFIG = "config"
    DEPENDENCY_LOCK = "dependency_lock"
    RUNTIME_ENV = "runtime_env"
    ARCHITECTURE_DOC = "architecture_doc"
    AGENT_PROMPT = "agent_prompt"
    PREVIOUS_ATTEMPT = "previous_attempt"
    USER_INPUT = "user_input"
    LOG = "log"
    CODE = "code"
    OTHER = "other"


class GatewayType(StrEnum):
    CLIPBOARD = "clipboard"
    API = "api"
    MCP = "mcp"
    BROWSER = "browser"
    CLOUD_AGENT = "cloud_agent"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class HypothesisStatus(StrEnum):
    PROPOSED = "Proposed"
    TESTING = "Testing"
    SUPPORTED = "Supported"
    REJECTED = "Rejected"
    CONFIRMED = "Confirmed"


class KnowledgeCandidateStatus(StrEnum):
    CAPTURED = "captured"
    VERIFIED = "verified"
    INDEXED = "indexed"
    RETRIEVED = "retrieved"
    REUSED = "reused"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
