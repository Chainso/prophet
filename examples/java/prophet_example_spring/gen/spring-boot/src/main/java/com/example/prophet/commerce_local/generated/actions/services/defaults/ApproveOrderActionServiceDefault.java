package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.ApproveOrderActionService;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.DomainEvent;
import com.example.prophet.commerce_local.generated.events.EventPublishingSupport;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransitionEvent;
import io.prophet.events.runtime.EventIds;
import io.prophet.events.runtime.EventPublisher;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class ApproveOrderActionServiceDefault implements ApproveOrderActionService {
    private final ObjectProvider<ApproveOrderActionHandler> handlerProvider;
    private final EventPublisher eventPublisher;

    public ApproveOrderActionServiceDefault(
        ObjectProvider<ApproveOrderActionHandler> handlerProvider,
        EventPublisher eventPublisher
    ) {
        this.handlerProvider = handlerProvider;
        this.eventPublisher = eventPublisher;
    }

    @Override
    public OrderApproveTransition execute(ApproveOrderCommand request) {
        ApproveOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'approveOrder'");
        }
        ActionOutcome<OrderApproveTransition> outcome = handler.handleOutcome(request);
        List<DomainEvent> events = new ArrayList<>();
        events.add(new OrderApproveTransitionEvent(outcome.output()));
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
