<!--
  Copyright 2026 EvoRule Project

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# 安全政策

## 报告漏洞

如果您发现安全漏洞,请**不要**在公开 Issue 中提交。

通过 <evorulelab@gmail.com> 私密报告,主题加 `[SECURITY]`。我们将在 48 小时内确认收到,并在 7 天内给出初步评估。

## SDK 特有安全关注点

### Bearer Token 处理

SDK 需要持有 evorule-server 的认证 token。注意事项:

- **不要**将 token 硬编码在源代码中
- **不要**将 token 提交到 Git 仓库
- **不要**将 token 记录在日志中
- 使用环境变量或安全凭据管理服务传递 token
- token 在传输时必须通过 HTTPS

### 各语言的 Token 安全建议

| 语言 | 建议 |
|---|---|
| Python | 使用 `os.environ["EVORULE_AUTH_TOKEN"]`，不要写入配置文件 |
| TypeScript | 使用 `process.env.EVORULE_AUTH_TOKEN`，不要写入前端代码 |
| Go | 使用 `os.Getenv("EVORULE_AUTH_TOKEN")` |
| Java | 使用 `System.getenv("EVORULE_AUTH_TOKEN")` |

### HTTPS 强制

生产环境中,SDK 必须通过 HTTPS 连接 evorule-server:

```
✅ https://api.example.com:18080
❌ http://api.example.com:18080  (明文传输,token 可被中间人截获)
```

> loopback 地址（`http://localhost:18080`）例外,仅用于本地开发。

## 依赖安全

SDK 依赖的第三方库如有已知漏洞,请报告。我们将及时升级。

| 语言 | 依赖审计命令 |
|---|---|
| Python | `pip-audit` 或 `safety check` |
| TypeScript | `npm audit` |
| Go | `govulncheck ./...` |
| Java | `gradle dependencyCheck` |

## 联系信息

- **安全报告邮箱**:<evorulelab@gmail.com>
- **PGP 公钥**:（后续补充）
- **响应时间**:48 小时内确认,7 天内初步评估

---

*本安全政策与 [evorule-server 安全政策](https://gitee.com/evo-rule-lab/evorule-server/blob/main/SECURITY.md)配合使用。*
