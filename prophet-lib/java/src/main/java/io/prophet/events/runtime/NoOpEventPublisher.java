package io.prophet.events.runtime;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

public final class NoOpEventPublisher implements EventPublisher {
    @Override
    public CompletionStage<Void> publish(EventWireEnvelope envelope) {
        return CompletableFuture.completedFuture(null);
    }

    @Override
    public CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes) {
        return CompletableFuture.completedFuture(null);
    }
}
