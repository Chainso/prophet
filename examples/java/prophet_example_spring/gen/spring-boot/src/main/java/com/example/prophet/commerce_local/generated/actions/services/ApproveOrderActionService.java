package com.example.prophet.commerce_local.generated.actions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderApproved;

/**
 * Approves an existing order.
 */
@Generated("prophet-cli")
public interface ApproveOrderActionService {
    OrderApproved execute(ApproveOrderCommand request);
}
