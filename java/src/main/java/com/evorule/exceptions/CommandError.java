// SPDX-License-Identifier: Apache-2.0
package com.evorule.exceptions;

public class CommandError extends EvoruleException {
    public CommandError(String message) {
        super(message);
    }

    public CommandError(String message, Throwable cause) {
        super(message, cause);
    }
}
