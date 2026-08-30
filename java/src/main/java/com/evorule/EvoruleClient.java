// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule;

import com.evorule.exceptions.*;
import com.evorule.models.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

public class EvoruleClient implements AutoCloseable {
    private final String baseURL;
    private final String authToken;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public EvoruleClient(String baseURL) {
        this(baseURL, null);
    }

    public EvoruleClient(String baseURL, String authToken) {
        this.baseURL = baseURL.endsWith("/") ? baseURL.substring(0, baseURL.length() - 1) : baseURL;
        this.authToken = authToken;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                .build();
        this.objectMapper = new ObjectMapper();
    }

    private HttpRequest.Builder requestBuilder(String path) {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(baseURL + path));
        if (authToken != null && !authToken.isEmpty()) {
            builder.header("Authorization", "Bearer " + authToken);
        }
        return builder;
    }

    private HttpResponse<String> sendRequest(HttpRequest request)
            throws EvoruleException, IOException, InterruptedException {
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        int status = response.statusCode();
        if (status == 401) {
            throw new AuthenticationException("Authentication failed");
        }
        if (status >= 400) {
            String body = response.body();
            String message = "Request failed with status " + status;
            try {
                JsonNode root = objectMapper.readTree(body);
                if (root.has("message")) {
                    message = root.get("message").asText();
                } else if (root.has("error")) {
                    message = root.get("error").asText();
                }
            } catch (Exception ignored) {
                if (!body.isEmpty()) {
                    message = body;
                }
            }
            throw new EvoruleException(message);
        }
        return response;
    }

    private JsonNode parseJson(String body) throws EvoruleException {
        try {
            return objectMapper.readTree(body);
        } catch (Exception e) {
            throw new EvoruleException("Failed to parse JSON response", e);
        }
    }

    public Session createSession() throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        long sessionId = root.get("session_id").asLong();
        return new Session(this, sessionId);
    }

    public SessionState getSessionState(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/state")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, SessionState.class);
    }

    public List<Long> listSessions() throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<Long> sessions = new ArrayList<>();
        JsonNode sessionsNode = root.get("sessions");
        if (sessionsNode != null && sessionsNode.isArray()) {
            for (JsonNode node : sessionsNode) {
                sessions.add(node.asLong());
            }
        }
        return sessions;
    }

    public void closeSession(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id)
                .DELETE()
                .build();
        sendRequest(request);
    }

    public void submitCommand(long id, JsonNode instruction) throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.set("instruction", instruction);
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/command")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        sendRequest(request);
    }

    public void updatePayload(long id, String path, Object value) throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.put("path", path);
        body.set("value", objectMapper.valueToTree(value));
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/payload")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        sendRequest(request);
    }

    public List<Fact> getReplay(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/replay")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<Fact> facts = new ArrayList<>();
        if (root.isArray()) {
            for (JsonNode node : root) {
                facts.add(objectMapper.treeToValue(node, Fact.class));
            }
        }
        return facts;
    }

    public RewindResponse rewind(long id, long version) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/rewind?version=" + version)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, RewindResponse.class);
    }

    public DiffResult diff(long id, long from, long to) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/diff?a=" + from + "&b=" + to)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, DiffResult.class);
    }

    public List<SharedFact> getSharedFacts(String prefix) throws EvoruleException, IOException, InterruptedException {
        String url = "/api/shared/facts";
        if (prefix != null && !prefix.isEmpty()) {
            url += "?prefix=" + URLEncoder.encode(prefix, StandardCharsets.UTF_8);
        }
        HttpRequest request = requestBuilder(url)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<SharedFact> facts = new ArrayList<>();
        if (root.isArray()) {
            for (JsonNode node : root) {
                facts.add(objectMapper.treeToValue(node, SharedFact.class));
            }
        }
        return facts;
    }

    public SharedFact sharedFactSource(long factId) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/shared/facts/" + factId + "/source")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, SharedFact.class);
    }

    public List<Long> sharedFactUsedBy(long factId) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/shared/facts/" + factId + "/used_by")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<Long> sessions = new ArrayList<>();
        JsonNode sessionsNode = root.get("sessions");
        if (sessionsNode != null && sessionsNode.isArray()) {
            for (JsonNode node : sessionsNode) {
                sessions.add(node.asLong());
            }
        }
        return sessions;
    }

    public void recordUsedAtStartup(long id, List<Long> factIds) throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        ArrayNode ids = body.putArray("fact_ids");
        for (Long fid : factIds) {
            ids.add(fid);
        }
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/used_at_startup")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        sendRequest(request);
    }

    public List<Long> getUsedAtStartup(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/used_at_startup")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<Long> factIds = new ArrayList<>();
        JsonNode idsNode = root.get("fact_ids");
        if (idsNode != null && idsNode.isArray()) {
            for (JsonNode node : idsNode) {
                factIds.add(node.asLong());
            }
        }
        return factIds;
    }

    public void interrupt(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/interrupt")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        sendRequest(request);
    }

    public void submitIoResponse(long id, long requestId, JsonNode result, String error)
            throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.put("request_id", requestId);
        body.set("result", result);
        if (error != null) {
            body.put("error", error);
        } else {
            body.putNull("error");
        }
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/io_response")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        sendRequest(request);
    }

    public String debugPhase(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/debug/phase")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("phase") ? root.get("phase").asText() : "Unknown";
    }

    public JsonNode debugQueue(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/debug/queue")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.get("queue");
    }

    public JsonNode debugPendingIo(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/debug/pending_io")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.get("pending_io");
    }

    // ===== S4 端点补齐：会话运行时状态查询 =====

    /** 查询会话是否已完成（GET /api/sessions/{id}/finished） */
    public boolean isFinished(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/finished")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("finished") && root.get("finished").asBoolean();
    }

    /** 查询因果链深度（GET /api/sessions/{id}/causal_depth） */
    public long causalDepth(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/causal_depth")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("causal_depth") ? root.get("causal_depth").asLong() : 0;
    }

    /** 查询结构不变式违规计数（GET /api/sessions/{id}/invariants） */
    public long invariants(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/invariants")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("structural_invariant_violations")
                ? root.get("structural_invariant_violations").asLong() : 0;
    }

    /** 查询待处理 I/O 数量（GET /api/sessions/{id}/pending_io_count） */
    public long pendingIoCount(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/pending_io_count")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("pending_io_count") ? root.get("pending_io_count").asLong() : 0;
    }

    /** 查询当前执行步数（GET /api/sessions/{id}/step） */
    public long currentStep(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/step")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("current_step") ? root.get("current_step").asLong() : 0;
    }

    /** 查询完整状态快照（GET /api/sessions/{id}/snapshot） */
    public SnapshotResponse snapshot(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/snapshot")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, SnapshotResponse.class);
    }

    // ===== 快照包（DatasetBundle）API =====
    //
    // 校验口径零复刻：六项校验链由服务端执行（evorule-bundle SSOT），
    // SDK 仅做 HTTP 薄封装。400 时 sendRequest 透传服务端 error 字段，不静默。

    /**
     * 导入快照包并激活（POST /api/bundles/import）
     *
     * 六项硬校验 + 逐条 Schema 门禁由服务端执行；任一失败整体拒绝，
     * 成功则原子落盘并触发滚动热重载（导入即激活）。
     *
     * @param bundle DatasetBundle 快照包对象（原样透传，不本地校验）
     * @throws EvoruleException 服务端校验/落盘失败（400，消息为服务端 error 字段）
     */
    public ImportBundleResponse importBundle(JsonNode bundle)
            throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.set("bundle", bundle);
        HttpRequest request = requestBuilder("/api/bundles/import")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        HttpResponse<String> response = sendRequest(request);
        return objectMapper.treeToValue(parseJson(response.body()), ImportBundleResponse.class);
    }

    /**
     * 导入预检（POST /api/bundles/import/dry-run）：只跑校验链，不落盘不热重载。
     *
     * @param bundle DatasetBundle 快照包对象（原样透传，不本地校验）
     * @throws EvoruleException 预检未通过（400，消息为服务端 error 字段）
     */
    public DryRunImportResponse dryRunImport(JsonNode bundle)
            throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.set("bundle", bundle);
        HttpRequest request = requestBuilder("/api/bundles/import/dry-run")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        HttpResponse<String> response = sendRequest(request);
        return objectMapper.treeToValue(parseJson(response.body()), DryRunImportResponse.class);
    }

    /** 查询当前激活的快照包列表（GET /api/bundles/active） */
    public ActiveBundlesResponse listActiveBundles()
            throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/bundles/active")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return objectMapper.treeToValue(parseJson(response.body()), ActiveBundlesResponse.class);
    }

    /**
     * 查询快照包导入溯源历史（GET /api/bundles/imports）
     *
     * @param limit 返回条数上限（1-1000，服务端默认 100）；null 时使用服务端默认值
     */
    public BundleImportsResponse listBundleImports(Integer limit)
            throws EvoruleException, IOException, InterruptedException {
        String url = "/api/bundles/imports";
        if (limit != null && limit > 0) {
            url += "?limit=" + limit;
        }
        HttpRequest request = requestBuilder(url)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return objectMapper.treeToValue(parseJson(response.body()), BundleImportsResponse.class);
    }

    public JsonNode health() throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/health")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    public JsonNode liveness() throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/health/liveness")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    public JsonNode readiness() throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/health/readiness")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    public JsonNode forkSession(long parentId, Long version) throws EvoruleException, IOException, InterruptedException {
        String url;
        if (version != null) {
            url = "/api/sessions/fork/" + parentId + "?version=" + version;
        } else {
            url = "/api/sessions/from/" + parentId;
        }
        HttpRequest request = requestBuilder(url)
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    public JsonNode sessionAudit(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/audit")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    public boolean sessionAuditVerify(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/audit/verify")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return root.has("valid") && root.get("valid").asBoolean();
    }

    public List<HistoryEntry> sessionHistory(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/history")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<HistoryEntry> entries = new ArrayList<>();
        if (root.isArray()) {
            for (JsonNode node : root) {
                entries.add(objectMapper.treeToValue(node, HistoryEntry.class));
            }
        }
        return entries;
    }

    public List<SessionFactEntry> sessionFactsByPrefix(long id, String prefix)
            throws EvoruleException, IOException, InterruptedException {
        String url = "/api/sessions/" + id + "/facts";
        if (prefix != null && !prefix.isEmpty()) {
            url += "?prefix=" + URLEncoder.encode(prefix, StandardCharsets.UTF_8);
        }
        HttpRequest request = requestBuilder(url)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<SessionFactEntry> entries = new ArrayList<>();
        if (root.isArray()) {
            for (JsonNode node : root) {
                entries.add(objectMapper.treeToValue(node, SessionFactEntry.class));
            }
        }
        return entries;
    }

    /**
     * 加入集群协作（POST /api/sessions/{id}/join）
     *
     * @deprecated evorule-server 已移除 cluster 端点（多 reactor 协作原语属应用层功能）。
     *             调用此方法将返回 404。保留代码供未来 cluster 模块重新启用时使用。
     */
    @Deprecated
    public JsonNode sessionJoin(long id, long targetId, String direction)
            throws EvoruleException, IOException, InterruptedException {
        ObjectNode body = objectMapper.createObjectNode();
        body.put("target_id", targetId);
        if (direction != null && !direction.isEmpty()) {
            body.put("direction", direction);
        }
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/join")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    /**
     * 离开所有集群协作（POST /api/sessions/{id}/leave）
     *
     * @deprecated evorule-server 已移除 cluster 端点。调用此方法将返回 404。
     */
    @Deprecated
    public JsonNode sessionLeave(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/leave")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

    /**
     * 查询会话集群成员（GET /api/sessions/{id}/cluster）
     *
     * @deprecated evorule-server 已移除 cluster 端点。调用此方法将返回 404。
     */
    @Deprecated
    public List<Long> sessionClusterStatus(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/cluster")
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        List<Long> members = new ArrayList<>();
        JsonNode membersNode = root.get("cluster_members");
        if (membersNode != null && membersNode.isArray()) {
            for (JsonNode node : membersNode) {
                members.add(node.asLong());
            }
        }
        return members;
    }

    public Stream<SseEvent> streamEvents(long sessionId) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + sessionId + "/events")
                .header("Accept", "text/event-stream")
                .GET()
                .build();
        HttpResponse<java.io.InputStream> response = httpClient.send(
                request, HttpResponse.BodyHandlers.ofInputStream());
        int status = response.statusCode();
        if (status == 401) {
            throw new AuthenticationException("Authentication failed");
        }
        if (status >= 400) {
            throw new EvoruleException("Failed to open SSE stream: status " + status);
        }
        BufferedReader reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8));
        Stream<SseEvent> stream = Stream.generate(() -> {
            try {
                String line;
                StringBuilder eventData = new StringBuilder();
                String eventType = null;
                String sseId = null; // SSE id: 行（规范来源）
                while ((line = reader.readLine()) != null) {
                    if (line.isEmpty()) {
                        if (eventData.length() > 0 || eventType != null) {
                            JsonNode data = eventData.length() > 0
                                    ? objectMapper.readTree(eventData.toString())
                                    : objectMapper.createObjectNode();
                            // S2 修复：优先用 SSE id: 行的 id，回退到 data JSON 的 id 字段
                            long id;
                            if (sseId != null && !sseId.isEmpty()) {
                                try {
                                    id = Long.parseLong(sseId);
                                } catch (NumberFormatException e) {
                                    id = data.has("id") ? data.get("id").asLong() : 0;
                                }
                            } else {
                                id = data.has("id") ? data.get("id").asLong() : 0;
                            }
                            return new SseEvent(eventType != null ? eventType : "message", id, data);
                        }
                        eventData.setLength(0);
                        eventType = null;
                        sseId = null;
                        continue;
                    }
                    if (line.startsWith("event:")) {
                        eventType = line.substring(6).trim();
                    } else if (line.startsWith("id:")) {
                        sseId = line.substring(3).trim();
                    } else if (line.startsWith("data:")) {
                        // SSE 规范：data: 后有一个可选空格，需去掉
                        String dataLine = line.substring(5);
                        if (dataLine.startsWith(" ")) {
                            dataLine = dataLine.substring(1);
                        }
                        eventData.append(dataLine);
                    }
                }
                return null;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }).takeWhile(event -> event != null);
        // N1 修复：确保 Stream 关闭时释放底层 reader/inputStream，避免 socket 泄漏
        return stream.onClose(() -> {
            try {
                reader.close();
            } catch (IOException ignored) {
                // 忽略关闭时的错误
            }
        });
    }

    public void close() {
        // HttpClient implements AutoCloseable in Java 21+, but not in Java 17
        // We leave it for GC to handle
    }
}
