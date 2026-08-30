<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: Apache-2.0
-->

# EvoRule SDK 更新日志

所有对 EvoRule SDK 仓的重大更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) v1.0,
本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) v2.0。

---

## [0.1.0] - 2026-08-01

**evorule-sdk 仓首次建立** — 多语言客户端 SDK 集合。

### 🆕 新增

- **Python SDK**（`python/`）— httpx + async，6 源文件 + 6 测试文件
- **TypeScript SDK**（`typescript/`）— fetch + EventSource，5 源文件 + E2E 测试
- **Go SDK**（`go/`）— net/http，单文件 680 行 + 示例
- **Java SDK**（`java/`）— OkHttp + Gson，14 源文件 + E2E 测试
- **Web Debugger**（`web/`）— 浏览器调试工具（单 HTML 文件）
- 各语言 SDK 均支持 Bearer token 认证
- 独立版本策略（VERSION_STRATEGY.md）
- monorepo + 各语言独立 tag 策略

### 📚 文档

- 各语言 SDK 各有 README + CHANGELOG
- API 端点覆盖矩阵（DOCS_INDEX.md）

### 🔄 变更

- **许可证变更**:SDK 代码从 AGPL-3.0-or-later 变更为 **Apache-2.0**
  - 许可分层策略:SDK 作为 evorule-server HTTP API 的客户端薄封装,采用宽松许可降低下游集成摩擦;
    evorule-server 本体维持 AGPL-3.0 + 商业双许可不变
  - 覆盖:根与各语言 LICENSE、全部源文件 SPDX 头、包元数据(pyproject/package.json/build.gradle.kts)、
    validate-license.ps1 检查逻辑、全部 L1 文档
  - CONTRIBUTING 新增 CLA 条款(为未来商业双许可保留权利基础)

### 🛠 治理基础设施

- **首次推送前治理加固**
  - 从 git 移除 4 个已跟踪的 `.class` 构建产物（根因：.gitignore 缺少 `target/` 规则）
  - 完善 `.gitignore`：添加 `target/`、`.env`、`.trae/`、`wendang/`、`*.log` 等规则
  - 清理所有文档中的兄弟仓提及、agent 身份泄露、内部代号
  - 删除 `ROADMAP.md`
  - 新增验证脚本套件（validate-version/changelog/license/release/all）
  - 新增文档安全检查工具（check_doc_safety.py）
  - 新增 CI 配置（.github/workflows/ci.yml + .gitee-ci/validate.yml）
  - 新增发布流程文档（docs/RELEASE_PROCESS.md）
  - 新增根 CHANGELOG.md（本文件）
