package io.prophet.events.runtime;

import java.util.List;
import java.util.concurrent.CompletionStage;

/**
 * Async contract for publishing event wire envelopes to an external transport.
 */
public interface EventPublisher {
    /**
     * Publishes a single event wire envelope.
     *
     * @param envelope envelope to publish
     * @return completion stage that resolves when publishing finishes
     */
    CompletionStage<Void> publish(EventWireEnvelope envelope);

    /**
     * Publishes a batch of event wire envelopes.
     *
     * @param envelopes envelopes to publish
     * @return completion stage that resolves when publishing finishes
     */
    CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes);
}
