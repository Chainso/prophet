package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.transitions.services.OrderTransitionService;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class ApproveOrderHandler implements ApproveOrderActionHandler {

    private final OrderTransitionService orderTransitionService;

    public ApproveOrderHandler(OrderTransitionService orderTransitionService) {
        this.orderTransitionService = orderTransitionService;
    }

    @Override
    @Transactional
    public OrderApproveTransition handle(ApproveOrderCommand request) {
        return orderTransitionService
            .approveOrder(OrderRef.builder().orderId(request.order().orderId()).build())
            .build();
    }
}
