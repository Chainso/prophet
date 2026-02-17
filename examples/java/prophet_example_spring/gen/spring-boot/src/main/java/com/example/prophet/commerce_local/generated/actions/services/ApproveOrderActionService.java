package com.example.prophet.commerce_local.generated.actions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;

/**
 * Approves an existing order.
 */
@Generated("prophet-cli")
public interface ApproveOrderActionService {
    OrderApproveTransition execute(ApproveOrderCommand request);
}
