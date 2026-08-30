// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * 导入快照包响应（POST /api/bundles/import，导入即激活）
 *
 * 对应 server 返回的 {imported, bundle_id, dataset_id, activated_version,
 * entry_count, missing_services}
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ImportBundleResponse {
    @JsonProperty("imported")
    private boolean imported;

    @JsonProperty("bundle_id")
    private String bundleId;

    @JsonProperty("dataset_id")
    private String datasetId;

    @JsonProperty("activated_version")
    private String activatedVersion;

    @JsonProperty("entry_count")
    private long entryCount;

    @JsonProperty("missing_services")
    private List<String> missingServices;

    public boolean isImported() { return imported; }
    public void setImported(boolean imported) { this.imported = imported; }

    public String getBundleId() { return bundleId; }
    public void setBundleId(String bundleId) { this.bundleId = bundleId; }

    public String getDatasetId() { return datasetId; }
    public void setDatasetId(String datasetId) { this.datasetId = datasetId; }

    public String getActivatedVersion() { return activatedVersion; }
    public void setActivatedVersion(String activatedVersion) { this.activatedVersion = activatedVersion; }

    public long getEntryCount() { return entryCount; }
    public void setEntryCount(long entryCount) { this.entryCount = entryCount; }

    public List<String> getMissingServices() { return missingServices; }
    public void setMissingServices(List<String> missingServices) { this.missingServices = missingServices; }
}
