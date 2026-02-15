package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.ActionOutcomes;

/**
 * Ships an approved order.
 */
@Generated("prophet-cli")
public interface ShipOrderActionHandler {
    ShipOrderResult handle(ShipOrderCommand request);

    default ActionOutcome<ShipOrderResult> handleOutcome(ShipOrderCommand request) {
        return ActionOutcomes.just(handle(request));
    }
}
