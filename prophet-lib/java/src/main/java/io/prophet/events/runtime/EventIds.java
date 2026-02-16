package io.prophet.events.runtime;

import java.util.UUID;

/**
 * Utility helpers for generating event identifiers.
 */
public final class EventIds {
    private EventIds() {}

    /**
     * Creates a unique event identifier.
     *
     * @return a new event id string
     */
    public static String createEventId() {
        return UUID.randomUUID().toString();
    }
}
