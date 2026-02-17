package com.example.prophet.commerce_local.generated.actions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.events.CreateOrderResult;

/**
 * Creates a new order.
 */
@Generated("prophet-cli")
public interface CreateOrderActionService {
    CreateOrderResult execute(CreateOrderCommand request);
}
