package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.ApproveOrderActionService;
import com.example.prophet.commerce_local.generated.events.GeneratedEventEmitter;
import com.example.prophet.commerce_local.generated.events.OrderApprovedEvent;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class ApproveOrderActionServiceDefault implements ApproveOrderActionService {
    private final ObjectProvider<ApproveOrderActionHandler> handlerProvider;
    private final GeneratedEventEmitter eventEmitter;

    public ApproveOrderActionServiceDefault(
        ObjectProvider<ApproveOrderActionHandler> handlerProvider,
        GeneratedEventEmitter eventEmitter
    ) {
        this.handlerProvider = handlerProvider;
        this.eventEmitter = eventEmitter;
    }

    @Override
    public ApproveOrderResult execute(ApproveOrderCommand request) {
        ApproveOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'approveOrder'");
        }
        ApproveOrderResult result = handler.handle(request);
        eventEmitter.emitOrderApprovedEvent(
            OrderApprovedEvent.builder()
                .payload(result)
                .build()
        );
        return result;
    }
}
