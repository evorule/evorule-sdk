# EvoRule SDK

> **版本**: v0.1.0
> **协议**: AGPL-3.0-or-later
> **版本策略**: [独立版本号,不跟随其他仓](VERSION_STRATEGY.md)

EvoRule 框架的多语言客户端 SDK 集合。

通过 HTTP API 与 [evorule-server](https://gitee.com/evo-rule-lab/evorule-server) 通信,
提供会话管理、命令提交、状态查询、SSE 事件流、时间机器等能力的客户端封装。

## SDK 状态

| 语言 | 状态 | 版本 | 认证支持 | 测试 |
|------|------|------|:--------:|:----:|
| [Python](python/) | ✅ 完整实现 | 0.1.0 | ✅ | 6 测试文件 |
| [TypeScript](typescript/) | ✅ 完整实现 | 0.1.0 | ✅ | E2E 测试 |
| [Go](go/) | ✅ 完整实现 | 0.1.0 | ✅ | 待补 |
| [Java](java/) | ✅ 完整实现 | 0.1.0 | ✅ | E2E 测试 |
| [Web Debugger](web/) | 🛠 调试工具 | - | - | - |

## 快速开始

### Python

```python
from evorule import EvoruleClient

client = EvoruleClient("http://localhost:18080", token="secret123")
session = await client.create_session()
```

### TypeScript

```typescript
import { EvoruleClient } from "evorule";

const client = new EvoruleClient("http://localhost:18080", { token: "secret123" });
const session = await client.createSession();
```

### Go

```go
import "github.com/evorule/go-sdk/evorule"

client := evorule.NewClientWithAuth("http://localhost:18080", "secret123")
session, err := client.CreateSession()
```

### Java

```java
import com.evorule.EvoruleClient;

EvoruleClient client = new EvoruleClient("http://localhost:18080", "secret123");
Session session = client.createSession();
```

## 文档

- [文档总索引](DOCS_INDEX.md)
- [版本策略](VERSION_STRATEGY.md)
- [路线图](ROADMAP.md)
- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

## 架构定位

EvoRule 生态分为以下独立仓:

| 仓 | 定位 | 与 SDK 的关系 |
|---|---|---|
| [evorule](https://gitee.com/evo-rule-lab/evorule) | 框架核心（Rust） | SDK 不依赖核心 crate |
| [evorule-server](https://gitee.com/evo-rule-lab/evorule-server) | HTTP API 后端 | SDK 的运行期依赖 |
| **evorule-sdk**（本仓） | 多语言客户端 SDK | - |
| [evo-agent](https://gitee.com/evo-rule-lab/evo-agent) | AI agent 编排层 | SDK 的用户之一 |

## 协议

AGPL-3.0-or-later,详见 [LICENSE](LICENSE)。
