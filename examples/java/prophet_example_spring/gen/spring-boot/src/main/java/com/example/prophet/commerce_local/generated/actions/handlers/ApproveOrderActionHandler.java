package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.ActionOutcomes;

/**
 * Approves an existing order.
 */
@Generated("prophet-cli")
public interface ApproveOrderActionHandler {
    OrderApproveTransition handle(ApproveOrderCommand request);

    default ActionOutcome<OrderApproveTransition> handleOutcome(ApproveOrderCommand request) {
        return ActionOutcomes.just(handle(request));
    }
}
