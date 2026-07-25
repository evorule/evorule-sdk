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

    public SessionState rewind(long id, long version) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/rewind/" + version)
                .GET()
                .build();
        HttpResponse<String> response = sendRequest(request);
        JsonNode root = parseJson(response.body());
        return objectMapper.treeToValue(root, SessionState.class);
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

    public List<Fact> sessionHistory(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/history")
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

    public List<Fact> sessionFactsByPrefix(long id, String prefix)
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
        List<Fact> facts = new ArrayList<>();
        if (root.isArray()) {
            for (JsonNode node : root) {
                facts.add(objectMapper.treeToValue(node, Fact.class));
            }
        }
        return facts;
    }

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

    public JsonNode sessionLeave(long id) throws EvoruleException, IOException, InterruptedException {
        HttpRequest request = requestBuilder("/api/sessions/" + id + "/leave")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        HttpResponse<String> response = sendRequest(request);
        return parseJson(response.body());
    }

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
        String url = baseURL + "/api/sessions/" + sessionId + "/events";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Accept", "text/event-stream")
                .GET()
                .build();
        if (authToken != null && !authToken.isEmpty()) {
            request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Accept", "text/event-stream")
                    .header("Authorization", "Bearer " + authToken)
                    .GET()
                    .build();
        }
        HttpResponse<java.io.InputStream> response = httpClient.send(
                request, HttpResponse.BodyHandlers.ofInputStream());
        int status = response.statusCode();
        if (status >= 400) {
            throw new EvoruleException("Failed to open SSE stream: status " + status);
        }
        BufferedReader reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8));
        return Stream.generate(() -> {
            try {
                String line;
                StringBuilder eventData = new StringBuilder();
                String eventType = null;
                while ((line = reader.readLine()) != null) {
                    if (line.isEmpty()) {
                        if (eventData.length() > 0 || eventType != null) {
                            JsonNode data = eventData.length() > 0
                                    ? objectMapper.readTree(eventData.toString())
                                    : objectMapper.createObjectNode();
                            long id = data.has("id") ? data.get("id").asLong() : 0;
                            return new SseEvent(eventType != null ? eventType : "message", id, data);
                        }
                        eventData.setLength(0);
                        eventType = null;
                        continue;
                    }
                    if (line.startsWith("event:")) {
                        eventType = line.substring(6).trim();
                    } else if (line.startsWith("data:")) {
                        eventData.append(line.substring(5).trim());
                    }
                }
                return null;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }).takeWhile(event -> event != null);
    }

    public void close() {
        // HttpClient implements AutoCloseable in Java 21+, but not in Java 17
        // We leave it for GC to handle
    }
}
