// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * history 单项
 *
 * 对应 server GET /api/sessions/{id}/history 返回的
 * 完整 Fact 对象 + version 字段。此处仅声明常用字段，
 * 完整 Fact 字段请参考 {@link Fact}。
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class HistoryEntry {
    @JsonProperty("id")
    private long id;

    @JsonProperty("type")
    private String type;

    @JsonProperty("version")
    private long version;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public long getVersion() { return version; }
    public void setVersion(long version) { this.version = version; }
}
