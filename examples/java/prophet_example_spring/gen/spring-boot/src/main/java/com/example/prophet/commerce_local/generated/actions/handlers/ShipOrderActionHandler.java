package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderShipped;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.ActionOutcomes;

/**
 * Ships an approved order.
 */
@Generated("prophet-cli")
public interface ShipOrderActionHandler {
    OrderShipped handle(ShipOrderCommand request);

    default ActionOutcome<OrderShipped> handleOutcome(ShipOrderCommand request) {
        return ActionOutcomes.just(handle(request));
    }
}
