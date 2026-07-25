# SPDX-License-Identifier: MIT
"""evorule.events 模块单元测试

测试 Event 类的构造、便捷属性和字符串表示。
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from evorule.events import Event


class TestEventConstruction:
    """测试 Event 构造"""

    def test_from_dict_basic(self):
        """从字典构造基本事件"""
        data = {"type": "Command", "id": 1}
        event = Event.from_dict(data)
        assert event.type == "Command"
        assert event.id == 1
        assert event.raw == data

    def test_from_dict_missing_fields(self):
        """缺少字段时有默认值"""
        event = Event.from_dict({})
        assert event.type == "Unknown"
        assert event.id == 0
        assert event.raw == {}

    def test_frozen(self):
        """Event 应是 frozen 的，不可修改"""
        event = Event.from_dict({"type": "Command", "id": 1})
        with pytest.raises(AttributeError):
            event.type = "Stable"  # type: ignore[misc]

    def test_raw_not_in_repr(self):
        """raw 字段不应出现在 repr 中"""
        event = Event.from_dict({"type": "Command", "id": 1})
        r = repr(event)
        assert "raw" not in r
        assert "Command" in r
        assert "id=1" in r


class TestCommandEvent:
    """测试 Command 事件属性"""

    def test_instruction(self):
        data = {
            "type": "Command",
            "id": 30001,
            "instruction": {"type": "set", "params": {"attr": "x", "value": 1}},
        }
        event = Event.from_dict(data)
        assert event.instruction is not None
        assert event.instruction["type"] == "set"
        assert event.instruction["params"]["attr"] == "x"

    def test_no_instruction(self):
        event = Event.from_dict({"type": "Command", "id": 1})
        assert event.instruction is None


class TestStateTransitionEvent:
    """测试 StateTransition 事件属性"""

    def test_cause_and_payload(self):
        data = {
            "type": "StateTransition",
            "id": 2,
            "cause": 1,
            "new_payload": {"x": 1, "y": 2},
            "new_queue": [],
        }
        event = Event.from_dict(data)
        assert event.cause == 1
        assert event.new_payload == {"x": 1, "y": 2}
        assert event.new_queue == []

    def test_no_cause(self):
        event = Event.from_dict({"type": "StateTransition", "id": 2})
        assert event.cause is None


class TestIoRequestEvent:
    """测试 IoRequest 事件属性"""

    def test_io_request_fields(self):
        data = {
            "type": "IoRequest",
            "id": 5,
            "cause": 3,
            "io_type": "http_get",
            "params": {"url": "https://example.com"},
        }
        event = Event.from_dict(data)
        assert event.io_type == "http_get"
        assert event.params == {"url": "https://example.com"}
        assert event.cause == 3

    def test_no_params(self):
        event = Event.from_dict({"type": "IoRequest", "id": 5, "io_type": "call_external"})
        assert event.io_type == "call_external"
        assert event.params is None


class TestIoResponseEvent:
    """测试 IoResponse 事件属性"""

    def test_io_response_success(self):
        data = {
            "type": "IoResponse",
            "id": 6,
            "request_id": 100,
            "result": {"status": 200, "data": "ok"},
        }
        event = Event.from_dict(data)
        assert event.request_id == 100
        assert event.result == {"status": 200, "data": "ok"}
        assert event.error is None

    def test_io_response_error(self):
        data = {
            "type": "IoResponse",
            "id": 7,
            "request_id": 101,
            "error": "timeout",
        }
        event = Event.from_dict(data)
        assert event.request_id == 101
        assert event.error == "timeout"
        assert event.result is None


class TestStableEvent:
    """测试 Stable 事件属性"""

    def test_final_snapshot(self):
        data = {
            "type": "Stable",
            "id": 10,
            "final_snapshot": {"x": 10, "y": 20, "z": {"nested": True}},
        }
        event = Event.from_dict(data)
        assert event.final_snapshot is not None
        assert event.final_snapshot["x"] == 10
        assert event.final_snapshot["z"]["nested"] is True

    def test_no_snapshot(self):
        event = Event.from_dict({"type": "Stable", "id": 10})
        assert event.final_snapshot is None


class TestPayloadUpdateEvent:
    """测试 PayloadUpdate 事件属性"""

    def test_path_and_value(self):
        data = {
            "type": "PayloadUpdate",
            "id": 8,
            "path": "user.profile.name",
            "value": "Alice",
        }
        event = Event.from_dict(data)
        assert event.path == "user.profile.name"
        assert event.value == "Alice"

    def test_nested_value(self):
        data = {
            "type": "PayloadUpdate",
            "id": 9,
            "path": "config",
            "value": {"theme": "dark", "lang": "zh"},
        }
        event = Event.from_dict(data)
        assert event.path == "config"
        assert event.value["theme"] == "dark"


class TestErrorEvent:
    """测试 Error 事件属性"""

    def test_error_from_error_field(self):
        data = {
            "type": "Error",
            "id": 11,
            "error": "something went wrong",
        }
        event = Event.from_dict(data)
        assert event.error == "something went wrong"
        assert event.message is None

    def test_error_from_message_field(self):
        """error 属性优先取 error 字段，没有则取 message"""
        data = {
            "type": "Error",
            "id": 12,
            "message": "detailed error message",
        }
        event = Event.from_dict(data)
        assert event.error == "detailed error message"
        assert event.message == "detailed error message"

    def test_error_prefers_error_over_message(self):
        """同时有 error 和 message 时，error 属性取 error 字段"""
        data = {
            "type": "Error",
            "id": 13,
            "error": "short error",
            "message": "long message",
        }
        event = Event.from_dict(data)
        assert event.error == "short error"
        assert event.message == "long message"

    def test_no_error(self):
        event = Event.from_dict({"type": "Error", "id": 14})
        assert event.error is None
        assert event.message is None


class TestEventString:
    """测试 __str__ 输出"""

    def test_str_basic(self):
        event = Event.from_dict({"type": "Command", "id": 1})
        s = str(event)
        assert "Command" in s
        assert "id=1" in s

    def test_str_with_cause(self):
        event = Event.from_dict({"type": "StateTransition", "id": 2, "cause": 1})
        s = str(event)
        assert "cause=1" in s

    def test_str_with_io_type(self):
        event = Event.from_dict({"type": "IoRequest", "id": 5, "io_type": "http_get"})
        s = str(event)
        assert "io_type=http_get" in s

    def test_str_with_error(self):
        event = Event.from_dict({"type": "Error", "id": 11, "error": "failed"})
        s = str(event)
        assert "error=failed" in s

    def test_str_format(self):
        """字符串格式应以类型开头，以 ) 结尾"""
        event = Event.from_dict({"type": "Stable", "id": 10})
        s = str(event)
        assert s.startswith("Stable(")
        assert s.endswith(")")


class TestEventEquality:
    """测试 Event 相等性（dataclass 默认行为）"""

    def test_same_data_equal(self):
        """相同数据的两个 Event 应相等"""
        data = {"type": "Command", "id": 1, "instruction": {"type": "set"}}
        e1 = Event.from_dict(data)
        e2 = Event.from_dict(data)
        assert e1 == e2

    def test_different_id_not_equal(self):
        """不同 ID 的事件不相等"""
        e1 = Event.from_dict({"type": "Command", "id": 1})
        e2 = Event.from_dict({"type": "Command", "id": 2})
        assert e1 != e2

    def test_different_type_not_equal(self):
        """不同类型的事件不相等"""
        e1 = Event.from_dict({"type": "Command", "id": 1})
        e2 = Event.from_dict({"type": "Stable", "id": 1})
        assert e1 != e2

    def test_not_hashable(self):
        """因为 raw 字段是 dict（不可哈希），所以 Event 整体不可哈希

        这是预期行为：frozen dataclass 在有不可哈希字段时也不可哈希。
        """
        e = Event.from_dict({"type": "Command", "id": 1})
        with pytest.raises(TypeError):
            hash(e)


class TestModuleExports:
    """测试模块导出"""

    def test_event_importable_from_package(self):
        """Event 能从 evorule 包导入"""
        from evorule import Event

        assert Event is not None

    def test_event_in_all(self):
        """Event 在 __all__ 中"""
        import evorule

        assert "Event" in evorule.__all__
