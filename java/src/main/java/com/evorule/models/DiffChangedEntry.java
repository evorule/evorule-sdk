// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Diff 响应中 changed 项
 *
 * 对应 server 返回的元组形态 <code>[key, old_value, new_value]</code>
 * （兼容对象形态 {"key": "...", "old_value": ..., "new_value": ...}）。
 */
public class DiffChangedEntry {
    @JsonProperty("key")
    private String key;

    @JsonProperty("old_value")
    private JsonNode oldValue;

    @JsonProperty("new_value")
    private JsonNode newValue;

    public DiffChangedEntry() {}

    public DiffChangedEntry(String key, JsonNode oldValue, JsonNode newValue) {
        this.key = key;
        this.oldValue = oldValue;
        this.newValue = newValue;
    }

    /** 兼容元组形态 [key, old_value, new_value] 与对象形态 */
    @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
    public static DiffChangedEntry fromRaw(JsonNode node) {
        if (node == null || node.isNull()) {
            return new DiffChangedEntry(null, null, null);
        }
        if (node.isArray()) {
            return new DiffChangedEntry(
                    node.size() > 0 && !node.get(0).isNull() ? node.get(0).asText() : null,
                    node.size() > 1 ? node.get(1) : null,
                    node.size() > 2 ? node.get(2) : null);
        }
        if (node.isObject()) {
            return new DiffChangedEntry(
                    node.hasNonNull("key") ? node.get("key").asText() : null,
                    node.get("old_value"),
                    node.get("new_value"));
        }
        return new DiffChangedEntry(node.asText(), null, null);
    }

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public JsonNode getOldValue() { return oldValue; }
    public void setOldValue(JsonNode oldValue) { this.oldValue = oldValue; }

    public JsonNode getNewValue() { return newValue; }
    public void setNewValue(JsonNode newValue) { this.newValue = newValue; }
}
