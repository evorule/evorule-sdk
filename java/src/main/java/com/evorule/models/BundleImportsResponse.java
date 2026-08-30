// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * 导入溯源历史响应（GET /api/bundles/imports）
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class BundleImportsResponse {
    @JsonProperty("imports")
    private List<BundleImportRecord> imports;

    @JsonProperty("count")
    private long count;

    public List<BundleImportRecord> getImports() { return imports; }
    public void setImports(List<BundleImportRecord> imports) { this.imports = imports; }

    public long getCount() { return count; }
    public void setCount(long count) { this.count = count; }
}
