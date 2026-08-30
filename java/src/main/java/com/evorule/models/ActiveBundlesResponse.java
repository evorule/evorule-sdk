// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * 激活快照包列表响应（GET /api/bundles/active）
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ActiveBundlesResponse {
    @JsonProperty("bundles")
    private List<ActiveBundleInfo> bundles;

    @JsonProperty("count")
    private long count;

    public List<ActiveBundleInfo> getBundles() { return bundles; }
    public void setBundles(List<ActiveBundleInfo> bundles) { this.bundles = bundles; }

    public long getCount() { return count; }
    public void setCount(long count) { this.count = count; }
}
