package com.example.prophet.commerce_local.generated.actions.handlers.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(ShipOrderActionHandler.class)
@Generated("prophet-cli")
public class ShipOrderActionHandlerDefault implements ShipOrderActionHandler {
    @Override
    public OrderShipTransition handle(ShipOrderCommand request) {
        throw new UnsupportedOperationException("Action 'shipOrder' is not implemented");
    }
}
