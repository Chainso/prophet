package io.prophet.events.runtime;

import java.util.List;
import java.util.concurrent.CompletionStage;

public interface EventPublisher {
    CompletionStage<Void> publish(EventWireEnvelope envelope);

    CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes);
}
