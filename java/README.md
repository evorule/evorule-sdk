# Evorule Java SDK

Evorule 的 Java 客户端 SDK，用于与 Evorule HTTP API 交互。

## 特性

- 完整的会话管理（创建、查询、关闭）
- 命令提交和 SSE 事件流订阅
- Payload 更新与嵌套字段支持
- 时间旅行（replay / rewind / diff）
- 调试端点（phase / queue / pending_io）
- 执行中断
- 共享 Facts 管理
- 审计链与验证
- 历史查询
- 集群协作（join / leave / cluster）
- 会话分叉
- 健康检查（health / liveness / readiness）
- I/O 响应提交

## 要求

- Java 17+
- Gradle 或 Maven

## 安装

### Gradle

```groovy
dependencies {
    implementation 'com.evorule:evorule-sdk:0.1.0'
}
```

### Maven

```xml
<dependency>
    <groupId>com.evorule</groupId>
    <artifactId>evorule-sdk</artifactId>
    <version>0.1.0</version>
</dependency>
```

## 快速开始

```java
import com.evorule.EvoruleClient;
import com.evorule.Session;
import com.evorule.models.Fact;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class QuickStart {
    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        EvoruleClient client = new EvoruleClient("http://localhost:18080");

        // 创建会话
        try (Session session = client.createSession()) {
            System.out.println("会话 ID: " + session.getSessionId());

            // 提交命令
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            setCmd.put("path", "counter");
            setCmd.put("value", 0);
            session.command(setCmd);

            ObjectNode incCmd = mapper.createObjectNode();
            incCmd.put("type", "increment");
            incCmd.put("path", "counter");
            incCmd.put("value", 5);
            session.command(incCmd);

            // 获取状态
            var state = session.state();
            System.out.println("版本: " + state.getVersion());
            System.out.println("Payload: " + state.getPayload());

            // 时间旅行 - 重放
            var facts = session.replay();
            System.out.println("重放事实数: " + facts.size());

            // 回滚到版本 1
            session.rewind(1);
        }
    }
}
```

## API 概览

### EvoruleClient

| 方法 | 说明 |
|------|------|
| `createSession()` | 创建新会话 |
| `getSessionState(id)` | 获取会话状态 |
| `listSessions()` | 列出所有会话 |
| `closeSession(id)` | 关闭会话 |
| `submitCommand(id, instruction)` | 提交命令 |
| `updatePayload(id, path, value)` | 更新 payload |
| `getReplay(id)` | 获取重放历史 |
| `rewind(id, version)` | 回滚到指定版本 |
| `diff(id, from, to)` | 比较两个版本差异 |
| `getSharedFacts(prefix)` | 获取共享 Facts |
| `sharedFactSource(factId)` | 获取共享 Fact 来源 |
| `sharedFactUsedBy(factId)` | 获取使用共享 Fact 的会话 |
| `recordUsedAtStartup(id, factIds)` | 记录启动时引用 |
| `getUsedAtStartup(id)` | 获取启动时引用 |
| `interrupt(id)` | 中断执行 |
| `submitIoResponse(id, requestId, result, error)` | 提交 I/O 响应 |
| `debugPhase(id)` | 获取反应器阶段 |
| `debugQueue(id)` | 获取执行队列 |
| `debugPendingIo(id)` | 获取挂起 I/O |
| `health()` | 健康检查 |
| `liveness()` | 存活探针 |
| `readiness()` | 就绪探针 |
| `forkSession(parentId, version)` | 分叉会话 |
| `sessionAudit(id)` | 获取审计报告 |
| `sessionAuditVerify(id)` | 验证审计链 |
| `sessionHistory(id)` | 获取历史 |
| `sessionFactsByPrefix(id, prefix)` | 按前缀查询 Facts |
| `sessionJoin(id, targetId, direction)` | 加入集群 |
| `sessionLeave(id)` | 离开集群 |
| `sessionClusterStatus(id)` | 集群状态 |
| `streamEvents(sessionId)` | SSE 事件流 |

### Session

`Session` 类提供了面向对象的会话操作接口，实现了 `AutoCloseable`：

| 方法 | 说明 |
|------|------|
| `state()` | 获取当前状态 |
| `payload()` | 获取当前 payload |
| `command(instruction)` | 提交命令 |
| `updatePayload(path, value)` | 更新 payload |
| `replay()` | 重放历史 |
| `rewind(version)` | 回滚版本 |
| `diff(from, to)` | 比较版本 |
| `debugPhase()` / `debugQueue()` / `debugPendingIo()` | 调试端点 |
| `interrupt()` | 中断执行 |
| `submitIoResponse(requestId, result, error)` | 提交 I/O 响应 |
| `audit()` / `auditVerify()` | 审计 |
| `history()` | 历史 |
| `factsByPrefix(prefix)` | 按前缀查 Facts |
| `recordUsedAtStartup(factIds)` / `getUsedAtStartup()` | 启动引用 |
| `join(targetId, direction)` / `leave()` / `clusterStatus()` | 集群 |
| `events()` | SSE 事件流 |
| `close()` | 关闭会话 |

## 异常体系

- `EvoruleException` — 基类异常
- `AuthenticationException` — 认证失败
- `SessionNotFoundError` — 会话不存在
- `SessionClosedError` — 会话已关闭
- `CommandError` — 命令执行错误

## 许可证

AGPL-3.0，详见 [LICENSE](LICENSE)。
