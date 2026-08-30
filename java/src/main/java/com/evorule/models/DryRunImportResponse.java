// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * 导入预检响应（POST /api/bundles/import/dry-run，只跑校验链，不落盘不热重载）
 *
 * 对应 server 返回的 {valid, bundle_id, dataset_id, source_version,
 * selection_mode, resolved_version, entry_count, verdict, missing_services}
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class DryRunImportResponse {
    @JsonProperty("valid")
    private boolean valid;

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

    @JsonProperty("entry_count")
    private long entryCount;

    @JsonProperty("verdict")
    private String verdict;

    @JsonProperty("missing_services")
    private List<String> missingServices;

    public boolean isValid() { return valid; }
    public void setValid(boolean valid) { this.valid = valid; }

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

    public long getEntryCount() { return entryCount; }
    public void setEntryCount(long entryCount) { this.entryCount = entryCount; }

    public String getVerdict() { return verdict; }
    public void setVerdict(String verdict) { this.verdict = verdict; }

    public List<String> getMissingServices() { return missingServices; }
    public void setMissingServices(List<String> missingServices) { this.missingServices = missingServices; }
}
