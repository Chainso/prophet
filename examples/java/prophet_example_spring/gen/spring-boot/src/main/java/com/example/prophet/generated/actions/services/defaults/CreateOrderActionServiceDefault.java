package com.example.prophet.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.CreateOrderCommand;
import com.example.prophet.generated.actions.CreateOrderResult;
import com.example.prophet.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.generated.actions.services.CreateOrderActionService;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(CreateOrderActionService.class)
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
