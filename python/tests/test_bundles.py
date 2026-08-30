# SPDX-License-Identifier: MIT
"""evorule.client 快照包（bundle）API 单元测试（Mock 版）

不依赖 evorule-server：成功路径断言响应字段与请求体，400 路径断言
服务端 error 字段透传（不静默）。校验口径本身由服务端保证，此处不测。
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from evorule import AuthenticationError, EvoruleClient, EvoruleError


# ======================================================================
# 辅助函数
# ======================================================================


def _make_mock_response(
    status_code: int = 200,
    json_data: dict | list | None = None,
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}

    def raise_for_status() -> None:
        if status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {status_code}",
                request=MagicMock(),
                response=resp,
            )

    resp.raise_for_status = raise_for_status
    return resp


def _make_mock_client(
    post_response: MagicMock | None = None,
    get_response: MagicMock | None = None,
) -> tuple[EvoruleClient, MagicMock]:
    client = EvoruleClient("http://localhost:18080")
    mock_http = MagicMock()
    mock_http.post = AsyncMock(return_value=post_response)
    mock_http.get = AsyncMock(return_value=get_response)
    client._http = mock_http  # type: ignore[assignment]
    return client, mock_http


def _sample_bundle() -> dict:
    """最小合法 bundle fixture（set 元指令，满足 6 元指令枚举）"""
    return {
        "bundle_schema_version": "1.0",
        "bundle_id": "bundle-demo-v1",
        "dataset": {"id": "ds-demo", "name": "demo"},
        "entries": [
            {
                "entry_id": "rule-001-abc",
                "rule_id": "rule.001",
                "source_version": "v1",
                "rule_body": {
                    "kind": "rule",
                    "id": "rule.001",
                    "transform": [
                        {"type": "set", "target": "x", "value": 1}
                    ],
                },
            }
        ],
    }


# ======================================================================
# import_bundle
# ======================================================================


class TestImportBundle:
    @pytest.mark.asyncio
    async def test_import_success(self):
        client, mock_http = _make_mock_client()
        mock_http.post.return_value = _make_mock_response(
            201,
            {
                "imported": True,
                "bundle_id": "bundle-demo-v1",
                "dataset_id": "ds-demo",
                "activated_version": "v1",
                "entry_count": 1,
                "missing_services": [],
            },
        )
        result = await client.import_bundle(_sample_bundle())
        assert result["imported"] is True
        assert result["bundle_id"] == "bundle-demo-v1"
        assert result["entry_count"] == 1
        # 请求体必须是 {"bundle": <bundle>} 包裹形态
        mock_http.post.assert_awaited_once_with(
            "/api/bundles/import", json={"bundle": _sample_bundle()}
        )

    @pytest.mark.asyncio
    async def test_import_400_surfaces_server_error(self):
        client, mock_http = _make_mock_client()
        mock_http.post.return_value = _make_mock_response(
            400, {"error": "entry rule.001: unknown service svc.x", "imported": False}
        )
        with pytest.raises(EvoruleError) as exc_info:
            await client.import_bundle(_sample_bundle())
        # 服务端 error 字段必须透传，不得吞掉
        assert "unknown service svc.x" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_import_401_raises_auth_error(self):
        client, mock_http = _make_mock_client()
        mock_http.post.return_value = _make_mock_response(401, {})
        with pytest.raises(AuthenticationError):
            await client.import_bundle(_sample_bundle())


# ======================================================================
# dry_run_import
# ======================================================================


class TestDryRunImport:
    @pytest.mark.asyncio
    async def test_dry_run_success(self):
        client, mock_http = _make_mock_client()
        mock_http.post.return_value = _make_mock_response(
            200,
            {
                "valid": True,
                "bundle_id": "bundle-demo-v1",
                "dataset_id": "ds-demo",
                "source_version": "v1",
                "selection_mode": "Pinned",
                "resolved_version": "v1",
                "entry_count": 1,
                "verdict": "Accept",
                "missing_services": [],
            },
        )
        result = await client.dry_run_import(_sample_bundle())
        assert result["valid"] is True
        assert result["verdict"] == "Accept"
        mock_http.post.assert_awaited_once_with(
            "/api/bundles/import/dry-run", json={"bundle": _sample_bundle()}
        )

    @pytest.mark.asyncio
    async def test_dry_run_400_surfaces_server_error(self):
        client, mock_http = _make_mock_client()
        mock_http.post.return_value = _make_mock_response(
            400, {"error": "content_hash mismatch", "valid": False}
        )
        with pytest.raises(EvoruleError) as exc_info:
            await client.dry_run_import(_sample_bundle())
        assert "content_hash mismatch" in str(exc_info.value)


# ======================================================================
# list_active_bundles / list_bundle_imports
# ======================================================================


class TestBundleQueries:
    @pytest.mark.asyncio
    async def test_active_bundles_success(self):
        client, mock_http = _make_mock_client()
        mock_http.get.return_value = _make_mock_response(
            200,
            {
                "bundles": [
                    {
                        "bundle_id": "bundle-demo-v1",
                        "dataset_id": "ds-demo",
                        "source_version": "v1",
                        "selection_mode": "pinned",
                        "content_hash": "blake3:abc",
                        "entry_count": 1,
                    }
                ],
                "count": 1,
            },
        )
        result = await client.list_active_bundles()
        assert result["count"] == 1
        assert result["bundles"][0]["dataset_id"] == "ds-demo"
        mock_http.get.assert_awaited_once_with("/api/bundles/active")

    @pytest.mark.asyncio
    async def test_bundle_imports_limit_param(self):
        client, mock_http = _make_mock_client()
        mock_http.get.return_value = _make_mock_response(200, {"imports": [], "count": 0})
        result = await client.list_bundle_imports(limit=50)
        assert result["count"] == 0
        mock_http.get.assert_awaited_once_with("/api/bundles/imports", params={"limit": 50})
