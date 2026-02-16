package io.prophet.events.runtime;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

/**
 * Publisher implementation that performs no external side effects.
 */
public final class NoOpEventPublisher implements EventPublisher {
    /**
     * Creates a no-op event publisher.
     */
    public NoOpEventPublisher() {}

    @Override
    public CompletionStage<Void> publish(EventWireEnvelope envelope) {
        return CompletableFuture.completedFuture(null);
    }

    @Override
    public CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes) {
        return CompletableFuture.completedFuture(null);
    }
}
