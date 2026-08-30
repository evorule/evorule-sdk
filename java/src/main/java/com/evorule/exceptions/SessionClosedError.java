// SPDX-License-Identifier: Apache-2.0
package com.evorule.exceptions;

public class SessionClosedError extends EvoruleException {
    private final long sessionId;

    public SessionClosedError(long sessionId) {
        super("Session " + sessionId + " is closed");
        this.sessionId = sessionId;
    }

    public long getSessionId() {
        return sessionId;
    }
}
