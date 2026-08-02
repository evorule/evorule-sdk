// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.databind.JsonNode;

public class SseEvent {
    private final String type;
    private final long id;
    private final JsonNode data;

    public SseEvent(String type, long id, JsonNode data) {
        this.type = type;
        this.id = id;
        this.data = data;
    }

    public String getType() { return type; }
    public long getId() { return id; }
    public JsonNode getData() { return data; }
}
