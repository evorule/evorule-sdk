// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

public class SharedFact {
    @JsonProperty("fact_id")
    private long factId;

    @JsonProperty("path")
    private String path;

    @JsonProperty("value")
    private JsonNode value;

    @JsonProperty("source_session_id")
    private long sourceSessionId;

    @JsonProperty("version")
    private long version;

    public long getFactId() { return factId; }
    public void setFactId(long factId) { this.factId = factId; }

    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }

    public JsonNode getValue() { return value; }
    public void setValue(JsonNode value) { this.value = value; }

    public long getSourceSessionId() { return sourceSessionId; }
    public void setSourceSessionId(long sourceSessionId) { this.sourceSessionId = sourceSessionId; }

    public long getVersion() { return version; }
    public void setVersion(long version) { this.version = version; }
}
