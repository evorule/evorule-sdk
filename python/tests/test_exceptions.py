# SPDX-License-Identifier: MIT
"""evorule.exceptions 模块单元测试

测试所有异常类的继承关系和基本行为。
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from evorule.exceptions import (
    AuthenticationError,
    CommandError,
    EvoruleConnectionError,
    EvoruleError,
    SessionClosedError,
    SessionNotFoundError,
)


class TestEvoruleError:
    """测试基础异常 EvoruleError"""

    def test_is_exception(self):
        """应继承自 Exception"""
        assert issubclass(EvoruleError, Exception)

    def test_raise_and_catch(self):
        """能被 raise 和 except"""
        with pytest.raises(EvoruleError) as exc_info:
            raise EvoruleError("test error")
        assert str(exc_info.value) == "test error"

    def test_with_message(self):
        """支持自定义消息"""
        err = EvoruleError("something went wrong")
        assert str(err) == "something went wrong"

    def test_without_message(self):
        """支持无参构造"""
        err = EvoruleError()
        assert str(err) == ""


class TestAuthenticationError:
    """测试认证失败异常"""

    def test_inheritance(self):
        """应继承自 EvoruleError"""
        assert issubclass(AuthenticationError, EvoruleError)
        assert issubclass(AuthenticationError, Exception)

    def test_catch_as_base(self):
        """能用基类捕获"""
        with pytest.raises(EvoruleError):
            raise AuthenticationError("unauthorized")

    def test_message(self):
        err = AuthenticationError("invalid token")
        assert str(err) == "invalid token"


class TestSessionNotFoundError:
    """测试会话不存在异常"""

    def test_inheritance(self):
        assert issubclass(SessionNotFoundError, EvoruleError)

    def test_catch_as_base(self):
        with pytest.raises(EvoruleError):
            raise SessionNotFoundError("session 404 not found")

    def test_message(self):
        err = SessionNotFoundError("session 99 not found")
        assert "99" in str(err)


class TestSessionClosedError:
    """测试会话已关闭异常"""

    def test_inheritance(self):
        assert issubclass(SessionClosedError, EvoruleError)

    def test_catch_as_base(self):
        with pytest.raises(EvoruleError):
            raise SessionClosedError("session already closed")

    def test_message(self):
        err = SessionClosedError("cannot operate on closed session")
        assert "closed" in str(err)


class TestCommandError:
    """测试命令提交失败异常"""

    def test_inheritance(self):
        assert issubclass(CommandError, EvoruleError)

    def test_catch_as_base(self):
        with pytest.raises(EvoruleError):
            raise CommandError("command failed")

    def test_message(self):
        err = CommandError("channel closed")
        assert "channel" in str(err)


class TestEvoruleConnectionError:
    """测试连接失败异常"""

    def test_inheritance(self):
        assert issubclass(EvoruleConnectionError, EvoruleError)

    def test_catch_as_base(self):
        with pytest.raises(EvoruleError):
            raise EvoruleConnectionError("connection refused")

    def test_message(self):
        err = EvoruleConnectionError("server unreachable")
        assert "server" in str(err)


class TestExceptionHierarchy:
    """测试异常继承层次"""

    def test_all_subclasses_of_base(self):
        """所有异常都应继承自 EvoruleError"""
        subclasses = [
            AuthenticationError,
            SessionNotFoundError,
            SessionClosedError,
            CommandError,
            EvoruleConnectionError,
        ]
        for cls in subclasses:
            assert issubclass(cls, EvoruleError), f"{cls.__name__} 不继承自 EvoruleError"

    def test_distinct_types(self):
        """不同异常类型不能相互捕获"""
        # AuthenticationError 不应被 SessionNotFoundError 捕获
        with pytest.raises(AuthenticationError):
            try:
                raise AuthenticationError("auth failed")
            except SessionNotFoundError:
                pytest.fail("AuthenticationError 被 SessionNotFoundError 错误捕获")

    def test_try_except_order(self):
        """测试 except 顺序：具体异常应先于基类被捕获"""
        caught_by = None
        try:
            raise AuthenticationError("bad token")
        except AuthenticationError:
            caught_by = "specific"
        except EvoruleError:
            caught_by = "base"

        assert caught_by == "specific"


class TestModuleExports:
    """测试模块导出"""

    def test_all_exceptions_importable_from_package(self):
        """所有异常都能从 evorule 包导入"""
        from evorule import (
            AuthenticationError,
            CommandError,
            EvoruleConnectionError,
            EvoruleError,
            SessionClosedError,
            SessionNotFoundError,
        )
        # 只要能导入就通过
        assert True

    def test_exceptions_in_all(self):
        """所有异常都在 __all__ 中"""
        import evorule

        expected = [
            "EvoruleError",
            "AuthenticationError",
            "SessionNotFoundError",
            "SessionClosedError",
            "CommandError",
            "EvoruleConnectionError",
        ]
        for name in expected:
            assert name in evorule.__all__, f"{name} not in __all__"
