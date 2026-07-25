package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonProperty;

public class DiffResult {
    @JsonProperty("version_a")
    private long versionA;

    @JsonProperty("version_b")
    private long versionB;

    @JsonProperty("added")
    private java.util.List<String> added;

    @JsonProperty("removed")
    private java.util.List<String> removed;

    @JsonProperty("changed")
    private java.util.List<String> changed;

    public long getVersionA() { return versionA; }
    public void setVersionA(long versionA) { this.versionA = versionA; }

    public long getVersionB() { return versionB; }
    public void setVersionB(long versionB) { this.versionB = versionB; }

    public java.util.List<String> getAdded() { return added; }
    public void setAdded(java.util.List<String> added) { this.added = added; }

    public java.util.List<String> getRemoved() { return removed; }
    public void setRemoved(java.util.List<String> removed) { this.removed = removed; }

    public java.util.List<String> getChanged() { return changed; }
    public void setChanged(java.util.List<String> changed) { this.changed = changed; }
}
