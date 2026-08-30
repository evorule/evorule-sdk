// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 单条导入溯源记录（T5 管理元数据，墙钟旁路，不参与审计验证链）
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class BundleImportRecord {
    @JsonProperty("id")
    private long id;

    @JsonProperty("bundle_id")
    private String bundleId;

    @JsonProperty("dataset_id")
    private String datasetId;

    @JsonProperty("source_version")
    private String sourceVersion;

    /** `auto_by_effective_date` | `pinned` */
    @JsonProperty("selection_mode")
    private String selectionMode;

    @JsonProperty("resolved_version")
    private String resolvedVersion;

    @JsonProperty("content_hash")
    private String contentHash;

    @JsonProperty("entry_count")
    private long entryCount;

    @JsonProperty("imported_at")
    private String importedAt;

    @JsonProperty("imported_by")
    private String importedBy;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getBundleId() { return bundleId; }
    public void setBundleId(String bundleId) { this.bundleId = bundleId; }

    public String getDatasetId() { return datasetId; }
    public void setDatasetId(String datasetId) { this.datasetId = datasetId; }

    public String getSourceVersion() { return sourceVersion; }
    public void setSourceVersion(String sourceVersion) { this.sourceVersion = sourceVersion; }

    public String getSelectionMode() { return selectionMode; }
    public void setSelectionMode(String selectionMode) { this.selectionMode = selectionMode; }

    public String getResolvedVersion() { return resolvedVersion; }
    public void setResolvedVersion(String resolvedVersion) { this.resolvedVersion = resolvedVersion; }

    public String getContentHash() { return contentHash; }
    public void setContentHash(String contentHash) { this.contentHash = contentHash; }

    public long getEntryCount() { return entryCount; }
    public void setEntryCount(long entryCount) { this.entryCount = entryCount; }

    public String getImportedAt() { return importedAt; }
    public void setImportedAt(String importedAt) { this.importedAt = importedAt; }

    public String getImportedBy() { return importedBy; }
    public void setImportedBy(String importedBy) { this.importedBy = importedBy; }
}
