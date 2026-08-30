// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Diff 响应中 added/removed/unchanged 项
 *
 * 对应 server 返回的元组形态 <code>[key, value]</code>（兼容对象形态 {"key": "...", "value": ...}）。
 */
public class DiffEntry {
    @JsonProperty("key")
    private String key;

    @JsonProperty("value")
    private JsonNode value;

    public DiffEntry() {}

    public DiffEntry(String key, JsonNode value) {
        this.key = key;
        this.value = value;
    }

    /** 兼容元组形态 [key, value] 与对象形态 {"key": ..., "value": ...} */
    @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
    public static DiffEntry fromRaw(JsonNode node) {
        if (node == null || node.isNull()) {
            return new DiffEntry(null, null);
        }
        if (node.isArray()) {
            return new DiffEntry(
                    node.size() > 0 && !node.get(0).isNull() ? node.get(0).asText() : null,
                    node.size() > 1 ? node.get(1) : null);
        }
        if (node.isObject()) {
            return new DiffEntry(
                    node.hasNonNull("key") ? node.get("key").asText() : null,
                    node.get("value"));
        }
        return new DiffEntry(node.asText(), null);
    }

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public JsonNode getValue() { return value; }
    public void setValue(JsonNode value) { this.value = value; }
}
