package com.example.prophet.generated.actions.handlers.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.CreateOrderCommand;
import com.example.prophet.generated.actions.CreateOrderResult;
import com.example.prophet.generated.actions.handlers.CreateOrderActionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(CreateOrderActionHandler.class)
@Generated("prophet-cli")
public class CreateOrderActionHandlerDefault implements CreateOrderActionHandler {
    @Override
    public CreateOrderResult handle(CreateOrderCommand request) {
        throw new UnsupportedOperationException("Action 'createOrder' is not implemented");
    }
}
