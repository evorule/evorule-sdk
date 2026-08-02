# SPDX-License-Identifier: MIT
"""evorule.client 和 evorule.session 模块单元测试（Mock 版）

不依赖 evorule-server，使用 mock HTTP 客户端进行测试。
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from evorule import (
    AuthenticationError,
    CommandError,
    EvoruleClient,
    Session,
    SessionClosedError,
    SessionNotFoundError,
)


# ======================================================================
# 辅助函数
# ======================================================================


def _make_mock_response(
    status_code: int = 200,
    json_data: dict | list | None = None,
    text: str | None = None,
) -> MagicMock:
    """创建一个模拟的 httpx.Response"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text or json.dumps(json_data) if json_data else ""

    def raise_for_status() -> None:
        if status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {status_code}",
                request=MagicMock(),
                response=resp,
            )

    resp.raise_for_status = raise_for_status
    return resp


def _make_mock_client(mock_http: MagicMock) -> EvoruleClient:
    """创建一个带 mock HTTP 客户端的 EvoruleClient"""
    client = EvoruleClient("http://localhost:18080")
    client._http = mock_http  # type: ignore[assignment]
    return client


# ======================================================================
# EvoruleClient 测试
# ======================================================================


class TestEvoruleClientInit:
    """测试客户端初始化"""

    def test_create_client_defaults(self):
        """默认参数创建客户端"""
        client = EvoruleClient("http://localhost:18080")
        assert client._base_url == "http://localhost:18080"
        assert isinstance(client._http, httpx.AsyncClient)

    def test_create_with_token(self):
        """带 token 创建客户端"""
        client = EvoruleClient("http://localhost:18080", token="abc123")
        # token 会被设置到 headers 里
        # 这里只验证不报错
        assert client is not None

    def test_create_with_timeout(self):
        """带自定义超时创建客户端"""
        client = EvoruleClient("http://localhost:18080", timeout=60.0)
        assert client is not None

    def test_repr(self):
        """测试 repr"""
        client = EvoruleClient("http://localhost:18080")
        r = repr(client)
        assert "EvoruleClient" in r
        assert "localhost:18080" in r


class TestEvoruleClientHealth:
    """测试健康检查接口"""

    @pytest.mark.asyncio
    async def test_health_success(self):
        """健康检查成功"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": True, "message": "ok", "fact_id": None}
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.health()
        assert result["success"] is True
        assert result["message"] == "ok"
        mock_http.get.assert_called_once_with("/api/health")

    @pytest.mark.asyncio
    async def test_health_unauthorized(self):
        """健康检查返回 401"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=_make_mock_response(401))
        client = _make_mock_client(mock_http)

        with pytest.raises(AuthenticationError):
            await client.health()

    @pytest.mark.asyncio
    async def test_liveness(self):
        """Liveness 探针"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": True, "message": "alive", "fact_id": None}
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.liveness()
        assert result["message"] == "alive"
        mock_http.get.assert_called_once_with("/api/health/liveness")

    @pytest.mark.asyncio
    async def test_readiness(self):
        """Readiness 探针"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": True, "message": "ready", "fact_id": None}
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.readiness()
        assert result["message"] == "ready"
        mock_http.get.assert_called_once_with("/api/health/readiness")


class TestEvoruleClientSessions:
    """测试会话管理接口"""

    @pytest.mark.asyncio
    async def test_create_session(self):
        """创建会话"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200, {"session_id": 1, "message": "created"}
            )
        )
        client = _make_mock_client(mock_http)

        session = await client.create_session()
        assert isinstance(session, Session)
        assert session.session_id == 1
        assert session.closed is False
        mock_http.post.assert_called_once_with("/api/sessions")

    @pytest.mark.asyncio
    async def test_create_session_unauthorized(self):
        """创建会话返回 401"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=_make_mock_response(401))
        client = _make_mock_client(mock_http)

        with pytest.raises(AuthenticationError):
            await client.create_session()

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """列出会话"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(200, {"sessions": [1, 2, 3]})
        )
        client = _make_mock_client(mock_http)

        sessions = await client.list_sessions()
        assert sessions == [1, 2, 3]
        mock_http.get.assert_called_once_with("/api/sessions")

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self):
        """空会话列表"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(200, {"sessions": []})
        )
        client = _make_mock_client(mock_http)

        sessions = await client.list_sessions()
        assert sessions == []


class TestEvoruleClientFork:
    """测试分叉会话接口"""

    @pytest.mark.asyncio
    async def test_fork_from_latest(self):
        """从最新版本分叉"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200,
                {
                    "session_id": 2,
                    "parent_session_id": 1,
                    "forked_from_version": 10,
                    "message": "forked",
                },
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.fork_session(1)
        assert result["session_id"] == 2
        assert result["parent_session_id"] == 1
        mock_http.post.assert_called_once_with("/api/sessions/from/1")

    @pytest.mark.asyncio
    async def test_fork_with_version(self):
        """从指定版本分叉"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200,
                {
                    "session_id": 3,
                    "parent_session_id": 1,
                    "forked_from_version": 5,
                    "message": "forked",
                },
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.fork_session(1, version=5)
        assert result["forked_from_version"] == 5
        mock_http.post.assert_called_once_with(
            "/api/sessions/fork/1", params={"version": 5}
        )


class TestEvoruleClientSharedFacts:
    """测试共享 Fact 接口"""

    @pytest.mark.asyncio
    async def test_shared_facts_no_prefix(self):
        """查询所有共享 Fact"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200,
                [
                    {
                        "fact_id": 1,
                        "path": "a.b",
                        "value": 10,
                        "source_session_id": 1,
                        "version": 1,
                    }
                ],
            )
        )
        client = _make_mock_client(mock_http)

        facts = await client.shared_facts()
        assert len(facts) == 1
        assert facts[0]["fact_id"] == 1
        mock_http.get.assert_called_once_with("/api/shared/facts", params={})

    @pytest.mark.asyncio
    async def test_shared_facts_with_prefix(self):
        """按前缀查询共享 Fact"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=_make_mock_response(200, []))
        client = _make_mock_client(mock_http)

        await client.shared_facts(prefix="user.profile")
        mock_http.get.assert_called_once_with(
            "/api/shared/facts", params={"prefix": "user.profile"}
        )

    @pytest.mark.asyncio
    async def test_shared_fact_source(self):
        """查询 Fact 来源"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200,
                {
                    "fact_id": 1,
                    "path": "x",
                    "value": 42,
                    "source_session_id": 1,
                    "version": 1,
                },
            )
        )
        client = _make_mock_client(mock_http)

        result = await client.shared_fact_source(1)
        assert result["fact_id"] == 1
        mock_http.get.assert_called_once_with("/api/shared/facts/1/source")

    @pytest.mark.asyncio
    async def test_shared_fact_used_by(self):
        """查询谁用了这个 Fact"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(200, {"fact_id": 1, "sessions": [1, 2]})
        )
        client = _make_mock_client(mock_http)

        result = await client.shared_fact_used_by(1)
        assert result["sessions"] == [1, 2]
        mock_http.get.assert_called_once_with("/api/shared/facts/1/used_by")


class TestEvoruleClientClose:
    """测试客户端关闭"""

    @pytest.mark.asyncio
    async def test_close(self):
        """关闭客户端"""
        mock_http = MagicMock()
        mock_http.aclose = AsyncMock()
        client = _make_mock_client(mock_http)

        await client.close()
        mock_http.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """async with 上下文管理器"""
        mock_http = MagicMock()
        mock_http.aclose = AsyncMock()
        client = _make_mock_client(mock_http)

        async with client as c:
            assert c is client

        mock_http.aclose.assert_called_once()


# ======================================================================
# Session 测试
# ======================================================================


class TestSessionBasics:
    """测试 Session 基本属性"""

    def test_session_creation(self):
        """创建 Session"""
        mock_client = MagicMock()
        session = Session(mock_client, 42)
        assert session.session_id == 42
        assert session.closed is False

    def test_repr(self):
        """测试 repr"""
        mock_client = MagicMock()
        session = Session(mock_client, 1)
        r = repr(session)
        assert "Session" in r
        assert "id=1" in r
        assert "closed=False" in r

    def test_closed_property(self):
        """closed 属性只读（通过 close 方法修改）"""
        mock_client = MagicMock()
        session = Session(mock_client, 1)
        assert session.closed is False

    def test_check_closed(self):
        """_check_closed 应抛出 SessionClosedError"""
        mock_client = MagicMock()
        session = Session(mock_client, 1)
        session._closed = True  # 直接设置

        with pytest.raises(SessionClosedError):
            session._check_closed()

    def test_url_builder(self):
        """URL 构建"""
        mock_client = MagicMock()
        session = Session(mock_client, 5)

        assert session._url() == "/api/sessions/5"
        assert session._url("/command") == "/api/sessions/5/command"
        assert session._url("/state") == "/api/sessions/5/state"


class TestSessionCommand:
    """测试命令提交"""

    @pytest.mark.asyncio
    async def test_command_success(self):
        """命令提交成功"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": True, "message": "ok", "fact_id": 1}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.command({"type": "set", "params": {"attr": "x", "value": 1}})
        assert result["success"] is True
        assert result["fact_id"] == 1
        mock_http.post.assert_called_once()
        args, kwargs = mock_http.post.call_args
        assert args[0] == "/api/sessions/1/command"
        assert kwargs["json"] == {
            "instruction": {"type": "set", "params": {"attr": "x", "value": 1}}
        }

    @pytest.mark.asyncio
    async def test_command_failed(self):
        """命令提交失败（success=false）"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": False, "message": "channel closed", "fact_id": None}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        with pytest.raises(CommandError) as exc_info:
            await session.command({"type": "set", "params": {"attr": "x", "value": 1}})
        assert "channel closed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_command_not_found(self):
        """会话不存在"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=_make_mock_response(404))
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 999)

        with pytest.raises(SessionNotFoundError):
            await session.command({"type": "set", "params": {"attr": "x", "value": 1}})

    @pytest.mark.asyncio
    async def test_command_closed_session(self):
        """已关闭的会话不能提交命令"""
        mock_client = MagicMock()
        session = Session(mock_client, 1)
        session._closed = True

        with pytest.raises(SessionClosedError):
            await session.command({"type": "set", "params": {"attr": "x", "value": 1}})


class TestSessionState:
    """测试状态查询"""

    @pytest.mark.asyncio
    async def test_state(self):
        """查询状态"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"payload": {"x": 10}, "queue": [], "version": 5}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        state = await session.state()
        assert state["payload"]["x"] == 10
        assert state["version"] == 5
        mock_http.get.assert_called_once_with("/api/sessions/1/state")


class TestSessionTimeMachine:
    """测试时间机器功能"""

    @pytest.mark.asyncio
    async def test_replay(self):
        """回放"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"facts": [{"type": "Command", "id": 1}]}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.replay()
        assert len(result["facts"]) == 1
        mock_http.get.assert_called_once_with("/api/sessions/1/replay")

    @pytest.mark.asyncio
    async def test_rewind(self):
        """回滚"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"version": 3, "payload": {"x": 5}, "queue": []}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.rewind(3)
        assert result["version"] == 3
        mock_http.get.assert_called_once_with("/api/sessions/1/rewind?version=3")

    @pytest.mark.asyncio
    async def test_diff(self):
        """版本差异"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200,
                {
                    "version_a": 1,
                    "version_b": 3,
                    "added": [],
                    "removed": [],
                    "changed": [],
                },
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.diff(1, 3)
        assert result["version_a"] == 1
        assert result["version_b"] == 3
        mock_http.get.assert_called_once_with(
            "/api/sessions/1/diff", params={"a": 1, "b": 3}
        )


class TestSessionClose:
    """测试会话关闭"""

    @pytest.mark.asyncio
    async def test_close(self):
        """关闭会话"""
        mock_http = MagicMock()
        mock_http.delete = AsyncMock(return_value=_make_mock_response(200))
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        assert session.closed is False
        await session.close()
        assert session.closed is True
        mock_http.delete.assert_called_once_with("/api/sessions/1")

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """重复关闭安全（幂等）"""
        mock_http = MagicMock()
        mock_http.delete = AsyncMock(return_value=_make_mock_response(200))
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        await session.close()
        await session.close()  # 第二次不应报错
        assert session.closed is True
        assert mock_http.delete.call_count == 1  # 只调用一次

    @pytest.mark.asyncio
    async def test_close_swallows_exceptions(self):
        """关闭时网络错误应被忽略"""
        mock_http = MagicMock()
        mock_http.delete = AsyncMock(side_effect=httpx.ConnectError("network error"))
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        # 不应抛出异常
        await session.close()
        assert session.closed is True

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """async with 上下文管理器"""
        mock_http = MagicMock()
        mock_http.delete = AsyncMock(return_value=_make_mock_response(200))
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        async with session as s:
            assert s is session
            assert s.closed is False

        assert session.closed is True
        mock_http.delete.assert_called_once()


class TestSessionCluster:
    """测试集群功能"""

    @pytest.mark.asyncio
    async def test_join_cluster(self):
        """加入集群"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(
                200, {"success": True, "message": "joined"}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.join(target_id=2)
        assert result["success"] is True
        mock_http.post.assert_called_once()
        args, kwargs = mock_http.post.call_args
        assert args[0] == "/api/sessions/1/join"
        assert kwargs["json"]["target_id"] == 2

    @pytest.mark.asyncio
    async def test_join_with_direction(self):
        """加入集群（指定方向）"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(200, {"success": True})
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        await session.join(target_id=2, direction="btoa")
        args, kwargs = mock_http.post.call_args
        assert kwargs["json"]["direction"] == "btoa"

    @pytest.mark.asyncio
    async def test_join_no_target(self):
        """未指定 target_id 应抛出 ValueError"""
        mock_client = MagicMock()
        session = Session(mock_client, 1)

        with pytest.raises(ValueError):
            await session.join()

    @pytest.mark.asyncio
    async def test_leave_cluster(self):
        """离开集群"""
        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            return_value=_make_mock_response(200, {"success": True})
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        await session.leave()
        mock_http.post.assert_called_once_with("/api/sessions/1/leave")

    @pytest.mark.asyncio
    async def test_cluster_status(self):
        """查询集群状态"""
        mock_http = MagicMock()
        mock_http.get = AsyncMock(
            return_value=_make_mock_response(
                200, {"session_id": 1, "cluster_members": [1, 2, 3]}
            )
        )
        mock_client = MagicMock()
        mock_client._http = mock_http
        session = Session(mock_client, 1)

        result = await session.cluster_status()
        assert result["cluster_members"] == [1, 2, 3]
        mock_http.get.assert_called_once_with("/api/sessions/1/cluster")


class TestModuleExports:
    """测试模块导出"""

    def test_client_importable(self):
        from evorule import EvoruleClient

        assert EvoruleClient is not None

    def test_session_importable(self):
        from evorule import Session

        assert Session is not None

    def test_in_all(self):
        import evorule

        assert "EvoruleClient" in evorule.__all__
        assert "Session" in evorule.__all__
