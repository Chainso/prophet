package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.CreateOrderActionService;
import com.example.prophet.commerce_local.generated.events.GeneratedEventEmitter;
import com.example.prophet.commerce_local.generated.events.OrderCreatedEvent;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class CreateOrderActionServiceDefault implements CreateOrderActionService {
    private final ObjectProvider<CreateOrderActionHandler> handlerProvider;
    private final GeneratedEventEmitter eventEmitter;

    public CreateOrderActionServiceDefault(
        ObjectProvider<CreateOrderActionHandler> handlerProvider,
        GeneratedEventEmitter eventEmitter
    ) {
        this.handlerProvider = handlerProvider;
        this.eventEmitter = eventEmitter;
    }

    @Override
    public CreateOrderResult execute(CreateOrderCommand request) {
        CreateOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'createOrder'");
        }
        CreateOrderResult result = handler.handle(request);
        eventEmitter.emitOrderCreatedEvent(
            OrderCreatedEvent.builder()
                .payload(result)
                .build()
        );
        return result;
    }
}
