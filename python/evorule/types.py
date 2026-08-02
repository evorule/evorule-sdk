# SPDX-License-Identifier: AGPL-3.0-or-later
"""evorule SDK 类型定义

使用 TypedDict 和 TypeAlias 定义所有公开 API 的数据结构，
供类型检查器（mypy / pyright）和 IDE 自动补全使用。

注意：这些是类型提示，不做运行时校验。实际返回值是普通 dict。
"""

from __future__ import annotations

from typing import Any, Literal, TypeAlias, TypedDict

# ======================================================================
# 基础类型
# ======================================================================

#: 通用 JSON 值类型
Json: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | list["Json"]
    | dict[str, "Json"]
)

#: 事件类型
EventType: TypeAlias = Literal[
    "Command",
    "StateTransition",
    "IoRequest",
    "IoResponse",
    "Stable",
    "PayloadUpdate",
    "Error",
]

#: 集群同步方向
SyncDirection: TypeAlias = Literal["atob", "btoa", "bidirectional"]


# ======================================================================
# 指令 / 响应
# ======================================================================


class Instruction(TypedDict, total=False):
    """业务规则指令

    必须字段：type
    可选字段：params 及其他自定义字段
    """

    type: str
    params: dict[str, Json]


class ApiResponse(TypedDict):
    """通用 API 响应"""

    success: bool
    message: str
    fact_id: int | None


# ======================================================================
# 会话相关
# ======================================================================


class SessionState(TypedDict):
    """会话状态快照"""

    payload: dict[str, Json]
    queue: list[Json]
    version: int


class CreateSessionResponse(TypedDict):
    """创建会话响应"""

    session_id: int
    message: str


class ListSessionsResponse(TypedDict):
    """列出会话响应"""

    sessions: list[int]


class ForkSessionResponse(TypedDict):
    """分叉会话响应"""

    session_id: int
    parent_session_id: int
    forked_from_version: int
    message: str


# ======================================================================
# 时间机器
# ======================================================================


class EventData(TypedDict, total=False):
    """SSE 事件原始 JSON"""

    type: EventType
    id: int
    cause: int
    instruction: Json
    new_payload: dict[str, Json]
    new_queue: list[Json]
    final_snapshot: dict[str, Json]
    io_type: str
    params: dict[str, Json]
    request_id: int
    result: Json
    error: str
    path: str
    value: Json
    message: str


class ReplayResponse(TypedDict):
    """回放响应（Fact 列表）"""

    facts: list[EventData]


class RewindResponse(TypedDict):
    """回滚响应（回滚后的状态快照）"""

    version: int
    payload: dict[str, Json]
    queue: list[Json]


class DiffEntry(TypedDict):
    """Diff 响应中 added/removed 项"""

    key: str
    value: Json


class DiffChangedEntry(TypedDict):
    """Diff 响应中 changed 项"""

    key: str
    old_value: Json
    new_value: Json


class DiffResponse(TypedDict):
    """Diff 响应（两个版本的 payload 对比）"""

    version_a: int
    version_b: int
    added: list[DiffEntry]
    removed: list[DiffEntry]
    changed: list[DiffChangedEntry]


# ======================================================================
# 共享 Fact
# ======================================================================


class SharedFact(TypedDict):
    """共享 Fact"""

    fact_id: int
    path: str
    value: Json
    source_session_id: int
    version: int


class SharedFactSourceResponse(TypedDict):
    """shared_fact_source 响应"""

    fact_id: int
    path: str
    value: Json
    source_session_id: int
    version: int


class SharedFactUsedByResponse(TypedDict):
    """shared_fact_used_by 响应"""

    fact_id: int
    sessions: list[int]


# ======================================================================
# 调试 / 审计
# ======================================================================


class PendingIoInfo(TypedDict):
    """挂起的 I/O 请求信息"""

    fact_id: int
    io_type: str
    duration_ms: int


class DebugPhaseResponse(TypedDict):
    """debug/phase 响应"""

    phase: str


class DebugQueueResponse(TypedDict):
    """debug/queue 响应"""

    queue: list[Json]


class DebugPendingIoResponse(TypedDict):
    """debug/pending_io 响应"""

    pending_io: list[PendingIoInfo]


class AuditVerifyResponse(TypedDict):
    """audit/verify 响应"""

    valid: bool
    session_id: int


# ======================================================================
# 历史 / 集群
# ======================================================================


class HistoryEntry(TypedDict):
    """history 单项"""

    version: int
    type: str


class SessionFactEntry(TypedDict):
    """会话内 Fact 单项（按前缀查询）"""

    fact_id: int
    version: int
    path: str
    value: Json


class UsedAtStartupResponse(TypedDict):
    """GET used_at_startup 响应"""

    session_id: int
    fact_ids: list[int]


class ClusterStatusResponse(TypedDict):
    """cluster_status 响应"""

    session_id: int
    cluster_members: list[int]


# ======================================================================
# 客户端配置
# ======================================================================


class ClientOptions(TypedDict, total=False):
    """客户端配置

    可选字段：
    - token: Bearer 认证 token
    - timeout: 请求超时（秒），默认 30
    """

    token: str
    timeout: float
