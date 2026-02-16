package io.prophet.events.runtime;

import java.time.Instant;

/**
 * Utility helpers for event timestamp generation.
 */
public final class EventTime {
    private EventTime() {}

    /**
     * Returns the current UTC timestamp in ISO-8601 format.
     *
     * @return current time string in ISO-8601 format
     */
    public static String nowIso() {
        return Instant.now().toString();
    }
}
