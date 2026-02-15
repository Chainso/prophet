package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import io.prophet.events.runtime.EventPublisher;
import io.prophet.events.runtime.EventWireEnvelope;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(value = EventPublisher.class, ignored = GeneratedEventPublisherNoOp.class)
@Generated("prophet-cli")
public class GeneratedEventPublisherNoOp implements EventPublisher {
    @Override
    public CompletionStage<Void> publish(EventWireEnvelope envelope) {
        return CompletableFuture.completedFuture(null);
    }

    @Override
    public CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes) {
        return CompletableFuture.completedFuture(null);
    }
}
