package io.prophet.events.runtime;

import java.util.UUID;

public final class EventIds {
    private EventIds() {}

    public static String createEventId() {
        return UUID.randomUUID().toString();
    }
}
