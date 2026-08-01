<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# 贡献指南

感谢您对 EvoRule SDK 项目的兴趣!本文档介绍如何为项目做贡献。

## 行为准则

参与本项目即表示您同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 项目结构

```
evorule-sdk/
├── python/          # Python SDK (httpx + async)
├── typescript/      # TypeScript SDK (fetch + EventSource)
├── go/              # Go SDK (net/http)
├── java/            # Java SDK (OkHttp + Gson)
├── web/             # Web 调试工具
├── LICENSE          # AGPL-3.0-or-later
├── NOTICE.md        # 版权声明
├── CONTRIBUTING.md  # 本文件
└── README.md        # 项目总览
```

## 开发环境

### Python SDK

```bash
cd python
pip install -e ".[dev]"
pytest
```

### TypeScript SDK

```bash
cd typescript
npm install
npm test
```

### Go SDK

```bash
cd go
go test ./...
```

### Java SDK

```bash
cd java
./gradlew test
```

## 提交 Issue

- Bug 报告:描述复现步骤、预期行为、实际行为、SDK 版本、语言
- 功能请求:描述使用场景和期望的 API 设计

## 提交 Pull Request

1. Fork 本仓
2. 创建分支:`git checkout -b fix/python-sse-reconnect`
3. 编写代码,确保测试通过
4. 提交 PR,描述变更内容和动机

### PR 检查清单

- [ ] 代码通过现有测试
- [ ] 新功能有对应测试
- [ ] 不引入新的第三方依赖(除非必要,且在 PR 中说明)
- [ ] 不将认证 token 硬编码或提交到仓库
- [ ] 遵循各语言惯用风格(PEP 8 / ESLint / gofmt / Google Java Style)

## 版本策略

SDK 采用**独立版本号**,不跟随 evorule 或 evorule-server。详见 [VERSION_STRATEGY.md](VERSION_STRATEGY.md)。

## 协议

所有贡献在 [AGPL-3.0-or-later](LICENSE) 下发布。提交 PR 即表示您同意在此协议下发布您的贡献。

---

_如有疑问,请提交 Issue 或联系 <evorulelab@gmail.com>。_
