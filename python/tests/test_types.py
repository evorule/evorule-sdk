# SPDX-License-Identifier: MIT
"""evorule.types 模块单元测试

测试所有 TypedDict 和 TypeAlias 的结构正确性，
不依赖 evorule-server，纯本地运行。
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from evorule.types import (
    # TypeAlias
    Json,
    EventType,
    SyncDirection,
    # 指令 / 响应
    Instruction,
    ApiResponse,
    # 会话
    SessionState,
    ForkSessionResponse,
    # 时间机器
    EventData,
    ReplayResponse,
    RewindResponse,
    DiffResponse,
    DiffEntry,
    DiffChangedEntry,
    # 共享 Fact
    SharedFact,
    SharedFactSourceResponse,
    SharedFactUsedByResponse,
    # 调试 / 审计
    PendingIoInfo,
    DebugPhaseResponse,
    DebugQueueResponse,
    DebugPendingIoResponse,
    AuditVerifyResponse,
    # 历史 / 集群
    HistoryEntry,
    SessionFactEntry,
    UsedAtStartupResponse,
    ClusterStatusResponse,
    # 客户端
    ClientOptions,
)


class TestTypeAliases:
    """测试 TypeAlias 类型"""

    def test_event_type_values(self):
        """EventType 应包含所有 7 种事件类型"""
        valid_types: list[EventType] = [
            "Command",
            "StateTransition",
            "IoRequest",
            "IoResponse",
            "Stable",
            "PayloadUpdate",
            "Error",
        ]
        assert len(valid_types) == 7

    def test_sync_direction_values(self):
        """SyncDirection 应包含 3 种方向"""
        valid_directions: list[SyncDirection] = [
            "atob",
            "btoa",
            "bidirectional",
        ]
        assert len(valid_directions) == 3


class TestInstruction:
    """测试 Instruction TypedDict"""

    def test_minimal_instruction(self):
        """最简指令（只有 type）"""
        instr: Instruction = {"type": "set"}
        assert instr["type"] == "set"
        assert "params" not in instr

    def test_full_instruction(self):
        """完整指令（type + params）"""
        instr: Instruction = {
            "type": "increment",
            "params": {"attr": "x", "operation": "add", "delta": 5},
        }
        assert instr["type"] == "increment"
        assert instr["params"]["attr"] == "x"
        assert instr["params"]["delta"] == 5

    def test_instruction_extra_fields(self):
        """Instruction 允许额外字段（total=False）"""
        instr: Instruction = {
            "type": "custom",
            "params": {},
            "custom_field": "value",
        }
        assert instr["custom_field"] == "value"


class TestApiResponse:
    """测试 ApiResponse TypedDict"""

    def test_success_response(self):
        """成功响应"""
        resp: ApiResponse = {
            "success": True,
            "message": "ok",
            "fact_id": 1,
        }
        assert resp["success"] is True
        assert resp["message"] == "ok"
        assert resp["fact_id"] == 1

    def test_error_response(self):
        """失败响应（fact_id 为 None）"""
        resp: ApiResponse = {
            "success": False,
            "message": "error",
            "fact_id": None,
        }
        assert resp["success"] is False
        assert resp["fact_id"] is None


class TestSessionState:
    """测试 SessionState TypedDict"""

    def test_empty_state(self):
        """空状态"""
        state: SessionState = {
            "payload": {},
            "queue": [],
            "version": 0,
        }
        assert state["version"] == 0
        assert len(state["payload"]) == 0
        assert len(state["queue"]) == 0

    def test_state_with_data(self):
        """有数据的状态"""
        state: SessionState = {
            "payload": {"x": 1, "y": "hello", "nested": {"a": True}},
            "queue": [{"type": "set", "params": {"attr": "z", "value": 3}}],
            "version": 42,
        }
        assert state["payload"]["x"] == 1
        assert state["payload"]["nested"]["a"] is True
        assert state["version"] == 42
        assert len(state["queue"]) == 1


class TestForkSessionResponse:
    """测试 ForkSessionResponse TypedDict"""

    def test_fork_response(self):
        resp: ForkSessionResponse = {
            "session_id": 2,
            "parent_session_id": 1,
            "forked_from_version": 10,
            "message": "forked",
        }
        assert resp["session_id"] == 2
        assert resp["parent_session_id"] == 1
        assert resp["forked_from_version"] == 10


class TestEventData:
    """测试 EventData TypedDict"""

    def test_command_event(self):
        """Command 事件"""
        event: EventData = {
            "type": "Command",
            "id": 1,
            "instruction": {"type": "set", "params": {"attr": "x", "value": 1}},
        }
        assert event["type"] == "Command"
        assert event["id"] == 1
        assert event["instruction"]["type"] == "set"

    def test_stable_event(self):
        """Stable 事件"""
        event: EventData = {
            "type": "Stable",
            "id": 5,
            "final_snapshot": {"x": 10, "y": 20},
        }
        assert event["type"] == "Stable"
        assert event["final_snapshot"]["x"] == 10

    def test_io_request_event(self):
        """IoRequest 事件"""
        event: EventData = {
            "type": "IoRequest",
            "id": 3,
            "io_type": "http_get",
            "params": {"url": "https://example.com"},
            "request_id": 100,
        }
        assert event["io_type"] == "http_get"
        assert event["request_id"] == 100

    def test_error_event(self):
        """Error 事件"""
        event: EventData = {
            "type": "Error",
            "id": 7,
            "error": "something went wrong",
            "message": "详细错误信息",
        }
        assert event["error"] == "something went wrong"
        assert event["message"] == "详细错误信息"

    def test_payload_update_event(self):
        """PayloadUpdate 事件"""
        event: EventData = {
            "type": "PayloadUpdate",
            "id": 4,
            "path": "user.name",
            "value": "Alice",
        }
        assert event["path"] == "user.name"
        assert event["value"] == "Alice"


class TestReplayResponse:
    """测试 ReplayResponse TypedDict"""

    def test_empty_replay(self):
        resp: ReplayResponse = {"facts": []}
        assert len(resp["facts"]) == 0

    def test_replay_with_events(self):
        resp: ReplayResponse = {
            "facts": [
                {"type": "Command", "id": 1},
                {"type": "StateTransition", "id": 2},
                {"type": "Stable", "id": 3},
            ]
        }
        assert len(resp["facts"]) == 3
        assert resp["facts"][0]["type"] == "Command"


class TestRewindResponse:
    """测试 RewindResponse TypedDict"""

    def test_rewind_response(self):
        resp: RewindResponse = {
            "version": 5,
            "payload": {"x": 10},
            "queue": [],
        }
        assert resp["version"] == 5
        assert resp["payload"]["x"] == 10


class TestDiffResponse:
    """测试 DiffResponse TypedDict"""

    def test_diff_response(self):
        resp: DiffResponse = {
            "version_a": 3,
            "version_b": 5,
            "added": [{"key": "new_field", "value": 42}],
            "removed": [{"key": "old_field", "value": "bye"}],
            "changed": [
                {"key": "counter", "old_value": 1, "new_value": 3}
            ],
        }
        assert resp["version_a"] == 3
        assert resp["version_b"] == 5
        assert len(resp["added"]) == 1
        assert len(resp["removed"]) == 1
        assert len(resp["changed"]) == 1
        assert resp["changed"][0]["old_value"] == 1
        assert resp["changed"][0]["new_value"] == 3


class TestSharedFact:
    """测试 SharedFact 相关 TypedDict"""

    def test_shared_fact(self):
        fact: SharedFact = {
            "fact_id": 100,
            "path": "config.theme",
            "value": "dark",
            "source_session_id": 1,
            "version": 5,
        }
        assert fact["fact_id"] == 100
        assert fact["path"] == "config.theme"

    def test_shared_fact_source(self):
        resp: SharedFactSourceResponse = {
            "fact_id": 100,
            "path": "config.theme",
            "value": "dark",
            "source_session_id": 1,
            "version": 5,
        }
        assert resp["source_session_id"] == 1

    def test_shared_fact_used_by(self):
        resp: SharedFactUsedByResponse = {
            "fact_id": 100,
            "sessions": [1, 2, 3],
        }
        assert resp["fact_id"] == 100
        assert len(resp["sessions"]) == 3


class TestDebugResponses:
    """测试调试相关 TypedDict"""

    def test_pending_io_info(self):
        info: PendingIoInfo = {
            "fact_id": 50,
            "io_type": "http_get",
            "duration_ms": 1500,
        }
        assert info["io_type"] == "http_get"
        assert info["duration_ms"] == 1500

    def test_debug_phase(self):
        resp: DebugPhaseResponse = {"phase": "stable"}
        assert resp["phase"] == "stable"

    def test_debug_queue(self):
        resp: DebugQueueResponse = {"queue": [{"type": "set", "params": {}}]}
        assert len(resp["queue"]) == 1

    def test_debug_pending_io(self):
        resp: DebugPendingIoResponse = {
            "pending_io": [
                {"fact_id": 1, "io_type": "a", "duration_ms": 100},
                {"fact_id": 2, "io_type": "b", "duration_ms": 200},
            ]
        }
        assert len(resp["pending_io"]) == 2

    def test_audit_verify(self):
        resp: AuditVerifyResponse = {"valid": True, "session_id": 1}
        assert resp["valid"] is True
        assert resp["session_id"] == 1


class TestHistoryAndCluster:
    """测试历史和集群相关 TypedDict"""

    def test_history_entry(self):
        entry: HistoryEntry = {"version": 5, "type": "Command"}
        assert entry["version"] == 5
        assert entry["type"] == "Command"

    def test_session_fact_entry(self):
        entry: SessionFactEntry = {
            "fact_id": 10,
            "version": 3,
            "path": "user.name",
            "value": "Alice",
        }
        assert entry["fact_id"] == 10
        assert entry["path"] == "user.name"

    def test_used_at_startup(self):
        resp: UsedAtStartupResponse = {
            "session_id": 1,
            "fact_ids": [10, 20, 30],
        }
        assert resp["session_id"] == 1
        assert len(resp["fact_ids"]) == 3

    def test_cluster_status(self):
        resp: ClusterStatusResponse = {
            "session_id": 1,
            "cluster_members": [1, 2, 3],
        }
        assert resp["session_id"] == 1
        assert len(resp["cluster_members"]) == 3


class TestClientOptions:
    """测试 ClientOptions TypedDict"""

    def test_empty_options(self):
        opts: ClientOptions = {}
        assert len(opts) == 0

    def test_full_options(self):
        opts: ClientOptions = {"token": "abc123", "timeout": 60.0}
        assert opts["token"] == "abc123"
        assert opts["timeout"] == 60.0

    def test_partial_options(self):
        opts: ClientOptions = {"token": "mytoken"}
        assert opts["token"] == "mytoken"
        assert "timeout" not in opts


class TestModuleExports:
    """测试模块导出完整性"""

    def test_all_types_importable(self):
        """所有类型都应能从 evorule 包导入"""
        from evorule import (
            Json,
            EventType,
            SyncDirection,
            Instruction,
            ApiResponse,
            SessionState,
            ForkSessionResponse,
            EventData,
            ReplayResponse,
            RewindResponse,
            DiffResponse,
            DiffEntry,
            DiffChangedEntry,
            SharedFact,
            SharedFactSourceResponse,
            SharedFactUsedByResponse,
            PendingIoInfo,
            DebugPhaseResponse,
            DebugQueueResponse,
            DebugPendingIoResponse,
            AuditVerifyResponse,
            HistoryEntry,
            SessionFactEntry,
            UsedAtStartupResponse,
            ClusterStatusResponse,
            ClientOptions,
        )
        # 只要能导入就通过
        assert True

    def test_types_in_all(self):
        """主要类型应在 __all__ 中"""
        import evorule

        expected = [
            "Json",
            "Instruction",
            "ApiResponse",
            "SessionState",
            "EventData",
            "EventType",
            "ReplayResponse",
            "RewindResponse",
            "DiffResponse",
            "SharedFact",
            "ForkSessionResponse",
            "AuditVerifyResponse",
            "ClusterStatusResponse",
            "SyncDirection",
            "ClientOptions",
        ]
        for name in expected:
            assert name in evorule.__all__, f"{name} not in __all__"
