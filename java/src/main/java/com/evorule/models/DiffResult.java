// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.util.ArrayList;
import java.util.List;

/**
 * Diff 响应（两个版本的 payload 对比）
 *
 * 对应 server GET /api/sessions/{id}/diff?a=X&b=Y 返回的
 * {session_id, from_version, to_version, items, removed, summary}。
 *
 * 注意：server 对空列表整体省略（如 added/changed 无变更时缺省），
 * 故各列表字段缺省为空列表，调用方无需判空。
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class DiffResult {
    @JsonProperty("session_id")
    private long sessionId;

    @JsonProperty("from_version")
    private long fromVersion;

    @JsonProperty("to_version")
    private long toVersion;

    /** 新增项 [key, value]（server 无新增时省略该键） */
    @JsonProperty("added")
    private List<DiffEntry> added = new ArrayList<>();

    /** 删除项 [key, value] */
    @JsonProperty("removed")
    private List<DiffEntry> removed = new ArrayList<>();

    /** 变更项 [key, old, new]（server 无变更时省略该键） */
    @JsonProperty("changed")
    private List<DiffChangedEntry> changed = new ArrayList<>();

    /** server 变更项主键（与 changed 同形态，元组 [key, old, new]） */
    @JsonProperty("items")
    private List<DiffChangedEntry> items = new ArrayList<>();

    /** 未变更项（server 无时省略该键） */
    @JsonProperty("unchanged")
    private List<DiffEntry> unchanged = new ArrayList<>();

    @JsonProperty("summary")
    private JsonNode summary;

    public long getSessionId() { return sessionId; }
    public void setSessionId(long sessionId) { this.sessionId = sessionId; }

    public long getFromVersion() { return fromVersion; }
    public void setFromVersion(long fromVersion) { this.fromVersion = fromVersion; }

    public long getToVersion() { return toVersion; }
    public void setToVersion(long toVersion) { this.toVersion = toVersion; }

    public List<DiffEntry> getAdded() { return added; }
    public void setAdded(List<DiffEntry> added) {
        this.added = added != null ? added : new ArrayList<>();
    }

    public List<DiffEntry> getRemoved() { return removed; }
    public void setRemoved(List<DiffEntry> removed) {
        this.removed = removed != null ? removed : new ArrayList<>();
    }

    public List<DiffChangedEntry> getChanged() { return changed; }
    public void setChanged(List<DiffChangedEntry> changed) {
        this.changed = changed != null ? changed : new ArrayList<>();
    }

    public List<DiffChangedEntry> getItems() { return items; }
    public void setItems(List<DiffChangedEntry> items) {
        this.items = items != null ? items : new ArrayList<>();
    }

    public List<DiffEntry> getUnchanged() { return unchanged; }
    public void setUnchanged(List<DiffEntry> unchanged) {
        this.unchanged = unchanged != null ? unchanged : new ArrayList<>();
    }

    public JsonNode getSummary() { return summary; }
    public void setSummary(JsonNode summary) { this.summary = summary; }
}
