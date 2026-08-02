// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule;

import com.evorule.exceptions.*;
import com.evorule.models.*;
import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;
import java.util.List;

public class Session implements AutoCloseable {
    private final EvoruleClient client;
    private final long sessionId;
    private boolean closed = false;

    public Session(EvoruleClient client, long sessionId) {
        this.client = client;
        this.sessionId = sessionId;
    }

    public long getSessionId() {
        return sessionId;
    }

    private void checkClosed() throws SessionClosedError {
        if (closed) {
            throw new SessionClosedError(sessionId);
        }
    }

    private String url(String path) {
        return "/api/sessions/" + sessionId + path;
    }

    public SessionState state() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.getSessionState(sessionId);
    }

    public JsonNode payload() throws EvoruleException, IOException, InterruptedException {
        return state().getPayload();
    }

    public void command(JsonNode instruction) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        client.submitCommand(sessionId, instruction);
    }

    public void updatePayload(String path, Object value) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        client.updatePayload(sessionId, path, value);
    }

    public List<Fact> replay() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.getReplay(sessionId);
    }

    public RewindResponse rewind(long version) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.rewind(sessionId, version);
    }

    public DiffResult diff(long from, long to) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.diff(sessionId, from, to);
    }

    public String debugPhase() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.debugPhase(sessionId);
    }

    public JsonNode debugQueue() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.debugQueue(sessionId);
    }

    public JsonNode debugPendingIo() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.debugPendingIo(sessionId);
    }

    public void interrupt() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        client.interrupt(sessionId);
    }

    public void submitIoResponse(long requestId, JsonNode result, String error) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        client.submitIoResponse(sessionId, requestId, result, error);
    }

    public JsonNode audit() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionAudit(sessionId);
    }

    public boolean auditVerify() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionAuditVerify(sessionId);
    }

    public List<HistoryEntry> history() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionHistory(sessionId);
    }

    public List<SessionFactEntry> factsByPrefix(String prefix) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionFactsByPrefix(sessionId, prefix);
    }

    public void recordUsedAtStartup(List<Long> factIds) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        client.recordUsedAtStartup(sessionId, factIds);
    }

    public List<Long> getUsedAtStartup() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.getUsedAtStartup(sessionId);
    }

    public JsonNode join(long targetId, String direction) throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionJoin(sessionId, targetId, direction);
    }

    public JsonNode leave() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionLeave(sessionId);
    }

    public List<Long> clusterStatus() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.sessionClusterStatus(sessionId);
    }

    public java.util.stream.Stream<SseEvent> events() throws EvoruleException, IOException, InterruptedException {
        checkClosed();
        return client.streamEvents(sessionId);
    }

    public void close() throws EvoruleException, IOException, InterruptedException {
        if (!closed) {
            client.closeSession(sessionId);
            closed = true;
        }
    }
}
