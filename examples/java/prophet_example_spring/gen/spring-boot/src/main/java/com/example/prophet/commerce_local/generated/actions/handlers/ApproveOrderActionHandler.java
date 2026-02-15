package com.example.prophet.commerce_local.generated.actions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.events.ActionOutcome;
import com.example.prophet.commerce_local.generated.events.ActionOutcomes;

/**
 * Approves an existing order.
 */
@Generated("prophet-cli")
public interface ApproveOrderActionHandler {
    ApproveOrderResult handle(ApproveOrderCommand request);

    default ActionOutcome<ApproveOrderResult> handleOutcome(ApproveOrderCommand request) {
        return ActionOutcomes.just(handle(request));
    }
}
