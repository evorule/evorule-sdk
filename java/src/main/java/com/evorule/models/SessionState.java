// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

@JsonIgnoreProperties(ignoreUnknown = true)
public class SessionState {
    @JsonProperty("version")
    private long version;

    @JsonProperty("payload")
    private JsonNode payload;

    @JsonProperty("queue")
    private JsonNode queue;

    @JsonProperty("reactor")
    private JsonNode reactor;

    public long getVersion() { return version; }
    public void setVersion(long version) { this.version = version; }

    public JsonNode getPayload() { return payload; }
    public void setPayload(JsonNode payload) { this.payload = payload; }

    public JsonNode getQueue() { return queue; }
    public void setQueue(JsonNode queue) { this.queue = queue; }

    public JsonNode getReactor() { return reactor; }
    public void setReactor(JsonNode reactor) { this.reactor = reactor; }

    public String getPhase() {
        if (reactor != null && reactor.has("phase") && !reactor.get("phase").isNull()) {
            return reactor.get("phase").asText();
        }
        return null;
    }
}
