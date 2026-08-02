// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.exceptions;

public class AuthenticationException extends EvoruleException {
    public AuthenticationException(String message) {
        super(message);
    }

    public AuthenticationException(String message, Throwable cause) {
        super(message, cause);
    }
}
