// SPDX-License-Identifier: Apache-2.0
package com.evorule.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 完整状态快照（GET /api/sessions/{id}/snapshot）
 *
 * 对应 server 返回的 {session_id, finished, phase, version, steps,
 * pending_io_count, structural_invariant_violations}
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class SnapshotResponse {
    @JsonProperty("session_id")
    private long sessionId;

    @JsonProperty("finished")
    private boolean finished;

    @JsonProperty("phase")
    private String phase;

    @JsonProperty("version")
    private long version;

    @JsonProperty("steps")
    private long steps;

    @JsonProperty("pending_io_count")
    private long pendingIoCount;

    @JsonProperty("structural_invariant_violations")
    private long structuralInvariantViolations;

    public long getSessionId() { return sessionId; }
    public void setSessionId(long sessionId) { this.sessionId = sessionId; }

    public boolean isFinished() { return finished; }
    public void setFinished(boolean finished) { this.finished = finished; }

    public String getPhase() { return phase; }
    public void setPhase(String phase) { this.phase = phase; }

    public long getVersion() { return version; }
    public void setVersion(long version) { this.version = version; }

    public long getSteps() { return steps; }
    public void setSteps(long steps) { this.steps = steps; }

    public long getPendingIoCount() { return pendingIoCount; }
    public void setPendingIoCount(long pendingIoCount) { this.pendingIoCount = pendingIoCount; }

    public long getStructuralInvariantViolations() { return structuralInvariantViolations; }
    public void setStructuralInvariantViolations(long structuralInvariantViolations) {
        this.structuralInvariantViolations = structuralInvariantViolations;
    }
}
