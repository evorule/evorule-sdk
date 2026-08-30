<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: Apache-2.0
-->

# EvoRule SDK 版本策略

> **核心原则**:SDK 版本号独立,按自身节奏演进。

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

### 仓库结构：monorepo + 独立 tag

**决策（2026-08-01）**：evorule-sdk 采用 **monorepo + 各语言独立 tag** 策略。

所有语言的 SDK 源码统一存放在 `evorule-sdk` 仓库的子目录中，但发布时各语言使用独立的 git tag 和版本号。

```
evorule-sdk/                        # 一个 git 仓库（monorepo）
├── go/          → tag: go-v0.1.0    → go get gitee.com/evo-rule-lab/evorule-sdk/go@go-v0.1.0
├── python/      → tag: python-v0.1.0 → pip install evorule==0.1.0
├── typescript/  → tag: ts-v0.1.0    → npm publish evorule@0.1.0
├── java/        → tag: java-v0.1.0  → maven publish com.evorule:evorule-client:0.1.0
├── web/                           → 前端辅助工具
├── DOCS_INDEX.md                   # 跨语言 API 端点覆盖矩阵（monorepo 独有优势）
└── VERSION_STRATEGY.md             # 本文档
```

#### tag 命名规则

| 语言 | tag 格式 | 示例 |
|---|---|---|
| Go | `go-v{MAJOR}.{MINOR}.{PATCH}` | `go-v0.1.0` |
| Python | `python-v{MAJOR}.{MINOR}.{PATCH}` | `python-v0.1.0` |
| TypeScript | `ts-v{MAJOR}.{MINOR}.{PATCH}` | `ts-v0.1.0` |
| Java | `java-v{MAJOR}.{MINOR}.{PATCH}` | `java-v0.1.0` |

> tag 前缀（`go-`/`python-`/`ts-`/`java-`）确保各语言版本号互不冲突，可独立演进。

#### 为什么选择 monorepo

| 理由 | 说明 |
|---|---|
| **跨语言一致性** | 一次 PR 同时修改所有 SDK 的字段名/端点变更（如 2026-08-01 审计修复了 10 个跨语言 BUG，monorepo 让这成为一次提交） |
| **版本对齐可审计** | DOCS_INDEX.md 端点覆盖矩阵只有在 monorepo 中才能有效维护 |
| **维护成本低** | 一套 CI/issue/PR 管理所有语言，不必维护 4-5 个仓库 |
| **各语言版本仍独立** | 独立 tag 满足"各语言按自身节奏演进"的要求，Go 可发 `go-v0.2.0` 而 Python 仍是 `python-v0.1.0` |

#### 何时考虑拆分到独立仓库

出现以下任一信号时，应评估是否拆分：

- [ ] 某语言的独立 contributor 超过 5 人，PR 噪音影响其他语言
- [ ] 某语言的版本节奏明显与其他语言脱节（如 Go 已到 1.0，Python 还在 0.3）
- [ ] 某语言需要独立的 security policy / release cycle
- [ ] 各语言 SDK 代码量超过 monorepo 的可维护阈值

> 拆分时应将 monorepo 子目录转为独立仓库，保留 git 历史（`git subtree split`）。

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
# 4. 发布到 PyPI
twine upload dist/*
# 5. 打 tag（monorepo 独立 tag 策略）
git tag python-v0.1.0
git push origin python-v0.1.0
```

### TypeScript SDK (npm)

```bash
cd typescript
# 1. 更新 package.json 版本号
# 2. 更新 CHANGELOG.md
# 3. 构建
npm run build
# 4. 发布到 npm
npm publish
# 5. 打 tag（monorepo 独立 tag 策略）
git tag ts-v0.1.0
git push origin ts-v0.1.0
```

### Go SDK (Go module)

Go module 不需要显式发布,通过 git tag 管理:

```bash
cd go
# 1. 更新 CHANGELOG.md
# 2. 打 tag（注意 go- 前缀，与 monorepo 独立 tag 策略一致）
git tag go-v0.1.0
git push origin go-v0.1.0
```

### Java SDK (Maven Central)

```bash
cd java
# 1. 更新 build.gradle.kts 版本号
# 2. 更新 CHANGELOG.md
# 3. 发布到 Maven Central
./gradlew publish
# 4. 打 tag（monorepo 独立 tag 策略）
git tag java-v0.1.0
git push origin java-v0.1.0
```

---

## 六、与 evorule-server API 的版本映射

SDK 不强制绑定 server 版本,但 CHANGELOG 中应记录"测试通过的最高 server 版本":

```markdown
## [0.1.0] - 2026-08-01

### 测试通过的 evorule-server 版本
- evorule-server 0.1.0
```

用户可以参考此信息判断 SDK 与 server 的兼容性。
