package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.events.CreateOrderResult;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.ActionOutcomes;

/**
 * Creates a new order.
 */
@Generated("prophet-cli")
public interface CreateOrderActionHandler {
    CreateOrderResult handle(CreateOrderCommand request);

    default ActionOutcome<CreateOrderResult> handleOutcome(CreateOrderCommand request) {
        return ActionOutcomes.just(handle(request));
    }
}
