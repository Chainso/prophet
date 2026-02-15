package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.ShipOrderActionService;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.DomainEvent;
import com.example.prophet.commerce_local.generated.events.EventPublishingSupport;
import com.example.prophet.commerce_local.generated.events.ShipOrderResultEvent;
import io.prophet.events.runtime.EventIds;
import io.prophet.events.runtime.EventPublisher;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class ShipOrderActionServiceDefault implements ShipOrderActionService {
    private final ObjectProvider<ShipOrderActionHandler> handlerProvider;
    private final EventPublisher eventPublisher;

    public ShipOrderActionServiceDefault(
        ObjectProvider<ShipOrderActionHandler> handlerProvider,
        EventPublisher eventPublisher
    ) {
        this.handlerProvider = handlerProvider;
        this.eventPublisher = eventPublisher;
    }

    @Override
    public ShipOrderResult execute(ShipOrderCommand request) {
        ShipOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'shipOrder'");
        }
        ActionOutcome<ShipOrderResult> outcome = handler.handleOutcome(request);
        List<DomainEvent> events = new ArrayList<>();
        events.add(new ShipOrderResultEvent(outcome.output()));
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
