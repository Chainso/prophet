package com.example.prophet.commerce_local.generated.transitions.validators;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Order;
import io.prophet.events.runtime.TransitionValidationResult;
@Generated("prophet-cli")
public interface OrderTransitionValidator {
    TransitionValidationResult validateApproveOrder(Order target);
    TransitionValidationResult validateShipOrder(Order target);
}
