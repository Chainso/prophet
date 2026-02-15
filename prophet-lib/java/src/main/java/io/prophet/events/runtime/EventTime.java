package io.prophet.events.runtime;

import java.time.Instant;

public final class EventTime {
    private EventTime() {}

    public static String nowIso() {
        return Instant.now().toString();
    }
}
