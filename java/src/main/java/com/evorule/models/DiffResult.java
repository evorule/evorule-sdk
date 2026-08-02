// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.util.List;

/**
 * Diff 响应（两个版本的 payload 对比）
 *
 * 对应 server GET /api/sessions/{id}/diff?a=X&b=Y 返回的
 * {session_id, from_version, to_version, added, removed, changed, unchanged, summary}
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class DiffResult {
    @JsonProperty("session_id")
    private long sessionId;

    @JsonProperty("from_version")
    private long fromVersion;

    @JsonProperty("to_version")
    private long toVersion;

    @JsonProperty("added")
    private List<DiffEntry> added;

    @JsonProperty("removed")
    private List<DiffEntry> removed;

    @JsonProperty("changed")
    private List<DiffChangedEntry> changed;

    @JsonProperty("unchanged")
    private List<DiffEntry> unchanged;

    @JsonProperty("summary")
    private JsonNode summary;

    public long getSessionId() { return sessionId; }
    public void setSessionId(long sessionId) { this.sessionId = sessionId; }

    public long getFromVersion() { return fromVersion; }
    public void setFromVersion(long fromVersion) { this.fromVersion = fromVersion; }

    public long getToVersion() { return toVersion; }
    public void setToVersion(long toVersion) { this.toVersion = toVersion; }

    public List<DiffEntry> getAdded() { return added; }
    public void setAdded(List<DiffEntry> added) { this.added = added; }

    public List<DiffEntry> getRemoved() { return removed; }
    public void setRemoved(List<DiffEntry> removed) { this.removed = removed; }

    public List<DiffChangedEntry> getChanged() { return changed; }
    public void setChanged(List<DiffChangedEntry> changed) { this.changed = changed; }

    public List<DiffEntry> getUnchanged() { return unchanged; }
    public void setUnchanged(List<DiffEntry> unchanged) { this.unchanged = unchanged; }

    public JsonNode getSummary() { return summary; }
    public void setSummary(JsonNode summary) { this.summary = summary; }
}
