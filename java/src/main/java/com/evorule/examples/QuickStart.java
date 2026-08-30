// SPDX-License-Identifier: Apache-2.0
package com.evorule.examples;

import com.evorule.EvoruleClient;
import com.evorule.Session;
import com.evorule.models.DiffResult;
import com.evorule.models.Fact;
import com.evorule.models.SessionState;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.List;

public class QuickStart {
    public static void main(String[] args) throws Exception {
        String baseUrl = System.getenv().getOrDefault("EVORULE_BASE_URL", "http://localhost:18080");
        ObjectMapper mapper = new ObjectMapper();
        EvoruleClient client = new EvoruleClient(baseUrl);

        System.out.println("=== Evorule Java SDK Quick Start ===");
        System.out.println("服务器: " + baseUrl);

        try (Session session = client.createSession()) {
            System.out.println("\n[1] 会话创建成功，ID: " + session.getSessionId());

            SessionState state = session.state();
            System.out.println("    初始版本: " + state.getVersion());
            System.out.println("    初始阶段: " + state.getPhase());

            System.out.println("\n[2] 提交命令: set counter = 0");
            ObjectNode setCmd = mapper.createObjectNode();
            setCmd.put("type", "set");
            ObjectNode setParams = setCmd.putObject("params");
            setParams.put("attr", "counter");
            setParams.put("operation", "set");
            setParams.put("value", 0);
            session.command(setCmd);

            System.out.println("    提交命令: increment counter + 5");
            ObjectNode incCmd = mapper.createObjectNode();
            incCmd.put("type", "increment");
            ObjectNode incParams = incCmd.putObject("params");
            incParams.put("attr", "counter");
            incParams.put("operation", "add");
            incParams.put("delta", 5);
            session.command(incCmd);

            state = session.state();
            System.out.println("    当前版本: " + state.getVersion());
            System.out.println("    counter = " + state.getPayload().get("counter"));

            System.out.println("\n[3] 更新 Payload: status = running");
            session.updatePayload("status", "running");
            state = session.state();
            System.out.println("    status = " + state.getPayload().get("status").asText());

            System.out.println("\n[4] 时间旅行 - 重放");
            List<Fact> facts = session.replay();
            System.out.println("    重放事实数: " + facts.size());
            for (Fact f : facts) {
                System.out.println("      - " + f.getType() + " (id=" + f.getId() + ")");
            }

            System.out.println("\n[5] 时间旅行 - 回滚到版本 1");
            session.rewind(1);
            state = session.state();
            System.out.println("    回滚后版本: " + state.getVersion());

            System.out.println("\n[6] 时间旅行 - 比较版本 1 和 3");
            DiffResult diff = session.diff(1, 3);
            System.out.println("    新增: " + diff.getAdded().size() + " 字段");
            System.out.println("    删除: " + diff.getRemoved().size() + " 字段");
            System.out.println("    变更: " + diff.getChanged().size() + " 字段");

            System.out.println("\n[7] 调试信息");
            System.out.println("    阶段: " + session.debugPhase());
            System.out.println("    队列长度: " + session.debugQueue().size());
            System.out.println("    挂起 I/O 数: " + session.debugPendingIo().size());

            System.out.println("\n✅ Quick Start 完成！");
        }
    }
}
