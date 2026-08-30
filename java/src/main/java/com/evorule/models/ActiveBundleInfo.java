// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 当前激活快照（来自 bundle_manifest.json 的精简视图）
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ActiveBundleInfo {
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

    @JsonProperty("effective_from")
    private String effectiveFrom;

    @JsonProperty("content_hash")
    private String contentHash;

    @JsonProperty("entry_count")
    private long entryCount;

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

    public String getEffectiveFrom() { return effectiveFrom; }
    public void setEffectiveFrom(String effectiveFrom) { this.effectiveFrom = effectiveFrom; }

    public String getContentHash() { return contentHash; }
    public void setContentHash(String contentHash) { this.contentHash = contentHash; }

    public long getEntryCount() { return entryCount; }
    public void setEntryCount(long entryCount) { this.entryCount = entryCount; }
}
