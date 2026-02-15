package com.example.prophet.commerce_local.generated.actions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.actions.services.ShipOrderActionService;
import com.example.prophet.commerce_local.generated.events.GeneratedEventEmitter;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class ShipOrderActionServiceDefault implements ShipOrderActionService {
    private final ObjectProvider<ShipOrderActionHandler> handlerProvider;
    private final GeneratedEventEmitter eventEmitter;

    public ShipOrderActionServiceDefault(
        ObjectProvider<ShipOrderActionHandler> handlerProvider,
        GeneratedEventEmitter eventEmitter
    ) {
        this.handlerProvider = handlerProvider;
        this.eventEmitter = eventEmitter;
    }

    @Override
    public ShipOrderResult execute(ShipOrderCommand request) {
        ShipOrderActionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No handler bean provided for action 'shipOrder'");
        }
        ShipOrderResult result = handler.handle(request);
        eventEmitter.emitShipOrderResult(result);
        return result;
    }
}
