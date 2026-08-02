# EvoRule Go SDK

> **版本**: 0.1.0
> **协议**: AGPL-3.0-or-later

evorule-server HTTP API 的 Go 客户端 SDK。

## 安装

```bash
go get gitee.com/evo-rule-lab/evorule-sdk/go
```

## 快速开始

```go
package main

import (
    "fmt"
    "gitee.com/evo-rule-lab/evorule-sdk/go/evorule"
)

func main() {
    // 带 Bearer token 认证（evorule-server 非 loopback 部署时必须）
    client := evorule.NewClientWithAuth("http://localhost:18080", "secret123")

    // 创建会话
    session, err := client.CreateSession()
    if err != nil {
        panic(err)
    }
    fmt.Printf("会话 ID: %d\n", session.ID)

    // 提交命令
    err = client.SubmitCommand(session.ID, map[string]interface{}{
        "type": "increment",
        "params": map[string]interface{}{
            "attr":  "x",
            "delta": 1,
        },
    })

    // 查询状态
    state, _ := client.GetState(session.ID)
    fmt.Printf("状态: %s\n", state.Payload)

    // 关闭会话
    client.CloseSession(session.ID)
}
```

## 认证

| 构造函数 | 用途 |
|---|---|
| `NewClient(baseURL)` | 无认证,仅适用于 loopback 开发环境 |
| `NewClientWithAuth(baseURL, token)` | Bearer token 认证,生产环境必须 |

> evorule-server 在非 loopback 地址上必须配置认证 token（B3 fail-closed），
> 此时必须使用 `NewClientWithAuth`。

## API 方法

### 会话管理

| 方法 | 端点 |
|---|---|
| `CreateSession()` | `POST /api/sessions` |
| `GetSession(id)` | `GET /api/sessions/{id}` |
| `ListSessions()` | `GET /api/sessions` |
| `CloseSession(id)` | `DELETE /api/sessions/{id}` |
| `ForkSession(parentID, version)` | `POST /api/sessions/fork/{parent_id}?version=X` |

### 命令与状态

| 方法 | 端点 |
|---|---|
| `SubmitCommand(id, instruction)` | `POST /api/sessions/{id}/command` |
| `GetState(id)` | `GET /api/sessions/{id}/state` |
| `Interrupt(id)` | `POST /api/sessions/{id}/interrupt` |
| `SubmitIoResponse(id, requestID, result, err)` | `POST /api/sessions/{id}/io_response` |

### 时间机器

| 方法 | 端点 |
|---|---|
| `GetReplay(id)` | `GET /api/sessions/{id}/replay` |
| `Rewind(id, version)` | `GET /api/sessions/{id}/rewind?version=X` |
| `Diff(id, from, to)` | `GET /api/sessions/{id}/diff?a={from}&b={to}` |
| `SessionHistory(id)` | `GET /api/sessions/{id}/history` |

### 审计

| 方法 | 端点 |
|---|---|
| `SessionAudit(id)` | `GET /api/sessions/{id}/audit` |
| `SessionAuditVerify(id)` | `GET /api/sessions/{id}/audit/verify` |

### 调试

| 方法 | 端点 |
|---|---|
| `DebugPhase(id)` | `GET /api/sessions/{id}/debug/phase` |
| `DebugQueue(id)` | `GET /api/sessions/{id}/debug/queue` |
| `DebugPendingIo(id)` | `GET /api/sessions/{id}/debug/pending_io` |

### 共享 Fact

| 方法 | 端点 |
|---|---|
| `GetSharedFacts(prefix)` | `GET /api/shared/facts` |
| `SharedFactSource(factID)` | `GET /api/shared/facts/{id}/source` |
| `SharedFactUsedBy(factID)` | `GET /api/shared/facts/{id}/used_by` |

### 集群协作

| 方法 | 端点 |
|---|---|
| `SessionJoin(id, targetID, direction)` | `POST /api/sessions/{id}/join` |
| `SessionLeave(id)` | `POST /api/sessions/{id}/leave` |
| `SessionClusterStatus(id)` | `GET /api/sessions/{id}/cluster` |

### 健康检查

| 方法 | 端点 |
|---|---|
| `Liveness()` | `GET /api/health/liveness` |
| `Readiness()` | `GET /api/health/readiness` |

## 已知限制

- ❌ 不支持 SSE 事件流（`/api/sessions/{id}/events`）— 计划在 v0.2.0 补齐
- ❌ 无单元测试 — 计划在 v0.1.x 补齐
