// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.exceptions;

public class SessionNotFoundError extends EvoruleException {
    private final long sessionId;

    public SessionNotFoundError(long sessionId) {
        super("Session " + sessionId + " not found");
        this.sessionId = sessionId;
    }

    public long getSessionId() {
        return sessionId;
    }
}
