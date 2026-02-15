package com.example.prophet.commerce_local.generated.events;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.prophet.events.runtime.EventTime;
import io.prophet.events.runtime.EventWireEnvelope;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

public final class EventPublishingSupport {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private EventPublishingSupport() {}

    public static EventWireEnvelope toEnvelope(DomainEvent event, String eventId, String traceId, String source, Map<String, String> attributes) {
        String eventType;
        Object payloadValue;
        if (event instanceof ApproveOrderResultEvent typed) {
            eventType = "ApproveOrderResult";
            payloadValue = typed.payload();
        }
        else if (event instanceof CreateOrderResultEvent typed) {
            eventType = "CreateOrderResult";
            payloadValue = typed.payload();
        }
        else if (event instanceof ShipOrderResultEvent typed) {
            eventType = "ShipOrderResult";
            payloadValue = typed.payload();
        }
        else if (event instanceof PaymentCapturedEvent typed) {
            eventType = "PaymentCaptured";
            payloadValue = typed.payload();
        }
        else {
            throw new IllegalArgumentException("Unsupported domain event: " + event.getClass().getName());
        }

        Map<String, Object> payload = MAPPER.convertValue(payloadValue, new TypeReference<Map<String, Object>>() {});
        return new EventWireEnvelope(
            eventId,
            traceId,
            eventType,
            "1.0.0",
            EventTime.nowIso(),
            source,
            payload,
            attributes
        );
    }

    public static CompletionStage<Void> publishAll(
        io.prophet.events.runtime.EventPublisher eventPublisher,
        List<DomainEvent> events,
        String traceId,
        String source,
        Map<String, String> attributes
    ) {
        if (events == null || events.isEmpty()) {
            return CompletableFuture.completedFuture(null);
        }
        List<EventWireEnvelope> envelopes = events.stream()
            .map(event -> toEnvelope(event, io.prophet.events.runtime.EventIds.createEventId(), traceId, source, attributes))
            .toList();
        return eventPublisher.publishBatch(envelopes);
    }
}
