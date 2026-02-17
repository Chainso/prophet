package com.example.prophet.commerce_local.generated.transitions.validators.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Order;
import com.example.prophet.commerce_local.generated.transitions.validators.OrderTransitionValidator;
import io.prophet.events.runtime.TransitionValidationResult;

@org.springframework.stereotype.Component
@org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean(value = OrderTransitionValidator.class, ignored = OrderTransitionValidatorDefault.class)
@Generated("prophet-cli")
public class OrderTransitionValidatorDefault implements OrderTransitionValidator {
    @Override
    public TransitionValidationResult validateApproveOrder(Order target) {
        return TransitionValidationResult.passed();
    }

    @Override
    public TransitionValidationResult validateShipOrder(Order target) {
        return TransitionValidationResult.passed();
    }
}
