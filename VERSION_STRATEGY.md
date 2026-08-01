<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# EvoRule SDK 版本策略

> **核心原则**:SDK 版本号独立于 evorule 核心仓和 evorule-server 仓,按自身节奏演进。

---

## 一、独立性声明

EvoRule SDK 是**独立仓**,版本号不绑定任何其他仓:

| 仓 | 版本 | 关系 |
|---|---|---|
| evorule（核心） | 0.1.1 | 框架核心,Rust crate |
| evorule-server | 0.1.0 | HTTP API 后端 |
| **evorule-sdk** | **0.1.0** | **本文档的主体,独立版本号** |

SDK 版本号反映 **SDK 自身的变化**（新增方法、bug 修复、API 变更），
**不**反映 evorule-server 的版本变化。例如：
- evorule-server 从 0.1.0 升到 0.2.0，如果 API 没有 breaking change，SDK 不需要升 MAJOR
- SDK 新增了一个 helper 方法，即使 evorule-server 没有发新版，SDK 也应该升 MINOR

---

## 二、语义化版本（SemVer 2.0）

### 版本号格式

```
MAJOR.MINOR.PATCH
```

### 升级规则

| 版本段 | 触发条件 | 示例 |
|---|---|---|
| **MAJOR** | SDK API 有 breaking change（方法签名变更、删除方法、行为语义变更） | `NewClient(token)` → `NewClient(config)` |
| **MINOR** | 新增功能（新方法、新端点支持、新可选参数）,向后兼容 | 新增 `Client.Metrics()` 方法 |
| **PATCH** | bug 修复,向后兼容 | 修复 SSE 重连 bug |

### 特殊情况

| 场景 | 处理方式 |
|---|---|
| evorule-server 新增 API 端点,SDK 添加支持 | SDK 升 MINOR |
| evorule-server 删除 API 端点,SDK 移除对应方法 | SDK 升 MAJOR |
| evorule-server 修改 API 响应格式,SDK 适配 | SDK 升 MINOR（如果适配是向后兼容的）或 MAJOR（如果不兼容） |
| 仅修复 SDK 内部 bug,不涉及 server API | SDK 升 PATCH |

---

## 三、各语言 SDK 的版本独立性

**各语言 SDK 可以有不同的版本号。** 它们按各自语言的生态节奏演进。

| 语言 | 版本号 | 发布平台 | 当前状态 |
|---|---|---|---|
| Python | 0.1.0 | PyPI | 完整实现 |
| TypeScript | 0.1.0 | npm | 完整实现 |
| Go | 0.1.0 | Go module | 完整实现 |
| Java | 0.1.0 | Maven Central | 完整实现 |

> 虽然各语言 SDK 可以独立演进,但应尽量保持功能对齐（同一 server API 端点在所有语言 SDK 中都应支持）。

---

## 四、0.x.0 阶段规则

在 1.0.0 之前（当前 0.1.0）:

- **MAJOR=0** 表示"公开 API 尚未稳定"
- breaking change 可以在 MINOR 版本中发生（但仍应尽量减少）
- 每个 MINOR 版本应在 CHANGELOG 中明确标注 breaking change

### 1.0.0 升级条件

- [ ] 四种语言 SDK 功能对齐（覆盖 evorule-server 全部公开 API）
- [ ] 各语言 SDK 测试覆盖率 ≥ 80%
- [ ] API 签名稳定（不再有 breaking change 预期）
- [ ] 各语言 SDK 各有完整 README + 示例
- [ ] 至少 1 个真实使用案例

---

## 五、发布流程

### Python SDK (PyPI)

```bash
cd python
# 1. 更新 pyproject.toml 版本号
# 2. 更新 CHANGELOG.md
# 3. 构建
python -m build
# 4. 发布
twine upload dist/*
```

### TypeScript SDK (npm)

```bash
cd typescript
# 1. 更新 package.json 版本号
# 2. 更新 CHANGELOG.md
# 3. 构建
npm run build
# 4. 发布
npm publish
```

### Go SDK (Go module)

Go module 不需要显式发布,通过 git tag 管理:

```bash
cd go
# 1. 更新 CHANGELOG.md
# 2. 打 tag
git tag v0.1.0
git push origin v0.1.0
```

### Java SDK (Maven Central)

```bash
cd java
# 1. 更新 build.gradle.kts 版本号
# 2. 更新 CHANGELOG.md
# 3. 发布
./gradlew publish
```

---

## 六、与 evorule-server API 的版本映射

SDK 不强制绑定 server 版本,但 CHANGELOG 中应记录"测试通过的最高 server 版本":

```markdown
## [0.1.0] - 2026-08-01

### 测试通过的 evorule-server 版本
- evorule-server 0.1.0（含 B1-B3 安全修复 + N1-N6 + S1-S4）
```

用户可以参考此信息判断 SDK 与 server 的兼容性。
