// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule.exceptions;

public class EvoruleException extends Exception {
    public EvoruleException(String message) {
        super(message);
    }

    public EvoruleException(String message, Throwable cause) {
        super(message, cause);
    }
}
