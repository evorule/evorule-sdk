<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# EvoRule SDK 路线图

> **最后更新**:2026-08-01
> **当前版本**:v0.1.0
> **版本策略**:见 [VERSION_STRATEGY.md](VERSION_STRATEGY.md)

---

## 概述

EvoRule SDK 是 EvoRule 框架的多语言客户端 SDK 集合。本路线图描述从当前基线到 v1.0 的演进路径。

**核心原则**:SDK 版本独立于 evorule 和 evorule-server,按自身节奏演进。

---

## v0.1.x — 基线期（当前）

### ✅ 已完成

| 里程碑 | 状态 |
|---|---|
| Python SDK 完整实现 | ✅ 6 源文件 + 6 测试文件 |
| TypeScript SDK 完整实现 | ✅ 5 源文件 + 1 E2E 测试 |
| Go SDK 完整实现 | ✅ 1 源文件（680 行）+ 示例 |
| Java SDK 完整实现 | ✅ 14 源文件 + 1 E2E 测试 |
| Go SDK 补 Bearer token 认证 | ✅ `NewClientWithAuth` + 全方法接入 |
| 治理文档清理 | ✅ 移除 33 个冗余文件 + 集中到根目录 |
| 独立版本策略 | ✅ VERSION_STRATEGY.md |

### 🔲 待办

| 里程碑 | 优先级 | 说明 |
|---|---|---|
| Go SDK 补测试 | HIGH | 当前无测试,需补单元测试 + E2E 测试 |
| Go SDK 补 SSE 事件流支持 | HIGH | 唯一缺失的核心功能（其他语言都有） |
| 各 SDK CHANGELOG 对齐 | MEDIUM | 统一格式,记录 v0.1.0 基线 |
| Web Debugger 完善 | LOW | 当前是单 HTML 文件,考虑集成到 SDK 或移到 application 仓 |

---

## v0.2.0 — 功能增强

**目标**:补齐功能差距,增强可用性。

### 计划项

| 里程碑 | 说明 |
|---|---|
| Go SDK SSE 支持 | 补齐唯一缺失的核心功能 |
| 自动重连 | SSE 连接断开后自动重连 + Last-Event-ID 恢复 |
| TypeScript SDK Node.js 兼容 | 当前依赖浏览器 fetch/EventSource,补 Node.js 兼容层 |
| 批量操作 API | 批量创建 session、批量提交 command |
| 类型生成 | 从 evorule-server OpenAPI spec 自动生成类型定义 |
| Python SDK async/sync 双模式 | 当前仅 async,补 sync 封装 |

---

## v0.3.0 — 发布准备

**目标**:准备首次公开发布到各语言包管理器。

### 计划项

| 里程碑 | 说明 |
|---|---|
| PyPI 发布 | Python SDK 发布到 PyPI |
| npm 发布 | TypeScript SDK 发布到 npm |
| Maven Central 发布 | Java SDK 发布到 Maven Central |
| Go module 稳定 | Go SDK 打 v0.3.0 tag |
| 文档网站 | 各语言 SDK API 参考文档 |
| 示例项目 | 各语言完整示例项目 |

---

## v1.0.0 — 稳定版

**前置条件**（见 [VERSION_STRATEGY.md §四](VERSION_STRATEGY.md)）:

- [ ] 四种语言 SDK 功能对齐
- [ ] 各语言 SDK 测试覆盖率 ≥ 80%
- [ ] API 签名稳定
- [ ] 各语言 SDK 各有完整 README + 示例
- [ ] 至少 1 个真实使用案例

---

## 版本节奏建议

| 阶段 | 频率 |
|---|---|
| v0.1.x | 2-4 周/版本 |
| v0.2.0 - v0.3.0 | 4-6 周/版本 |
| v1.0.0 | 功能对齐 + 测试覆盖后发布 |
| v1.0.0 之后 | 6-8 周/版本,严格 semver |

---

*本路线图反映当前计划,可能根据用户反馈和实际情况调整。*
