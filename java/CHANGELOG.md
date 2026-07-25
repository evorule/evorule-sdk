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
