<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# EvoRule SDK — 声明

**版权所有 (c) 2026 EvoRule Project**

本项目（`evorule-sdk`）是 EvoRule 框架的多语言客户端 SDK 集合，包含：
- Python SDK（`python/`）
- TypeScript SDK（`typescript/`）
- Go SDK（`go/`）
- Java SDK（`java/`）
- Web Debugger（`web/`）

## 协议

**本仓（EvoRule SDK）所有代码采用 Apache-2.0 协议。** 详见 [LICENSE](LICENSE)。

> 许可分层说明:SDK 是 evorule-server HTTP API 的客户端薄封装,独立采用宽松的
> Apache-2.0 许可,应用集成 SDK 不触发服务端协议义务;evorule-server 本体采用
> AGPL-3.0 + 商业双许可(以 server 仓 LICENSE 为准)。

## 依赖说明

SDK 通过 HTTP API 与 [evorule-server](https://gitee.com/evo-rule-lab/evorule-server) 通信。

| 依赖 | 来源 | 说明 |
|---|---|---|
| evorule-server | [evorule-server 仓](https://gitee.com/evo-rule-lab/evorule-server) | HTTP API 后端，SDK 的运行期依赖 |

## 各语言 SDK 第三方依赖

### Python SDK
| 依赖 | 协议 | 用途 |
|---|---|---|
| `httpx` | BSD-3-Clause | HTTP 客户端（async） |
| `websockets` | BSD-3-Clause | SSE/WebSocket 事件流 |
| `pydantic` | MIT | 数据模型校验 |

### TypeScript SDK
| 依赖 | 协议 | 用途 |
|---|---|---|
| `fetch` (浏览器原生) | - | HTTP 请求 |
| `EventSource` (浏览器原生) | - | SSE 事件流 |

### Go SDK
无第三方依赖，仅使用 Go 标准库。

### Java SDK
| 依赖 | 协议 | 用途 |
|---|---|---|
| `okhttp` | Apache-2.0 | HTTP 客户端 |
| `gson` | Apache-2.0 | JSON 序列化 |
| `junit` | Eclipse Public License | 测试框架 |

## 联系信息

- **项目**: EvoRule SDK — 多语言客户端 SDK
- **作者**: EvoRule Project
- **邮箱**: <evorulelab@gmail.com>
- **组织**: [EvoRule Lab](https://gitee.com/evo-rule-lab)
- **Gitee**: <https://gitee.com/evo-rule-lab/evorule-sdk>
