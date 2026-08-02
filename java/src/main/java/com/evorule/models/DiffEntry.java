// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Diff 响应中 added/removed/unchanged 项
 *
 * 对应 server 返回的 {"key": "...", "value": ...}
 */
public class DiffEntry {
    @JsonProperty("key")
    private String key;

    @JsonProperty("value")
    private JsonNode value;

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public JsonNode getValue() { return value; }
    public void setValue(JsonNode value) { this.value = value; }
}
