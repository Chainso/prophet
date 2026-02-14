package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.CreateOrderActionService;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class CreateOrderActionServiceDefault implements CreateOrderActionService {
    private final ObjectProvider<CreateOrderActionHandler> handlerProvider;

    public CreateOrderActionServiceDefault(ObjectProvider<CreateOrderActionHandler> handlerProvider) {
        this.handlerProvider = handlerProvider;
    }

    @Override
    public CreateOrderResult execute(CreateOrderCommand request) {
        CreateOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'createOrder'");
        }
        return handler.handle(request);
    }
}
