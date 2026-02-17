package io.prophet.events.runtime;

import static org.junit.jupiter.api.Assertions.assertFalse;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class EventPublisherRuntimeTest {
    @Test
    void noOpPublisherCompletes() {
        NoOpEventPublisher publisher = new NoOpEventPublisher();
        EventWireEnvelope envelope = new EventWireEnvelope(
            EventIds.createEventId(),
            "trace-1",
            "Example",
            "1.0.0",
            EventTime.nowIso(),
            "tests",
            Map.of(),
            Map.of(),
            List.of(
                Map.of(
                    "object_type", "Order",
                    "object_ref", Map.of("orderId", "ord-1"),
                    "object", Map.of("orderId", "ord-1", "totalAmount", 42)
                )
            )
        );

        publisher.publish(envelope).toCompletableFuture().join();
        publisher.publishBatch(List.of(envelope)).toCompletableFuture().join();
    }

    @Test
    void eventIdHelperProducesValue() {
        assertFalse(EventIds.createEventId().isBlank());
    }
}
