package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;

/**
 * Creates a new order.
 */
@Generated("prophet-cli")
public interface CreateOrderActionHandler {
    CreateOrderResult handle(CreateOrderCommand request);
}
