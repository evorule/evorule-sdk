# SPDX-License-Identifier: AGPL-3.0-or-later
"""evorule Python SDK

evorule-server 的 HTTP API 薄封装，提供会话管理、命令提交和 SSE 事件流订阅。

安装：
    pip install evorule

使用示例：
    import asyncio
    from evorule import EvoruleClient

    async def main():
        async with EvoruleClient("http://localhost:18080") as client:
            async with await client.create_session() as session:
                await session.command({"type": "increment", "params": {"attr": "x", "delta": 5}})
                state = await session.state()
                print(state)

    asyncio.run(main())
"""

from .client import EvoruleClient
from .events import Event
from .exceptions import (
    AuthenticationError,
    CommandError,
    EvoruleConnectionError,
    EvoruleError,
    SessionClosedError,
    SessionNotFoundError,
)
from .session import Session
from .types import (
    AuditVerifyResponse,
    ApiResponse,
    ClientOptions,
    ClusterStatusResponse,
    DebugPendingIoResponse,
    DebugPhaseResponse,
    DebugQueueResponse,
    DiffChangedEntry,
    DiffEntry,
    DiffResponse,
    EventData,
    EventType,
    ForkSessionResponse,
    HistoryEntry,
    Instruction,
    Json,
    PendingIoInfo,
    ReplayResponse,
    RewindResponse,
    SessionFactEntry,
    SessionState,
    SharedFact,
    SharedFactSourceResponse,
    SharedFactUsedByResponse,
    SyncDirection,
    UsedAtStartupResponse,
)

__version__ = "6.0.0"

__all__ = [
    "EvoruleClient",
    "Session",
    "Event",
    "EvoruleError",
    "AuthenticationError",
    "SessionNotFoundError",
    "SessionClosedError",
    "CommandError",
    "EvoruleConnectionError",
    "Json",
    "EventType",
    "SyncDirection",
    "Instruction",
    "ApiResponse",
    "SessionState",
    "ForkSessionResponse",
    "EventData",
    "ReplayResponse",
    "RewindResponse",
    "DiffResponse",
    "DiffEntry",
    "DiffChangedEntry",
    "SharedFact",
    "SharedFactSourceResponse",
    "SharedFactUsedByResponse",
    "PendingIoInfo",
    "DebugPhaseResponse",
    "DebugQueueResponse",
    "DebugPendingIoResponse",
    "AuditVerifyResponse",
    "HistoryEntry",
    "SessionFactEntry",
    "UsedAtStartupResponse",
    "ClusterStatusResponse",
    "ClientOptions",
    "__version__",
]
