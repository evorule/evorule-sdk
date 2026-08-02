// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.util.List;

/**
 * Rewind 响应（回滚后的状态快照）
 *
 * 对应 server GET /api/sessions/{id}/rewind?version=X 返回的
 * {session_id, target_version, payload, queue, actual_version}
 *
 * actual_version 是实际回滚到的版本（可能因版本间隙与 target_version 不同）
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class RewindResponse {
    @JsonProperty("session_id")
    private long sessionId;

    @JsonProperty("target_version")
    private long targetVersion;

    @JsonProperty("actual_version")
    private long actualVersion;

    @JsonProperty("payload")
    private JsonNode payload;

    @JsonProperty("queue")
    private List<JsonNode> queue;

    public long getSessionId() { return sessionId; }
    public void setSessionId(long sessionId) { this.sessionId = sessionId; }

    public long getTargetVersion() { return targetVersion; }
    public void setTargetVersion(long targetVersion) { this.targetVersion = targetVersion; }

    public long getActualVersion() { return actualVersion; }
    public void setActualVersion(long actualVersion) { this.actualVersion = actualVersion; }

    public JsonNode getPayload() { return payload; }
    public void setPayload(JsonNode payload) { this.payload = payload; }

    public List<JsonNode> getQueue() { return queue; }
    public void setQueue(List<JsonNode> queue) { this.queue = queue; }
}
