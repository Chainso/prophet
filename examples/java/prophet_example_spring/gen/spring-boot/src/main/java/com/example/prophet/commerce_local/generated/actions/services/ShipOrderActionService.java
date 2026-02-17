package com.example.prophet.commerce_local.generated.actions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;

/**
 * Ships an approved order.
 */
@Generated("prophet-cli")
public interface ShipOrderActionService {
    OrderShipTransition execute(ShipOrderCommand request);
}
