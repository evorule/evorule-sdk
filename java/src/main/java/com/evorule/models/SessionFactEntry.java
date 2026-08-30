// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * 会话内 Fact 单项（按前缀查询）
 *
 * 对应 server GET /api/sessions/{id}/facts 返回的
 * {"fact_id": ..., "version": ..., "path": "...", "value": ...}
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class SessionFactEntry {
    @JsonProperty("fact_id")
    private long factId;

    @JsonProperty("version")
    private long version;

    @JsonProperty("path")
    private String path;

    @JsonProperty("value")
    private JsonNode value;

    public long getFactId() { return factId; }
    public void setFactId(long factId) { this.factId = factId; }

    public long getVersion() { return version; }
    public void setVersion(long version) { this.version = version; }

    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }

    public JsonNode getValue() { return value; }
    public void setValue(JsonNode value) { this.value = value; }
}
