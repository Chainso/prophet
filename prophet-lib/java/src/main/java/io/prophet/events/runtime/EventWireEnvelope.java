package io.prophet.events.runtime;

import java.util.Map;

/**
 * Canonical wire payload for cross-platform event publishing.
 *
 * @param eventId unique event identifier
 * @param traceId distributed trace identifier
 * @param eventType ontology-scoped event type name
 * @param schemaVersion wire schema version
 * @param occurredAt event occurrence time in ISO-8601 format
 * @param source logical source that emitted this event
 * @param payload event payload data
 * @param attributes optional transport metadata
 */
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
