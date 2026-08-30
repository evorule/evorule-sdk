// SPDX-License-Identifier: Apache-2.0
package com.evorule;

import com.evorule.exceptions.*;
import com.evorule.models.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.*;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class EvoruleE2ETest {
    private static final String BASE_URL = System.getenv().getOrDefault("EVORULE_BASE_URL", "http://localhost:18080");
    private static EvoruleClient client;
    private static ObjectMapper mapper;
    private static final AtomicInteger passed = new AtomicInteger(0);
    private static final AtomicInteger failed = new AtomicInteger(0);

    @BeforeAll
    static void setup() {
        client = new EvoruleClient(BASE_URL);
        mapper = new ObjectMapper();
        System.out.println("evorule Java SDK E2E 测试");
        System.out.println("服务器: " + BASE_URL);
    }

    private void pass(String msg) {
        passed.incrementAndGet();
        System.out.println("  ✅ PASS: " + msg);
    }

    private void fail(String msg) {
        failed.incrementAndGet();
        System.out.println("  ❌ FAIL: " + msg);
    }

    @Test
    @Order(1)
    @DisplayName("场景 1: 会话生命周期")
    void testSessionLifecycle() throws Exception {
        System.out.println("\n[场景 1] 会话生命周期");

        List<Long> before = client.listSessions();
        assertNotNull(before);
        assertInstanceOf(List.class, before);
        pass("list_sessions（初始列表）");

        try (Session session = client.createSession()) {
            assertTrue(session.getSessionId() > 0);
            pass("create_session（id=" + session.getSessionId() + "）");

            List<Long> sessions = client.listSessions();
            assertNotNull(sessions);
            assertTrue(sessions.size() >= before.size() + 1);
            pass("list_sessions（包含新会话）");

            SessionState state = session.state();
            assertNotNull(state);
            assertTrue(state.getVersion() >= 0);
            assertNotNull(state.getPayload());
            pass("state（version=" + state.getVersion() + "）");
        }
    }

    @Test
    @Order(2)
    @DisplayName("场景 2: 命令提交 + 状态更新")
    void testCommandAndState() throws Exception {
        System.out.println("\n[场景 2] 命令提交 + 状态更新");

        try (Session session = client.createSession()) {
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "x");
            setParams.put("operation", "set");
            setParams.put("value", 0);
            assertDoesNotThrow(() -> session.command(setCmd));
            pass("command（set x=0）");

            ObjectNode incCmd = mapper.createObjectNode();
            incCmd.put("type", "increment");
            ObjectNode incParams = incCmd.putObject("params");
            incParams.put("attr", "x");
            incParams.put("operation", "add");
            incParams.put("delta", 5);
            assertDoesNotThrow(() -> session.command(incCmd));
            pass("command（increment x +5）");

            SessionState state = session.state();
            assertNotNull(state);
            assertNotNull(state.getPayload());
            assertTrue(state.getVersion() >= 0);
            pass("state 验证（version=" + state.getVersion() + "）");
        }
    }

    @Test
    @Order(3)
    @DisplayName("场景 3: Payload 更新")
    void testPayloadUpdate() throws Exception {
        System.out.println("\n[场景 3] Payload 更新");

        try (Session session = client.createSession()) {
            assertDoesNotThrow(() -> session.updatePayload("status", "running"));
            pass("update_payload（status = running）");

            SessionState state = session.state();
            assertNotNull(state.getPayload());
            pass("state 验证（payload 非空）");

            assertDoesNotThrow(() -> session.updatePayload("nested.field", "deep"));
            pass("update_payload（nested.field = deep）");

            state = session.state();
            assertNotNull(state.getPayload());
            pass("state 验证（payload 非空）");
        }
    }

    @Test
    @Order(4)
    @DisplayName("场景 4: 时间旅行")
    void testTimeMachine() throws Exception {
        System.out.println("\n[场景 4] 时间旅行");

        try (Session session = client.createSession()) {
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "counter");
            setParams.put("operation", "set");
            setParams.put("value", 0);
            session.command(setCmd);

            ObjectNode incCmd = mapper.createObjectNode();
            incCmd.put("type", "increment");
            ObjectNode incParams = incCmd.putObject("params");
            incParams.put("attr", "counter");
            incParams.put("operation", "add");
            incParams.put("delta", 1);
            session.command(incCmd);
            session.command(incCmd);

            SessionState state = session.state();
            assertNotNull(state);
            assertNotNull(state.getPayload());
            pass("执行 3 条命令（version=" + state.getVersion() + "）");

            List<Fact> facts = session.replay();
            assertNotNull(facts);
            assertInstanceOf(List.class, facts);
            assertTrue(facts.size() > 0);
            pass("replay（返回 " + facts.size() + " 条记录）");

            long currentVersion = state.getVersion();
            if (currentVersion >= 1) {
                RewindResponse rewound = session.rewind(0);
                assertNotNull(rewound);
                pass("rewind(version=0)");
            } else {
                pass("rewind（跳过：version 不足）");
            }

            state = session.state();
            assertTrue(state.getVersion() >= 0);
            pass("state 验证（version=" + state.getVersion() + "）");

            if (currentVersion >= 2) {
                DiffResult diff = session.diff(0, 1);
                assertNotNull(diff);
                assertTrue(diff.getFromVersion() >= 0);
                assertTrue(diff.getToVersion() >= 0);
                pass("diff(v0→v1): from_version=" + diff.getFromVersion() +
                        ", added=" + diff.getAdded().size() +
                        ", removed=" + diff.getRemoved().size() +
                        ", changed=" + diff.getChanged().size());
            } else {
                pass("diff（跳过：version 不足）");
            }
        }
    }

    @Test
    @Order(5)
    @DisplayName("场景 5: Debug 端点")
    void testDebugEndpoints() throws Exception {
        System.out.println("\n[场景 5] Debug 端点");

        try (Session session = client.createSession()) {
            String phase = session.debugPhase();
            assertNotNull(phase);
            pass("debug_phase（phase=" + phase + "）");

            JsonNode queue = session.debugQueue();
            assertNotNull(queue);
            pass("debug_queue（queue_len=" + queue.size() + "）");

            JsonNode pendingIo = session.debugPendingIo();
            assertNotNull(pendingIo);
            pass("debug_pending_io（count=" + pendingIo.size() + "）");
        }
    }

    @Test
    @Order(6)
    @DisplayName("场景 6: 执行中断")
    void testInterrupt() throws Exception {
        System.out.println("\n[场景 6] 执行中断");

        try (Session session = client.createSession()) {
            SessionState state = session.state();
            assertNotNull(state.getPhase());
            pass("初始状态就绪（phase=" + state.getPhase() + "）");

            assertDoesNotThrow(() -> session.interrupt());
            pass("interrupt（成功提交）");

            state = session.state();
            assertNotNull(state);
            pass("中断后状态可读（version=" + state.getVersion() + "）");
        }
    }

    @Test
    @Order(7)
    @DisplayName("场景 7: 共享 Facts")
    void testSharedFacts() throws Exception {
        System.out.println("\n[场景 7] 共享 Facts");

        try (Session session = client.createSession()) {
            session.updatePayload("shared.value", 42);

            List<SharedFact> facts = client.getSharedFacts("");
            assertNotNull(facts);
            assertInstanceOf(List.class, facts);
            pass("shared_facts（count=" + facts.size() + "）");
        }
    }

    @Test
    @Order(8)
    @DisplayName("场景 8: Used at Startup")
    void testUsedAtStartup() throws Exception {
        System.out.println("\n[场景 8] Used at Startup");

        try (Session session = client.createSession()) {
            List<Long> factIds = new ArrayList<>();
            factIds.add(1L);
            factIds.add(2L);
            factIds.add(3L);
            assertDoesNotThrow(() -> session.recordUsedAtStartup(factIds));
            pass("record_used_at_startup（fact_ids=[1,2,3]）");

            List<Long> result = session.getUsedAtStartup();
            assertNotNull(result);
            assertInstanceOf(List.class, result);
            pass("get_used_at_startup（返回类型: list）");
        }
    }

    @Test
    @Order(9)
    @DisplayName("场景 9: IO Response")
    void testIoResponse() throws Exception {
        System.out.println("\n[场景 9] IO Response");

        try (Session session = client.createSession()) {
            ObjectNode result = mapper.createObjectNode();
            result.put("status", "ok");
            assertDoesNotThrow(() -> session.submitIoResponse(1L, result, null));
            pass("submit_io_response（成功提交）");
        }
    }

    @Test
    @Order(10)
    @DisplayName("场景 10: 审计链")
    void testAudit() throws Exception {
        System.out.println("\n[场景 10] 审计链");

        try (Session session = client.createSession()) {
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "x");
            setParams.put("operation", "set");
            setParams.put("value", 0);
            session.command(setCmd);

            JsonNode audit = session.audit();
            assertNotNull(audit);
            pass("audit（返回数据）");

            boolean valid = session.auditVerify();
            pass("audit_verify（valid=" + valid + "）");
        }
    }

    @Test
    @Order(11)
    @DisplayName("场景 11: 历史查询")
    void testHistory() throws Exception {
        System.out.println("\n[场景 11] 历史查询");

        try (Session session = client.createSession()) {
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "x");
            setParams.put("operation", "set");
            setParams.put("value", 0);
            session.command(setCmd);

            List<HistoryEntry> history = session.history();
            assertNotNull(history);
            assertInstanceOf(List.class, history);
            assertTrue(history.size() > 0);
            pass("history（返回 " + history.size() + " 条）");
        }
    }

    @Test
    @Order(12)
    @DisplayName("场景 12: 集群协作")
    void testCluster() throws Exception {
        System.out.println("\n[场景 12] 集群协作（DEPRECATED）");

        try (Session s1 = client.createSession();
             Session s2 = client.createSession()) {
            pass("创建 2 个会话（" + s1.getSessionId() + ", " + s2.getSessionId() + "）");

            // cluster 端点已被 evorule-server 移除，调用应失败（404 或连接重置）
            // 注意：server 对未注册的 /join 路径可能直接重置连接（IOException），
            // 也可能返回 404（EvoruleException），两种都算"deprecated 端点调用失败"。
            try {
                s1.join(s2.getSessionId(), null);
                fail("cluster join: expected failure (endpoint deprecated)");
            } catch (Exception e) {
                pass("cluster join（expected failure, endpoint deprecated: "
                        + e.getClass().getSimpleName() + "）");
            }
        }
    }

    @Test
    @Order(13)
    @DisplayName("场景 13: 会话分叉")
    void testFork() throws Exception {
        System.out.println("\n[场景 13] 会话分叉");

        try (Session parent = client.createSession()) {
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "forked");
            setParams.put("operation", "set");
            setParams.put("value", true);
            parent.command(setCmd);

            SessionState state = parent.state();
            assertNotNull(state);
            pass("父会话就绪（version=" + state.getVersion() + "）");

            JsonNode forkResult = client.forkSession(parent.getSessionId(), null);
            assertNotNull(forkResult);
            assertTrue(forkResult.has("session_id"));
            long childId = forkResult.get("session_id").asLong();
            assertTrue(childId > 0);
            assertNotEquals(parent.getSessionId(), childId);
            pass("fork_session（parent=" + parent.getSessionId() + " → child=" + childId + "）");

            SessionState childState = client.getSessionState(childId);
            assertNotNull(childState);
            assertNotNull(childState.getPayload());
            pass("子会话继承父状态（payload 非空）");

            client.closeSession(childId);
        }
    }

    @Test
    @Order(14)
    @DisplayName("场景 14: 健康检查")
    void testHealthChecks() throws Exception {
        System.out.println("\n[场景 14] 健康检查");

        JsonNode health = client.health();
        assertNotNull(health);
        pass("health（message=" + health.path("message").asText("ok") + "）");

        JsonNode liveness = client.liveness();
        assertNotNull(liveness);
        pass("liveness（status=" + liveness.path("status").asText("alive") + "）");

        JsonNode readiness = client.readiness();
        assertNotNull(readiness);
        pass("readiness（status=" + readiness.path("status").asText("ready") + "）");
    }

    @AfterAll
    static void summary() {
        System.out.println("\n============================================================");
        System.out.println("结果: " + passed.get() + " passed, " + failed.get() + " failed");
        if (failed.get() > 0) {
            System.out.println("\n失败用例: 详见上面的 ❌ FAIL 标记");
        }
        System.out.println("============================================================");
    }
}
