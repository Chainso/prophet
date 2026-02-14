package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;

/**
 * Approves an existing order.
 */
@Generated("prophet-cli")
public interface ApproveOrderActionHandler {
    ApproveOrderResult handle(ApproveOrderCommand request);
}
