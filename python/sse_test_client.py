# SPDX-License-Identifier: MIT
#!/usr/bin/env python3
"""
evorule-server SSE 事件流测试客户端

通过 httpx 异步连接 evorule-server 的 SSE 端点，验证实时事件推送和长驻模式状态累积。

前置条件：
1. 安装依赖：pip install httpx
2. 启动 evorule-server：
   cargo run --bin evorule-server -- --addr 127.0.0.1:18080 --log-level info

运行：
    python sse_test_client.py
    python sse_test_client.py --url http://127.0.0.1:18080

验证流程：
    1. 创建会话
    2. 异步连接 SSE 事件流
    3. 提交命令 1：increment x=5
    4. 提交命令 2：sequence(increment y=3, increment x=10)
    5. 打印所有 SSE 接收到的事件
    6. 查询最终状态，验证 x=15, y=3
    7. 关闭会话
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any

import httpx


def make_increment_instruction(attr: str, delta: int) -> dict[str, Any]:
    """构造 increment 指令"""
    return {
        "type": "increment",
        "params": {"attr": attr, "delta": delta},
    }


def make_sequence_instruction(instructions: list[dict[str, Any]]) -> dict[str, Any]:
    """构造 sequence 指令（打包多个操作）"""
    return {
        "type": "sequence",
        "params": {"instructions": instructions},
    }


async def _read_sse_stream(
    client: httpx.AsyncClient,
    sse_url: str,
    events: list[dict[str, Any]],
) -> None:
    """内部函数：连接 SSE 端点并持续读取事件流直到连接关闭。"""
    async with client.stream("GET", sse_url) as response:
        response.raise_for_status()
        print(f"  [SSE] 连接已建立: {sse_url}")

        # SSE 流按行读取，事件以空行分隔
        # 每个事件格式: data: <json>\n\n
        async for line in response.aiter_lines():
            if not line:
                # 空行 = 事件分隔符，跳过
                continue

            if line.startswith("data: "):
                data_str = line[len("data: "):]
                try:
                    event = json.loads(data_str)
                    events.append(event)
                    # 打印实时事件
                    event_type = event.get("type", "Unknown")
                    event_id = event.get("id", "?")
                    print(f"  [SSE] 收到事件 #{len(events)}: type={event_type}, id={event_id}")
                except json.JSONDecodeError as e:
                    print(f"  [SSE] JSON 解析失败: {e}, raw={data_str[:100]}")
            elif line.startswith(":"):
                # SSE 注释行（心跳），忽略
                continue
            else:
                # 其他 SSE 字段（event:, id:, retry:），暂不处理
                pass


async def consume_sse_events(
    client: httpx.AsyncClient,
    sse_url: str,
    timeout_seconds: float = 10.0,
) -> list[dict[str, Any]]:
    """
    连接 SSE 端点并消费事件流。

    在 timeout_seconds 内持续读取 SSE 事件，超时后返回已收集的事件列表。
    使用 asyncio.wait_for 实现（兼容 Python 3.10+）。
    """
    events: list[dict[str, Any]] = []

    try:
        await asyncio.wait_for(
            _read_sse_stream(client, sse_url, events),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        # 超时是正常行为，SSE 是长连接
        print(f"  [SSE] 读取超时（{timeout_seconds}s），共收到 {len(events)} 个事件")

    return events


def print_event_details(events: list[dict[str, Any]]) -> None:
    """打印事件详细信息"""
    print(f"\n=== SSE 接收到 {len(events)} 个事件 ===\n")
    for i, event in enumerate(events, 1):
        event_type = event.get("type", "Unknown")
        event_id = event.get("id", 0)

        if event_type == "Command":
            instr_type = event.get("instruction", {}).get("type", "?")
            print(f"  [{i}] Command (id={event_id}) instruction.type={instr_type}")

        elif event_type == "StateTransition":
            payload = event.get("new_payload", {})
            x = payload.get("x", 0)
            y = payload.get("y", 0)
            cause = event.get("cause", "?")
            print(f"  [{i}] StateTransition (id={event_id}, cause={cause}) → payload={{x:{x}, y:{y}}}")

        elif event_type == "Stable":
            snapshot = event.get("final_snapshot", {})
            x = snapshot.get("x", 0)
            y = snapshot.get("y", 0)
            print(f"  [{i}] Stable (id={event_id}) → snapshot={{x:{x}, y:{y}}}")

        elif event_type == "IoRequest":
            io_type = event.get("io_type", "?")
            print(f"  [{i}] IoRequest (id={event_id}) io_type={io_type}")

        elif event_type == "IoResponse":
            print(f"  [{i}] IoResponse (id={event_id})")

        elif event_type == "PayloadUpdate":
            path = event.get("path", "?")
            print(f"  [{i}] PayloadUpdate (id={event_id}) path={path}")

        elif event_type == "Error":
            message = event.get("message", "?")
            print(f"  [{i}] Error (id={event_id}) message={message}")

        else:
            print(f"  [{i}] {event_type} (id={event_id}): {event}")


async def main(server_url: str) -> int:
    """主流程：创建会话 → SSE 订阅 → 提交命令 → 验证状态 → 关闭会话"""

    print("=== evorule-server SSE 事件流测试（Python httpx）===\n")
    print(f"服务器地址: {server_url}")

    async with httpx.AsyncClient(base_url=server_url, timeout=30.0) as client:
        # 1. 健康检查
        print("\n--- 健康检查 ---")
        resp = await client.get("/api/health")
        resp.raise_for_status()
        print(f"GET /api/health -> {resp.json()}")

        # 2. 创建会话
        print("\n--- 创建会话 ---")
        resp = await client.post("/api/sessions")
        resp.raise_for_status()
        session_data = resp.json()
        session_id = session_data["session_id"]
        print(f"POST /api/sessions -> {session_data} (session_id={session_id})")

        # 3. 启动 SSE 事件流订阅（后台任务）
        print("\n--- 启动 SSE 事件流订阅 ---")
        sse_url = f"/api/sessions/{session_id}/events"
        sse_task = asyncio.create_task(
            consume_sse_events(client, sse_url, timeout_seconds=8.0)
        )

        # 等待 SSE 连接建立
        await asyncio.sleep(0.5)

        # 4. 提交命令 1：increment x=5
        print("\n--- 提交命令 1: increment x=5 ---")
        cmd1 = {"instruction": make_increment_instruction("x", 5)}
        resp = await client.post(f"/api/sessions/{session_id}/command", json=cmd1)
        resp.raise_for_status()
        print(f"命令 1 响应: {resp.json()}")

        await asyncio.sleep(0.5)

        # 5. 提交命令 2：sequence(increment y=3, increment x=10)
        print("\n--- 提交命令 2: sequence(increment y=3, increment x=10) ---")
        cmd2 = {
            "instruction": make_sequence_instruction(
                [
                    make_increment_instruction("y", 3),
                    make_increment_instruction("x", 10),
                ]
            )
        }
        resp = await client.post(f"/api/sessions/{session_id}/command", json=cmd2)
        resp.raise_for_status()
        print(f"命令 2 响应: {resp.json()}")

        # 6. 等待 SSE 任务完成
        print("\n--- 等待 SSE 事件流接收完成 ---")
        events = await sse_task

        # 7. 打印事件详情
        print_event_details(events)

        # 8. 查询最终状态
        print("\n--- 查询最终状态 ---")
        resp = await client.get(f"/api/sessions/{session_id}/state")
        resp.raise_for_status()
        state = resp.json()
        print(f"最终状态: {json.dumps(state, ensure_ascii=False)}")

        x = state.get("payload", {}).get("x", 0)
        y = state.get("payload", {}).get("y", 0)
        print(f"\n验证: x={x} (期望 5+10=15), y={y} (期望 3)")

        if x == 15 and y == 3:
            print("\n✅ SSE 事件流验证通过！长驻模式状态累积正确。")
            success = True
        else:
            print("\n❌ 状态验证失败！")
            success = False

        # 9. 关闭会话
        print("\n--- 关闭会话 ---")
        resp = await client.delete(f"/api/sessions/{session_id}")
        resp.raise_for_status()
        print(f"关闭响应: {resp.json()}")

        print("\n=== 测试完成 ===")
        return 0 if success else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="evorule-server SSE 事件流测试客户端"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("EVORULE_URL", "http://127.0.0.1:18080"),
        help="evorule-server 地址（默认: http://127.0.0.1:18080，环境变量: EVORULE_URL）",
    )
    args = parser.parse_args()

    sys.exit(asyncio.run(main(args.url)))
