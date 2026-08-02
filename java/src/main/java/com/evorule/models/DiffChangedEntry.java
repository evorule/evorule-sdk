// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Diff 响应中 changed 项
 *
 * 对应 server 返回的 {"key": "...", "old_value": ..., "new_value": ...}
 */
public class DiffChangedEntry {
    @JsonProperty("key")
    private String key;

    @JsonProperty("old_value")
    private JsonNode oldValue;

    @JsonProperty("new_value")
    private JsonNode newValue;

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public JsonNode getOldValue() { return oldValue; }
    public void setOldValue(JsonNode oldValue) { this.oldValue = oldValue; }

    public JsonNode getNewValue() { return newValue; }
    public void setNewValue(JsonNode newValue) { this.newValue = newValue; }
}
