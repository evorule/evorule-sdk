# EvoRule Java SDK 更新日志

所有对 EvoRule Java SDK 的重大更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) v1.0,
本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) v2.0。

徽章说明:
- 🆕 新增
- 🔄 变更
- 🐛 修复
- 🗑 弃用
- ⚠️ Breaking Change
- 🔒 安全

---

## [Unreleased]

### 🆕 新增

#### 快照包（DatasetBundle）API — `EvoruleClient`
- **`importBundle(JsonNode)`** — 导入快照包并激活（`POST /api/bundles/import`，导入即激活）
- **`dryRunImport(JsonNode)`** — 导入预检（`POST /api/bundles/import/dry-run`，只跑校验链，不落盘不热重载）
- **`listActiveBundles()`** — 查询当前激活的快照包列表（`GET /api/bundles/active`）
- **`listBundleImports(Integer)`** — 查询导入溯源历史（`GET /api/bundles/imports`）
- 新增模型类：`ImportBundleResponse` / `DryRunImportResponse` / `ActiveBundleInfo` / `ActiveBundlesResponse` / `BundleImportRecord` / `BundleImportsResponse`

> 校验口径零复刻：六项硬校验 + 逐条 Schema 门禁由服务端执行（evorule-bundle SSOT），
> SDK 仅做 HTTP 薄封装；400 时透传服务端 `error` 字段，不静默。
> 单元测试：`BundleApiTest`（7 用例，JDK 内置 HttpServer 模拟服务端）。

## [0.1.0] - 2026-07-20

### 🆕 新增

- **Gradle 构建系统** — 从 Maven 迁移到 Gradle Kotlin DSL，Java 17 目标
- **完整的异常体系** — EvoruleException / AuthenticationException / SessionNotFoundError / SessionClosedError / CommandError
- **数据模型类** — Fact / SharedFact / SessionState / DiffResult / SseEvent
- **EvoruleClient 客户端** — 完整覆盖所有 HTTP API 端点
- **Session 会话类** — 面向对象的会话操作，实现 AutoCloseable
- **SSE 事件流支持** — 通过 streamEvents() / events() 订阅实时事件
- **updatePayload API** — PUT /api/sessions/{id}/payload
- **健康检查端点** — health / liveness / readiness
- **会话分叉** — forkSession()，支持可选 version 参数
- **集群协作** — join / leave / clusterStatus
- **审计与历史** — audit / auditVerify / history
- **共享 Facts** — getSharedFacts / sharedFactSource / sharedFactUsedBy
- **时间旅行** — replay / rewind / diff
- **调试端点** — debugPhase / debugQueue / debugPendingIo
- **I/O 响应** — submitIoResponse
- **执行中断** — interrupt
- **启动引用** — recordUsedAtStartup / getUsedAtStartup
