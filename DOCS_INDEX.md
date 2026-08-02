<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# EvoRule SDK 文档总索引

> **最后更新**:2026-08-01
> **版本对齐**:SDK v0.1.0

---

## 一、仓级文档

| 文档 | 用途 |
|:---|:---|
| [README.md](README.md) | 项目总览 — 各语言 SDK 状态、快速链接 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 — 开发环境、提 PR 检查清单 |
| [SECURITY.md](SECURITY.md) | 安全政策 — Token 处理、HTTPS 强制、依赖审计 |
| [VERSION_STRATEGY.md](VERSION_STRATEGY.md) | 版本策略 — 独立版本号、SemVer 规则、发布流程 |
| [CHANGELOG.md](CHANGELOG.md) | 更新日志 — 仓级变更记录（各语言变更见各自子目录 CHANGELOG） |

### 法律文档

| 文档 | 用途 |
|:---|:---|
| [LICENSE](LICENSE) | AGPL-3.0-or-later 协议全文 |
| [NOTICE.md](NOTICE.md) | 版权声明 + 第三方依赖许可 |
| [AUTHORS.md](AUTHORS.md) | 作者列表 |
| [TRADEMARK.md](TRADEMARK.md) | 商标政策 |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | 行为准则（Contributor Covenant 2.1） |

---

## 二、开发文档（`docs/` 目录）

| 文档 | 说明 |
|:---|:---|
| [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) | 发布流程 — 发布前就绪检查、各语言独立 tag、包管理器发布 |

## 三、各语言 SDK 文档

### Python SDK (`python/`)

| 文档 | 用途 |
|:---|:---|
| [python/README.md](python/README.md) | Python SDK 使用文档 |
| [python/CHANGELOG.md](python/CHANGELOG.md) | Python SDK 更新日志 |
| [python/pyproject.toml](python/pyproject.toml) | 包配置 + 依赖 |

### TypeScript SDK (`typescript/`)

| 文档 | 用途 |
|:---|:---|
| [typescript/README.md](typescript/README.md) | TypeScript SDK 使用文档 |
| [typescript/CHANGELOG.md](typescript/CHANGELOG.md) | TypeScript SDK 更新日志 |
| [typescript/package.json](typescript/package.json) | 包配置 + 依赖 |

### Go SDK (`go/`)

| 文档 | 用途 |
|:---|:---|
| [go/evorule/client.go](go/evorule/client.go) | Go SDK 源码（单文件,含 godoc 注释） |
| [go/examples/quickstart.go](go/examples/quickstart.go) | 快速入门示例 |
| [go/go.mod](go/go.mod) | Go module 定义 |

### Java SDK (`java/`)

| 文档 | 用途 |
|:---|:---|
| [java/README.md](java/README.md) | Java SDK 使用文档 |
| [java/CHANGELOG.md](java/CHANGELOG.md) | Java SDK 更新日志 |
| [java/build.gradle.kts](java/build.gradle.kts) | Gradle 构建配置 |

### Web Debugger (`web/`)

| 文档 | 用途 |
|:---|:---|
| [web/debugger.html](web/debugger.html) | 浏览器调试工具（单 HTML 文件） |

---

## 四、API 端点覆盖矩阵

SDK 覆盖的 evorule-server API 端点（截至 2026-08-01 审计）：

| 端点 | Python | TypeScript | Go | Java |
|:---|:---:|:---:|:---:|:---:|
| `/api/sessions` CRUD | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/command` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/state` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/events` (SSE) | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/replay` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/rewind` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/diff` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/interrupt` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/io_response` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/payload` | ✅ | ✅ | ❌ | ✅ |
| `/api/sessions/{id}/audit` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/audit/verify` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/history` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/facts` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/debug/*` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/used_at_startup` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/finished` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/causal_depth` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/invariants` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/pending_io_count` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/step` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/{id}/snapshot` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/fork/{id}` | ✅ | ✅ | ✅ | ✅ |
| `/api/sessions/from/{id}` | ✅ | ❌ | ✅ | ✅ |
| `/api/sessions/{id}/join` / `/leave` / `/cluster` | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `/api/shared/facts` | ✅ | ✅ | ✅ | ✅ |
| `/api/shared/facts/{id}/source` | ✅ | ✅ | ✅ | ✅ |
| `/api/shared/facts/{id}/used_by` | ✅ | ✅ | ✅ | ✅ |
| `/api/health/*` | ✅ | ✅ | ✅ | ✅ |
| `/api/rules/validate` | ❌ | ❌ | ❌ | ❌ |
| `/api/rules/reload` | ❌ | ❌ | ❌ | ❌ |
| `/api/sessions/{id}/audit/export` | ❌ | ❌ | ❌ | ❌ |
| `/api/sessions/{id}/audit/import` | ❌ | ❌ | ❌ | ❌ |
| `/api/sessions/{id}/audit/auto_verify` | ❌ | ❌ | ❌ | ❌ |
| `/metrics` | ❌ | ❌ | ❌ | ❌ |
| **Bearer token 认证** | ✅ | ✅ | ✅ | ✅ |

> **⚠️ 说明**:`/join`/`/leave`/`/cluster` 端点已废弃，各 SDK 保留方法但标注 `@Deprecated`，调用将返回 404。
>
> **未覆盖端点**:标记 ❌ 的端点为各 SDK 均未实现，包括规则管理（`/api/rules/validate`、`/api/rules/reload`）、审计链导入导出（`/audit/export`、`/audit/import`、`/audit/auto_verify`）、Prometheus 指标（`/metrics`）。这些端点多为运维/批量操作场景，按需在后续版本补充。

---

## 五、文档维护规则

1. **加新文档必登索引**:新增 README 或重要文档时,必须在本 DOCS_INDEX 登记
2. **版本号单一真相源**:各 SDK 的版本号以各自构建文件为准（pyproject.toml / package.json / go.mod / build.gradle.kts）
3. **文档被取代必标废弃**:新版文档生效时,旧版顶部加 `[已废弃]` 横幅
4. **API 覆盖矩阵同步**:新增端点支持时,更新第三节覆盖矩阵
