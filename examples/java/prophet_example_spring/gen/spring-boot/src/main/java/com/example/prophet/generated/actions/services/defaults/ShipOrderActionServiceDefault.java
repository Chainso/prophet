package com.example.prophet.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.ShipOrderCommand;
import com.example.prophet.generated.actions.ShipOrderResult;
import com.example.prophet.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.generated.actions.services.ShipOrderActionService;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(ShipOrderActionService.class)
@Generated("prophet-cli")
public class ShipOrderActionServiceDefault implements ShipOrderActionService {
    private final ObjectProvider<ShipOrderActionHandler> handlerProvider;

    public ShipOrderActionServiceDefault(ObjectProvider<ShipOrderActionHandler> handlerProvider) {
        this.handlerProvider = handlerProvider;
    }

    @Override
    public ShipOrderResult execute(ShipOrderCommand request) {
        ShipOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'shipOrder'");
        }
        return handler.handle(request);
    }
}
