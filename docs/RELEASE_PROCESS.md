<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# EvoRule SDK 发布流程

> **文档性质**：evorule-sdk 仓的发布操作手册。
> **适用范围**：evorule-sdk 仓（Python / TypeScript / Go / Java 多语言 SDK）。
> **前置文档**：[VERSION_STRATEGY.md](../VERSION_STRATEGY.md) 版本策略。

## 各仓独立发布原则

- **各仓独立发布**，不追求生态版本同步 bump。
- 本仓文档**只管好自己仓的真实情况**，诚实说明。
- 如依赖其他仓，最多说明"依赖哪个仓哪个版本"，不谈论其内部结构、运行方式或发布情况。
- **分支策略**：`main` 为发布分支（tag 从 main 打），`dev/wip` 为开发分支。发布前将 dev/wip 合并到 main。
- **monorepo + 各语言独立 tag**：所有语言 SDK 源码统一存放，但发布时各语言使用独立的 git tag。

---

## 0. 前置条件

发布执行人需具备：

- Gitee 源仓库的 push 权限
- 各语言包管理器账号（PyPI / npm / Maven Central）
- PowerShell 7（`pwsh`）或 Windows PowerShell 5.1
- Python 3.10+（运行 check_doc_safety.py）
- 各语言工具链（Python / Node.js 18+ / Go 1.21+ / Java 17+）

## 1. 发布前就绪检查

### 1.1 代码验证

```bash
# Python SDK
cd python && pytest

# TypeScript SDK
cd typescript && npm install && npm run typecheck && npm test

# Go SDK
cd go && go test ./...

# Java SDK
cd java && ./gradlew test
```

以上 4 项必须全部通过。如有失败，**停止发布**，修复后重新执行。

### 1.2 版本与文档治理验证（一站式）

```powershell
# 发布前就绪检查模式：跳过 tag 检查，允许 CHANGELOG 有 [Unreleased] 段
pwsh scripts/validate-all.ps1 -PreRelease
```

此命令一次性运行 **5 项检查**：

| #   | 检查项                    | 检查内容                                                                 |
| --- | ------------------------- | ------------------------------------------------------------------------ |
| 1   | `validate-version.ps1`    | Python/TypeScript/Java 版本号一致性 + L1 文档版本号字面量扫描           |
| 2   | `validate-changelog.ps1`  | 根 CHANGELOG + 各语言 CHANGELOG 首段版本号 == 构建文件                  |
| 3   | `validate-license.ps1`    | LICENSE 含 AGPL + 所有源文件 SPDX 头                                    |
| 4   | `validate-release.ps1`    | tag 格式校验（`-SkipTagCheck` 跳过 tag 存在性，发布前用）              |
| 5   | `check_doc_safety.py`     | 文档安全 + 交叉引用完整性 + 基调合规（7 类规则）                        |

以上全部通过（exit 0）才可继续。

## 2. 确认文档状态

### 2.1 CHANGELOG

- 确认根 `CHANGELOG.md` 当前版本章节完整
- 确认各语言 `CHANGELOG.md` 首段版本号与构建文件一致
- 填入实际发布日期
- 确认无 `[Unreleased]` 段（发布时转为版本段或清空）
- 历史段只保留本仓事实，不谈论其他仓

### 2.2 README

- 确认版本号与构建文件一致
- 确认"使用风险自负"声明存在
- 确认 API 稳定性诚实声明（"1.0 之前不承诺"）

## 3. 创建 Git Tag（各语言独立）

### 3.1 tag 命名规则

| 语言 | tag 格式 | 示例 |
|:---|:---|:---|
| Go | `go-v{MAJOR}.{MINOR}.{PATCH}` | `go-v0.1.0` |
| Python | `python-v{MAJOR}.{MINOR}.{PATCH}` | `python-v0.1.0` |
| TypeScript | `ts-v{MAJOR}.{MINOR}.{PATCH}` | `ts-v0.1.0` |
| Java | `java-v{MAJOR}.{MINOR}.{PATCH}` | `java-v0.1.0` |

### 3.2 创建 tag

```bash
# 确认工作区干净
git status  # 必须无未提交变更

# 各语言独立打 tag（按需，不是所有语言同时打）
git tag -a python-v0.1.0 -m "EvoRule Python SDK v0.1.0"
git tag -a ts-v0.1.0 -m "EvoRule TypeScript SDK v0.1.0"
git tag -a go-v0.1.0 -m "EvoRule Go SDK v0.1.0"
git tag -a java-v0.1.0 -m "EvoRule Java SDK v0.1.0"
```

## 4. 推送到 Gitee

```bash
# 推送 main 分支 + tags
git push origin main --tags
```

确认 Gitee CI（`.gitee-ci/validate.yml`）通过：

- validate-pr（文档安全 + 版本一致性）✅
- python-test ✅
- typescript-test ✅
- go-test ✅
- java-test ✅

## 5. 各语言发布到包管理器

### Python SDK (PyPI)

```bash
cd python
python -m build
twine upload dist/*
```

### TypeScript SDK (npm)

```bash
cd typescript
npm run build
npm publish
```

### Go SDK (Go module)

Go module 不需要显式发布，通过 git tag 管理：

```bash
# tag 已在 §3 创建并推送
# 用户通过 go get gitee.com/evo-rule-lab/evorule-sdk/go@go-v0.1.0 获取
```

### Java SDK (Maven Central)

```bash
cd java
./gradlew publish
```

## 6. 发布后验证

```powershell
# 严格模式验证（tag 必须存在，CHANGELOG 无 [Unreleased]）
pwsh scripts/validate-all.ps1
```

```bash
# 确认 tag 在仓库存在
git tag -l python-v0.1.0
git ls-remote --tags origin python-v0.1.0

# 确认 CI 全绿
# 访问 Gitee CI 页面确认 validate.yml 通过
```

## 7. 发布后事项

- [ ] 归档本次发布的 CI 日志链接
- [ ] 确认各语言包管理器上的版本可正常安装

---

## 附录：紧急回滚流程

如果发布后发现严重问题需要回滚：

```bash
# 1. 删除对应的语言 tag
git tag -d python-v0.1.0
git push origin :refs/tags/python-v0.1.0

# 2. 在各语言包管理器撤回（如有权限）
# PyPI: pip uninstall evorule（已发布版本无法删除，只能发布新版本）
# npm: npm unpublish @evorule/sdk@0.1.0（72 小时内）
# Maven Central: 无法撤回，发布新版本

# 3. 修复后以新 patch 版本重新发布
```

> **注意**：撤回 tag 是最后手段。仅当源码本身有严重缺陷时才撤回。
