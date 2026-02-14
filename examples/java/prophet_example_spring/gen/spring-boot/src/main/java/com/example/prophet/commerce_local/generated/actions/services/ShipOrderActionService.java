package com.example.prophet.commerce_local.generated.actions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;

/**
 * Ships an approved order.
 */
@Generated("prophet-cli")
public interface ShipOrderActionService {
    ShipOrderResult execute(ShipOrderCommand request);
}
