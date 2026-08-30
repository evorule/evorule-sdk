// SPDX-License-Identifier: Apache-2.0
package com.evorule.exceptions;

public class AuthenticationException extends EvoruleException {
    public AuthenticationException(String message) {
        super(message);
    }

    public AuthenticationException(String message, Throwable cause) {
        super(message, cause);
    }
}
