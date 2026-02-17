package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.CreateOrderActionService;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.CreateOrderResult;
import com.example.prophet.commerce_local.generated.events.CreateOrderResultEvent;
import com.example.prophet.commerce_local.generated.events.DomainEvent;
import com.example.prophet.commerce_local.generated.events.EventPublishingSupport;
import io.prophet.events.runtime.EventIds;
import io.prophet.events.runtime.EventPublisher;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class CreateOrderActionServiceDefault implements CreateOrderActionService {
    private final ObjectProvider<CreateOrderActionHandler> handlerProvider;
    private final EventPublisher eventPublisher;

    public CreateOrderActionServiceDefault(
        ObjectProvider<CreateOrderActionHandler> handlerProvider,
        EventPublisher eventPublisher
    ) {
        this.handlerProvider = handlerProvider;
        this.eventPublisher = eventPublisher;
    }

    @Override
    public CreateOrderResult execute(CreateOrderCommand request) {
        CreateOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'createOrder'");
        }
        ActionOutcome<CreateOrderResult> outcome = handler.handleOutcome(request);
        List<DomainEvent> events = new ArrayList<>();
        events.add(new CreateOrderResultEvent(outcome.output()));
        events.addAll(outcome.additionalEvents());
        EventPublishingSupport.publishAll(
            eventPublisher,
            events,
            EventIds.createEventId(),
            "commerce_local",
            null
        ).toCompletableFuture().join();
        return outcome.output();
    }
}
