# SPDX-License-Identifier: AGPL-3.0-or-later
"""evorule SDK 主客户端

通过 HTTP API 与 evorule-server 交互，提供会话管理、健康检查等接口。

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

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from .exceptions import AuthenticationError, EvoruleError
from .session import Session


class EvoruleClient:
    """evorule-server 客户端

    参数：
        base_url: 服务器地址，如 "http://localhost:18080"
        token: Bearer 认证 token（可选，未提供时服务器需禁用认证）
        timeout: 请求超时时间（秒），默认 30

    支持 `async with` 上下文管理器，退出时自动关闭底层 HTTP 连接。
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        self._base_url = base_url

    def __repr__(self) -> str:
        return f"EvoruleClient(base_url={self._base_url!r})"

    async def __aenter__(self) -> EvoruleClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def health(self) -> dict[str, Any]:
        """健康检查（GET /api/health）

        返回：
            `{"success": true, "message": "ok", "fact_id": null}`
        """
        resp = await self._http.get("/api/health")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def liveness(self) -> dict[str, Any]:
        """Liveness 探针（GET /api/health/liveness）

        始终返回 200，只要进程在运行就算存活。

        返回：
            `{"success": true, "message": "alive", "fact_id": null}`
        """
        resp = await self._http.get("/api/health/liveness")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def readiness(self) -> dict[str, Any]:
        """Readiness 探针（GET /api/health/readiness）

        就绪时返回 200，未就绪（如优雅退出中）返回 503。

        返回：
            `{"success": true, "message": "ready", "fact_id": null}`
        异常：
            httpx.HTTPStatusError: 服务未就绪（503）
        """
        resp = await self._http.get("/api/health/readiness")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def fork_session(self, parent_id: int, version: int | None = None) -> dict[str, Any]:
        """从父会话的指定版本分叉新会话

        - 传 version 时使用 POST /api/sessions/fork/{parent_id}?version=X（需指定版本）
        - 不传 version 时使用 POST /api/sessions/from/{parent_id}（从最新版本分叉）

        参数：
            parent_id: 父会话 ID
            version: 分叉起点版本号（可选，不传则从最新版本分叉）

        返回：
            `{"session_id", "parent_session_id", "forked_from_version", "message"}`
        """
        if version is not None:
            resp = await self._http.post(
                f"/api/sessions/fork/{parent_id}",
                params={"version": version},
            )
        else:
            resp = await self._http.post(
                f"/api/sessions/from/{parent_id}",
            )
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def shared_facts(self, prefix: str = "") -> list[dict[str, Any]]:
        """查询共享 Fact 列表（GET /api/shared/facts）

        参数：
            prefix: 可选的路径前缀过滤（如 "user.profile"）

        返回：
            共享 Fact 列表，每项包含 fact_id / path / value / source_session_id / version
        """
        params: dict[str, str] = {}
        if prefix:
            params["prefix"] = prefix
        resp = await self._http.get("/api/shared/facts", params=params)
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def shared_fact_source(self, fact_id: int) -> dict[str, Any]:
        """查询共享 Fact 的来源信息（GET /api/shared/facts/{fact_id}/source）

        参数：
            fact_id: 共享 Fact ID

        返回：
            `{"fact_id", "path", "value", "source_session_id", "version"}`
        """
        resp = await self._http.get(f"/api/shared/facts/{fact_id}/source")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def shared_fact_used_by(self, fact_id: int) -> dict[str, Any]:
        """查询使用了指定共享 Fact 的会话列表（GET /api/shared/facts/{fact_id}/used_by）

        参数：
            fact_id: 共享 Fact ID

        返回：
            `{"fact_id": int, "sessions": [int, ...]}`
        """
        resp = await self._http.get(f"/api/shared/facts/{fact_id}/used_by")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def create_session(self) -> Session:
        """创建会话（POST /api/sessions）

        返回：
            Session 实例，封装单会话的操作接口
        """
        resp = await self._http.post("/api/sessions")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        data = resp.json()
        session_id = data["session_id"]
        return Session(self, session_id)

    async def list_sessions(self) -> list[int]:
        """列出所有活跃会话（GET /api/sessions）

        返回：
            会话 ID 列表
        """
        resp = await self._http.get("/api/sessions")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json().get("sessions", [])

    # ------------------------------------------------------------------
    # 快照包（DatasetBundle）API
    # 校验口径零复刻：六项校验链由服务端执行（evorule-bundle SSOT），
    # SDK 仅做 HTTP 薄封装。400 时透传服务端 error 字段，不静默。
    # ------------------------------------------------------------------

    async def import_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """导入快照包并激活（POST /api/bundles/import）

        六项硬校验 + 逐条 Schema 门禁由服务端执行；任一失败整体拒绝，
        成功则原子落盘并触发滚动热重载（导入即激活，T4）。

        参数：
            bundle: DatasetBundle 快照包对象（原样透传，不本地校验）

        返回：
            `{"imported", "bundle_id", "dataset_id", "activated_version",
              "entry_count", "missing_services"}`
        异常：
            EvoruleError: 服务端校验/落盘失败（400，消息为服务端 error 字段）
            httpx.HTTPStatusError: 其他 HTTP 错误
        """
        resp = await self._http.post("/api/bundles/import", json={"bundle": bundle})
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        if resp.status_code == 400:
            error = resp.json().get("error", "unknown error")
            raise EvoruleError(f"bundle 导入失败: {error}")
        resp.raise_for_status()
        return resp.json()

    async def dry_run_import(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """导入预检：只跑校验链，不落盘不热重载（POST /api/bundles/import/dry-run）

        参数：
            bundle: DatasetBundle 快照包对象（原样透传，不本地校验）

        返回：
            `{"valid", "bundle_id", "dataset_id", "source_version",
              "selection_mode", "resolved_version", "entry_count",
              "verdict", "missing_services"}`
        异常：
            EvoruleError: 预检未通过（400，消息为服务端 error 字段）
        """
        resp = await self._http.post("/api/bundles/import/dry-run", json={"bundle": bundle})
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        if resp.status_code == 400:
            error = resp.json().get("error", "unknown error")
            raise EvoruleError(f"bundle 预检未通过: {error}")
        resp.raise_for_status()
        return resp.json()

    async def list_active_bundles(self) -> dict[str, Any]:
        """查询当前激活的快照包列表（GET /api/bundles/active）

        返回：
            `{"bundles": [{"bundle_id", "dataset_id", "source_version",
              "selection_mode", "resolved_version?", "effective_from?",
              "content_hash", "entry_count"}], "count"}`
        """
        resp = await self._http.get("/api/bundles/active")
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def list_bundle_imports(self, limit: int = 100) -> dict[str, Any]:
        """查询快照包导入溯源历史（GET /api/bundles/imports）

        记录为管理元数据（含墙钟 imported_at），不参与审计验证链。

        参数：
            limit: 返回条数上限（1-1000，服务端默认 100）

        返回：
            `{"imports": [...], "count"}`
        """
        resp = await self._http.get("/api/bundles/imports", params={"limit": limit})
        if resp.status_code == 401:
            raise AuthenticationError("Authentication failed")
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        """关闭客户端，释放底层 HTTP 连接"""
        await self._http.aclose()
