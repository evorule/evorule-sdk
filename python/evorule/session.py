# SPDX-License-Identifier: Apache-2.0
"""evorule SDK 会话管理

每个 Session 对应服务端一个独立的长驻反应器实例，
拥有独立的 state / FactsLog / command-event 通道。
"""

from __future__ import annotations

import json
from types import TracebackType
from typing import TYPE_CHECKING, Any, AsyncIterator

import httpx

from .events import Event
from .exceptions import CommandError, SessionClosedError, SessionNotFoundError

if TYPE_CHECKING:
    from .client import EvoruleClient


class Session:
    """会话客户端

    通过 `EvoruleClient.create_session()` 创建，封装单会话的命令提交、
    状态查询、payload 更新和 SSE 事件流订阅。

    支持 `async with` 上下文管理器，退出时自动关闭会话。
    """

    def __init__(self, client: EvoruleClient, session_id: int) -> None:
        self._client = client
        self.session_id = session_id
        self._closed = False

    def __repr__(self) -> str:
        return f"Session(id={self.session_id}, closed={self._closed})"

    async def __aenter__(self) -> Session:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @property
    def closed(self) -> bool:
        """会话是否已关闭"""
        return self._closed

    def _check_closed(self) -> None:
        if self._closed:
            raise SessionClosedError(f"Session {self.session_id} already closed")

    def _url(self, suffix: str = "") -> str:
        base = f"/api/sessions/{self.session_id}"
        return f"{base}{suffix}" if suffix else base

    async def command(self, instruction: dict[str, Any]) -> dict[str, Any]:
        """提交命令到会话的反应器

        参数：
            instruction: 指令 JSON，如 `{"type": "increment", "params": {"attr": "x", "operation": "add", "delta": 5}}`

        返回：
            服务端响应 `{"success": bool, "message": str, "fact_id": int | None}`

        异常：
            CommandError: 命令提交失败（channel closed）
            SessionNotFoundError: 会话不存在
        """
        self._check_closed()
        resp = await self._client._http.post(
            self._url("/command"),
            json={"instruction": instruction},
        )
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", False):
            raise CommandError(data.get("message", "Command submission failed"))
        return data

    async def state(self) -> dict[str, Any]:
        """查询会话当前状态快照

        返回：
            `{"payload": {...}, "queue": [...], "version": int}`
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/state"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def update_payload(self, path: str, value: Any) -> dict[str, Any]:
        """更新会话的 payload 字段

        参数：
            path: 字段路径（如 "status" 或 "nested.field"）
            value: 字段值

        返回：
            服务端响应

        异常：
            CommandError: 反应器通道已关闭（payload 提交失败）
            SessionNotFoundError: 会话不存在
        """
        self._check_closed()
        resp = await self._client._http.post(
            self._url("/payload"),
            json={"path": path, "value": value},
        )
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", False):
            raise CommandError(data.get("message", "Payload update failed"))
        return data

    async def interrupt(self) -> dict[str, Any]:
        """中断会话反应器执行（POST /api/sessions/{id}/interrupt）

        触发服务端 AtomicBool 中断标志，反应器主循环在下个检查点
        会发出 Error + Stable 事件并停止当前指令序列。

        返回：
            服务端响应
        """
        self._check_closed()
        resp = await self._client._http.post(self._url("/interrupt"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def replay(self) -> list[dict[str, Any]]:
        """回放会话的完整 FactsLog（GET /api/sessions/{id}/replay）

        返回：
            Fact 列表，每项为完整 fact 对象 + version 字段
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/replay"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def rewind(self, version: int) -> dict[str, Any]:
        """回滚到指定版本（GET /api/sessions/{id}/rewind?version=X）

        参数：
            version: 目标版本号

        返回：
            `{"session_id": int, "target_version": int, "actual_version": int,
              "payload": {...}, "queue": [...]}`
            actual_version 是实际回滚到的版本（可能因版本间隙与 target_version 不同）
        """
        self._check_closed()
        resp = await self._client._http.get(self._url(f"/rewind?version={version}"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def diff(self, from_version: int, to_version: int) -> dict[str, Any]:
        """对比两个版本的 payload 差异（GET /api/sessions/{id}/diff）

        参数：
            from_version: 起始版本（对应服务端参数 a）
            to_version: 目标版本（对应服务端参数 b）

        返回：
            `{"session_id": int, "from_version": int, "to_version": int,
              "added": [...], "removed": [...], "changed": [...],
              "unchanged": [...], "summary": {...}}`
        """
        self._check_closed()
        resp = await self._client._http.get(
            self._url("/diff"),
            params={"a": from_version, "b": to_version},
        )
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def submit_io_response(
        self,
        request_id: int,
        result: Any = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """提交 I/O 响应（POST /api/sessions/{id}/io_response）

        用于回应 IoRequest 事件。result 与 error 二选一：成功时填 result，
        失败时填 error。

        参数：
            request_id: 对应 IoRequest 事件的 request_id
            result: I/O 成功结果（可选）
            error: I/O 错误信息（可选）

        返回：
            服务端响应
        """
        self._check_closed()
        body: dict[str, Any] = {"request_id": request_id}
        if error is not None:
            body["error"] = error
        else:
            body["result"] = result
        resp = await self._client._http.post(self._url("/io_response"), json=body)
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def record_used_at_startup(self, fact_ids: list[int]) -> dict[str, Any]:
        """记录会话启动时引用的共享 Fact（POST /api/sessions/{id}/used_at_startup）

        参数：
            fact_ids: 启动时引用的共享 Fact ID 列表

        返回：
            服务端响应
        """
        self._check_closed()
        resp = await self._client._http.post(
            self._url("/used_at_startup"),
            json={"fact_ids": fact_ids},
        )
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def debug_phase(self) -> str:
        """查询反应器当前阶段（GET /api/sessions/{id}/debug/phase）

        返回：
            phase 取值: Idle/Draining/Executing/AwaitingIo/Stable/Error
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/debug/phase"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("phase", "Unknown")

    async def debug_queue(self) -> list[dict[str, Any]]:
        """查询反应器待执行队列（GET /api/sessions/{id}/debug/queue）

        返回：
            queue 为当前队列中的指令 JSON 列表
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/debug/queue"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("queue", [])

    async def debug_pending_io(self) -> list[dict[str, Any]]:
        """查询挂起的 I/O 请求（GET /api/sessions/{id}/debug/pending_io）

        返回：
            pending_io 列表中每项包含 fact_id / io_type / duration_ms
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/debug/pending_io"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("pending_io", [])

    async def audit(self, limit: int | None = None) -> dict[str, Any]:
        """查询会话审计报告（GET /api/sessions/{id}/audit）

        参数：
            limit: 可选，返回条目数限制（客户端侧过滤）

        返回：
            审计报告 JSON（包含事实链、哈希等）
        """
        self._check_closed()
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        resp = await self._client._http.get(self._url("/audit"), params=params if params else None)
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def audit_verify(self) -> dict[str, Any]:
        """校验会话审计链完整性（GET /api/sessions/{id}/audit/verify）

        返回：
            `{"valid": bool, "session_id": int}`
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/audit/verify"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """查询会话历史（GET /api/sessions/{id}/history）

        参数：
            limit: 可选，返回条目数限制（客户端侧截断）

        返回：
            `[{"version": int, "type": str, ...}, ...]`，每项为完整 fact + version
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/history"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result, list) and limit is not None:
            return result[:limit]
        return result

    async def facts_by_prefix(self, prefix: str = "") -> list[dict[str, Any]]:
        """按路径前缀查询会话内 Facts（GET /api/sessions/{id}/facts）

        参数：
            prefix: 路径前缀（可选）

        返回：
            `[{"fact_id", "version", "path", "value"}, ...]`
        """
        self._check_closed()
        params: dict[str, str] = {}
        if prefix:
            params["prefix"] = prefix
        resp = await self._client._http.get(self._url("/facts"), params=params)
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def get_used_at_startup(self) -> list[int]:
        """查询会话启动时引用的共享 Fact ID（GET /api/sessions/{id}/used_at_startup）

        返回：
            Fact ID 列表
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/used_at_startup"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("fact_ids", [])

    # ===== S4 端点补齐：会话运行时状态查询 =====

    async def finished(self) -> bool:
        """查询会话是否已完成（GET /api/sessions/{id}/finished）

        返回：
            True 如果会话已结束（反应器到达 Stable 或 Error 终态）
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/finished"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("finished", False)

    async def causal_depth(self) -> int:
        """查询因果链深度（GET /api/sessions/{id}/causal_depth）

        返回：
            当前因果链深度
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/causal_depth"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("causal_depth", 0)

    async def invariants(self) -> int:
        """查询结构不变式违规计数（GET /api/sessions/{id}/invariants）

        返回：
            结构不变式违规次数（0 表示无违规）
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/invariants"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("structural_invariant_violations", 0)

    async def pending_io_count(self) -> int:
        """查询待处理 I/O 数量（GET /api/sessions/{id}/pending_io_count）

        返回：
            当前挂起的 I/O 请求数
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/pending_io_count"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("pending_io_count", 0)

    async def step(self) -> int:
        """查询当前执行步数（GET /api/sessions/{id}/step）

        返回：
            当前执行步数
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/step"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json().get("current_step", 0)

    async def snapshot(self) -> dict[str, Any]:
        """查询完整状态快照（GET /api/sessions/{id}/snapshot）

        返回：
            `{"session_id", "finished", "phase", "version", "steps",
              "pending_io_count", "structural_invariant_violations"}`
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/snapshot"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def join(
        self,
        target_id: int | None = None,
        direction: str | None = None,
        target_session_id: int | None = None,
    ) -> dict[str, Any]:
        """加入集群协作（POST /api/sessions/{id}/join）

        ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点（多 reactor 协作原语属应用层功能）。
        调用此方法将返回 404。保留代码供未来 cluster 模块重新启用时使用。

        参数：
            target_id: 目标会话 ID（推荐使用）
            target_session_id: 目标会话 ID（别名，向后兼容）
            direction: 同步方向，可选 "atob" / "btoa" / None（双向）

        返回：
            服务端响应
        """
        self._check_closed()
        tid = target_id if target_id is not None else target_session_id
        if tid is None:
            raise ValueError("target_id or target_session_id must be provided")
        body: dict[str, Any] = {"target_id": tid}
        if direction is not None:
            body["direction"] = direction
        resp = await self._client._http.post(self._url("/join"), json=body)
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def leave(self) -> dict[str, Any]:
        """离开所有集群协作（POST /api/sessions/{id}/leave）

        ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点。调用此方法将返回 404。

        返回：
            服务端响应
        """
        self._check_closed()
        resp = await self._client._http.post(self._url("/leave"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def cluster_status(self) -> dict[str, Any]:
        """查询会话集群成员（GET /api/sessions/{id}/cluster）

        ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点。调用此方法将返回 404。

        返回：
            `{"session_id": int, "cluster_members": [...]}`
        """
        self._check_closed()
        resp = await self._client._http.get(self._url("/cluster"))
        if resp.status_code == 404:
            raise SessionNotFoundError(f"Session {self.session_id} not found")
        resp.raise_for_status()
        return resp.json()

    async def events(self) -> AsyncIterator[Event]:
        """订阅 SSE 事件流

        返回一个异步迭代器，持续产出 Event 对象。
        流是长连接，反应器在长驻模式下持续推送事件。

        使用示例：
            async for event in session.events():
                if event.type == "Stable":
                    break
                print(event)

        注意：调用方负责在适当时机 break 退出循环，
        否则流将持续到会话关闭或连接断开。
        """
        self._check_closed()
        url = self._url("/events")
        async with self._client._http.stream("GET", url) as response:
            if response.status_code == 404:
                raise SessionNotFoundError(f"Session {self.session_id} not found")
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    try:
                        data = json.loads(data_str)
                        yield Event.from_dict(data)
                    except json.JSONDecodeError:
                        continue

    async def close(self) -> None:
        """关闭会话（DELETE /api/sessions/{id}）

        重复调用安全（幂等）。关闭时的网络错误被忽略（会话可能已被 server 清理）。
        """
        if self._closed:
            return
        self._closed = True
        try:
            await self._client._http.delete(self._url())
        except httpx.HTTPError:
            # 网络错误忽略：会话可能已被 server 清理，或网络已断开
            pass
