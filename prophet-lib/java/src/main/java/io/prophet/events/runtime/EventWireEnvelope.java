package io.prophet.events.runtime;

import java.util.Map;

public record EventWireEnvelope(
    String eventId,
    String traceId,
    String eventType,
    String schemaVersion,
    String occurredAt,
    String source,
    Map<String, Object> payload,
    Map<String, String> attributes
) {}
